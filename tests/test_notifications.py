"""Transport contracts with mocked HTTP/processes; never send live messages."""

import base64
import json
from contextlib import contextmanager
from urllib.error import HTTPError
from xml.etree import ElementTree

import pytest

from xaydungso.application.ports import NotificationError
from xaydungso.application.settings import Preferences
from xaydungso.infrastructure import notifications


def test_telegram_posts_unicode_and_checks_ack(monkeypatch):
    captured = []

    @contextmanager
    def request(req, timeout):
        captured.append((req, timeout))

        class Response:
            def read(self):
                if req.full_url.endswith("/getMe"):
                    return b'{"ok":true,"result":{"id":999}}'
                if req.full_url.endswith("/getChat"):
                    return b'{"ok":true,"result":{"id":123}}'
                return b'{"ok":true}'

        yield Response()

    monkeypatch.setattr(notifications, "urlopen", request)
    notifications.TelegramNotification("fake-token", "123").send(
        "Tiêu đề", "Nội dung mẫu"
    )
    req, timeout = captured[-1]
    assert req.method == "POST"
    assert timeout == 10
    assert json.loads(req.data) == {"chat_id": "123", "text": "Tiêu đề\nNội dung mẫu"}


def test_telegram_errors_do_not_expose_bot_token(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("https://example.test/fake-secret")

    monkeypatch.setattr(notifications, "urlopen", fail)
    with pytest.raises(RuntimeError) as error:
        notifications.TelegramNotification("fake-secret", "123").send("A", "B")
    assert "fake-secret" not in str(error.value)
    with pytest.raises(RuntimeError):
        notifications.TelegramNotification("", "").send("A", "B")


def test_telegram_rejects_bot_as_recipient_without_sending(monkeypatch):
    calls = []

    @contextmanager
    def request(req, timeout):
        calls.append(req.full_url.rsplit("/", 1)[-1])

        class Response:
            def read(self):
                return b'{"ok":true,"result":{"id":999}}'

        yield Response()

    monkeypatch.setattr(notifications, "urlopen", request)
    with pytest.raises(NotificationError, match="ID của chính bot"):
        notifications.TelegramNotification("private-fake-token", "999").send("A", "B")
    assert calls == ["getMe", "getChat"]


@pytest.mark.parametrize("code", [400, 401, 403, 429, 500])
def test_telegram_http_error_is_actionable_and_does_not_leak_credentials(
    monkeypatch, code
):
    def fail(req, **kwargs):
        raise HTTPError(req.full_url, code, "private-fake-token", {}, None)

    monkeypatch.setattr(notifications, "urlopen", fail)
    with pytest.raises(NotificationError) as error:
        notifications.TelegramNotification(
            "private-fake-token", "123"
        ).validate_connection()
    assert "private-fake-token" not in str(error.value)
    assert "https://" not in str(error.value)


def test_worker_transport_reloads_saved_target_before_sending(monkeypatch, tmp_path):
    saved = [Preferences("", "fake-token-a", "123")]

    class Store:
        def __init__(self, directory):
            pass

        def load(self):
            return saved[0]

    monkeypatch.setattr(notifications, "FilePreferences", Store)
    transport = notifications.TelegramNotification(
        "old-token", "old-chat", settings_directory=tmp_path
    )
    calls = []

    def request(method, payload):
        calls.append((method, transport.token, transport.chat_id))
        if method == "getMe":
            return {"id": 99999}
        if method == "getChat":
            return {"id": int(payload["chat_id"])}
        return {"message_id": 1}

    monkeypatch.setattr(transport, "_request", request)
    transport.send("First", "")
    saved[0] = Preferences("", "fake-token-b", "456")
    transport.send("Second", "")
    assert [entry for entry in calls if entry[0] == "sendMessage"] == [
        ("sendMessage", "fake-token-a", "123"),
        ("sendMessage", "fake-token-b", "456"),
    ]
    assert len([entry for entry in calls if entry[0] == "getMe"]) == 2

    def fail(self):
        raise RuntimeError("private-fake-token")

    monkeypatch.setattr(Store, "load", fail)
    count = len(calls)
    with pytest.raises(NotificationError) as error:
        transport.send("Third", "")
    assert "private-fake-token" not in str(error.value)
    assert len(calls) == count


def test_windows_payload_is_encoded_data_not_executable_text():
    message = "Tên & <mẫu> ' ; $(untrusted)"
    script = notifications.windows_script("Tiêu đề", message)
    assert message not in script
    encoded = script.split("FromBase64String('", 1)[1].split("')", 1)[0]
    root = ElementTree.fromstring(base64.b64decode(encoded))
    assert root.findall(".//text")[1].text == message


def test_windows_process_errors_are_reported(monkeypatch):
    monkeypatch.setattr(notifications.sys, "platform", "win32")
    monkeypatch.setenv("SystemRoot", "C:/Windows")
    monkeypatch.setattr(notifications.subprocess, "CREATE_NO_WINDOW", 0, raising=False)
    captured = []

    def run(args, **options):
        captured.append((args, options))

    monkeypatch.setattr(notifications.subprocess, "run", run)
    notifications.WindowsNotification().send("Mẫu", "Nội dung")
    assert captured[0][1]["check"] is True
    assert captured[0][1]["timeout"] == 20
    script = base64.b64decode(captured[0][0][-1]).decode("utf-16-le")
    assert "ToastNotificationManager" in script

    def fail(*args, **kwargs):
        raise OSError("Synthetic process failure")

    monkeypatch.setattr(notifications.subprocess, "run", fail)
    with pytest.raises(RuntimeError):
        notifications.WindowsNotification().send("Mẫu", "Nội dung")
