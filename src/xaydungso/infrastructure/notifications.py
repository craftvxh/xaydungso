"""Bounded Telegram HTTP transport and checked native Windows toast dispatch."""

import base64
import json
import os
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from xaydungso.application.ports import NotificationError
from xaydungso.infrastructure.preferences import FilePreferences


class TelegramNotification:
    def __init__(
        self,
        token: str | None = None,
        chat_id: str | None = None,
        *,
        settings_directory=None,
    ):
        self.token = (
            token
            if token is not None
            else os.environ.get("XAYDUNGSO_TELEGRAM_BOT_TOKEN", "")
        )
        self.chat_id = (
            chat_id
            if chat_id is not None
            else os.environ.get("XAYDUNGSO_TELEGRAM_CHAT_ID", "")
        )
        self._validated = False
        self.settings_directory = settings_directory

    def _request(self, method, payload):
        request = Request(
            f"https://api.telegram.org/bot{self.token}/{method}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                result = json.loads(response.read())
            if not result.get("ok"):
                raise NotificationError(
                    "Telegram từ chối yêu cầu. Kiểm tra Bot Token, Chat ID và quyền gửi của bot."
                )
            return result.get("result", {})
        except HTTPError as error:
            if error.code in (401, 404):
                message = (
                    "Bot Token Telegram không hợp lệ. Kiểm tra lại token trong Cài đặt."
                )
            elif error.code == 403:
                message = "Telegram từ chối quyền truy cập. Mở bot, bấm Start và kiểm tra bot không bị chặn."
            elif error.code == 400:
                message = "Telegram không chấp nhận yêu cầu. Kiểm tra Chat ID người nhận và bấm Start trong cuộc trò chuyện với bot."
            elif error.code == 429:
                message = "Telegram đang giới hạn số yêu cầu; lịch nhắc sẽ thử lại sau."
            else:
                message = "Máy chủ Telegram chưa xử lý được yêu cầu; hãy thử lại."
            raise NotificationError(message) from None
        except NotificationError:
            raise
        except (URLError, OSError, ValueError):
            raise NotificationError(
                "Không kết nối được Telegram. Kiểm tra mạng, proxy và chứng chỉ HTTPS."
            ) from None
        except Exception:
            raise NotificationError(
                "Gửi Telegram thất bại; hãy kiểm tra kết nối và cấu hình."
            ) from None

    def validate_connection(self):
        if not self.token or not self.chat_id:
            raise NotificationError(
                "Telegram chưa được cấu hình đủ Bot Token và Chat ID."
            )
        bot = self._request("getMe", {})
        chat = self._request("getChat", {"chat_id": self.chat_id})
        if not bot.get("id") or not chat.get("id"):
            raise NotificationError("Phản hồi kiểm tra Telegram không hợp lệ.")
        if bot["id"] == chat["id"]:
            raise NotificationError(
                "Chat ID đang là ID của chính bot. Hãy bấm Start trong chat với bot rồi dùng Chat ID của cuộc trò chuyện nhận tin."
            )
        self._validated = True
        # Shown as "Kênh nhận thông báo" in Cài đặt; never logged.
        self.chat_name = (
            chat.get("title")
            or " ".join(
                part for part in (chat.get("first_name"), chat.get("last_name")) if part
            )
            or (f"@{chat['username']}" if chat.get("username") else str(chat["id"]))
        )
        return "Bot Token và Chat ID hợp lệ. Để nhận lịch nhắc, cần bật nhắc nền và chờ đúng giờ gửi."

    def send(self, title: str, message: str) -> None:
        if self.settings_directory is not None:
            try:
                current = FilePreferences(self.settings_directory).load()
            except (OSError, RuntimeError):
                raise NotificationError(
                    "Không đọc được cấu hình Telegram mới; hãy kiểm tra Cài đặt."
                ) from None
            token = current.telegram_token or os.environ.get(
                "XAYDUNGSO_TELEGRAM_BOT_TOKEN", ""
            )
            chat = current.telegram_chat_id or os.environ.get(
                "XAYDUNGSO_TELEGRAM_CHAT_ID", ""
            )
            if (token, chat) != (self.token, self.chat_id):
                self.token, self.chat_id = token, chat
                self._validated = False
        if not self._validated:
            self.validate_connection()
        # Telegram's limit is 4096 characters. Keep the identifier at the end visible.
        text = f"{title}\n{message}"
        if len(text) > 4096:
            text = text[:3800] + "\n…\n" + text[-200:]
        self._request("sendMessage", {"chat_id": self.chat_id, "text": text})


def windows_script(title: str, message: str) -> str:
    toast = ElementTree.Element("toast")
    binding = ElementTree.SubElement(
        ElementTree.SubElement(toast, "visual"), "binding", template="ToastGeneric"
    )
    ElementTree.SubElement(binding, "text").text = title
    ElementTree.SubElement(binding, "text").text = message
    payload = base64.b64encode(ElementTree.tostring(toast, encoding="utf-8")).decode(
        "ascii"
    )
    # User text is base64-encoded XML, never interpolated as PowerShell code.
    return """
$ErrorActionPreference = 'Stop'
try {
  $null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime]
  $null = [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime]
  $key = 'HKCU:\\Software\\Classes\\AppUserModelId\\xaydungso'
  $null = New-Item -Path $key -Force
  $null = New-ItemProperty -Path $key -Name DisplayName -Value 'Xây Dựng Số' -PropertyType String -Force
  $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
  $xml.LoadXml([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('PAYLOAD')))
  $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('xaydungso')
  if ($notifier.Setting.ToString() -ne 'Enabled') { throw 'Notifications disabled' }
  $notifier.Show([Windows.UI.Notifications.ToastNotification]::new($xml))
  exit 0
} catch { exit 1 }
""".replace("PAYLOAD", payload)


class WindowsNotification:
    def send(self, title: str, message: str) -> None:
        if sys.platform != "win32":
            raise RuntimeError("Windows Notification chỉ có trên Windows.")
        encoded = base64.b64encode(
            windows_script(title, message).encode("utf-16-le")
        ).decode("ascii")
        powershell = os.path.join(
            os.environ["SystemRoot"],
            "System32",
            "WindowsPowerShell",
            "v1.0",
            "powershell.exe",
        )
        try:
            subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-NonInteractive",
                    "-EncodedCommand",
                    encoded,
                ],
                capture_output=True,
                check=True,
                timeout=20,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except (OSError, subprocess.SubprocessError):
            raise RuntimeError("Gửi Windows Notification thất bại.") from None
