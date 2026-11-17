"""Transport contracts with mocked HTTP/processes; never send live messages."""

import base64
import json
from contextlib import contextmanager
from xml.etree import ElementTree

import pytest

from xaydungso.infrastructure import notifications


def test_telegram_posts_unicode_and_checks_ack(monkeypatch):
    captured = []

    @contextmanager
    def request(req, timeout):
        captured.append((req, timeout))

        class Response:
            def read(self):
                return b'{"ok":true}'

        yield Response()

    monkeypatch.setattr(notifications, "urlopen", request)
    notifications.TelegramNotification("fake-token", "123").send(
        "Tiêu đề", "Nội dung mẫu"
    )
    req, timeout = captured[0]
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
