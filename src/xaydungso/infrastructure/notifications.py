"""Bounded Telegram HTTP transport and checked native Windows toast dispatch."""

import base64
import json
import os
import subprocess
import sys
from urllib.request import Request, urlopen
from xml.etree import ElementTree


class TelegramNotification:
    def __init__(self, token: str | None = None, chat_id: str | None = None):
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

    def send(self, title: str, message: str) -> None:
        if not self.token or not self.chat_id:
            raise RuntimeError("Telegram chưa được cấu hình.")
        # Telegram's limit is 4096 characters. Keep the identifier at the end visible.
        text = f"{title}\n{message}"
        if len(text) > 4096:
            text = text[:3800] + "\n…\n" + text[-200:]
        request = Request(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            data=json.dumps({"chat_id": self.chat_id, "text": text}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        # Do not expose the original exception: the URL contains the bot token.
        try:
            with urlopen(request, timeout=10) as response:
                result = json.loads(response.read())
            if not result.get("ok"):
                raise RuntimeError("Telegram rejected the notification")
        except Exception:
            raise RuntimeError("Gửi Telegram thất bại.") from None


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
