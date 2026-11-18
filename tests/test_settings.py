"""Preferences persistence, Windows credential protection and settings UI."""

import json
import sys

import pytest
from test_foundation import run_python

from xaydungso.application.settings import Preferences, Settings
from xaydungso.core.paths import template_path
from xaydungso.domain.records import ValidationError
from xaydungso.infrastructure import preferences
from xaydungso.infrastructure.preferences import FilePreferences


def test_workbook_defaults_to_so_theo_doi_and_only_uses_merge(tmp_path):
    store = FilePreferences(tmp_path)
    service = Settings(store, tmp_path, template_path())
    assert service.export_path(service.load()) == template_path().resolve()
    selected = service.save(Preferences(str(template_path()), excel_policy="replace"))
    assert selected.excel_policy == "merge"
    output = tmp_path / "Sổ đang dùng.xlsx"
    output.write_bytes(template_path().read_bytes())
    service.save(Preferences(str(output), excel_policy="merge"))
    assert (
        Settings(FilePreferences(tmp_path), tmp_path, template_path()).export_path(
            store.load()
        )
        == output
    )
    for folder in (
        str(tmp_path),
        "relative.xlsx",
        str(tmp_path / "missing.xlsx"),
    ):
        with pytest.raises(ValidationError):
            service.save(Preferences(folder, excel_policy="merge"))
    assert store.load().excel_file == str(output)


def test_partial_credentials_and_corrupt_settings_are_not_silently_reset(tmp_path):
    store = FilePreferences(tmp_path)
    service = Settings(store, tmp_path, template_path())
    for value in (Preferences("", "secret", ""), Preferences("", "", "123")):
        with pytest.raises(ValidationError):
            service.save(value)
    store.path.write_text(
        '{"version":1,"telegram_token":"private-invalid"}', encoding="utf-8"
    )
    with pytest.raises(RuntimeError) as error:
        store.load()
    assert "private-invalid" not in str(error.value)
    assert "secret" not in repr(Preferences("", "secret", "123"))


def test_legacy_directory_is_not_automatically_selected_for_overwriting(tmp_path):
    store = FilePreferences(tmp_path)
    store.path.write_text(
        json.dumps(
            {
                "version": 1,
                "export_directory": str(tmp_path),
                "telegram_token": "",
                "telegram_chat_id": "",
            }
        ),
        encoding="utf-8",
    )
    assert Settings(store, tmp_path, template_path()).load() == Preferences()
    store.save(store.load())
    assert json.loads(store.path.read_text(encoding="utf-8"))["version"] == 2


@pytest.mark.skipif(sys.platform != "win32", reason="Windows DPAPI")
def test_real_dpapi_roundtrip_and_failed_write_preserves_old_settings(
    tmp_path, monkeypatch
):
    store = FilePreferences(tmp_path)
    value = Preferences(str(tmp_path), "fake-token-never-send", "-100123456")
    store.save(value)
    before = store.path.read_bytes()
    assert value.telegram_token.encode() not in before
    assert json.loads(before)["telegram_token"]
    assert FilePreferences(tmp_path).load() == value

    def fail(*args):
        raise PermissionError("locked")

    monkeypatch.setattr(preferences.os, "replace", fail)
    with pytest.raises(PermissionError):
        store.save(Preferences(str(tmp_path)))
    assert store.path.read_bytes() == before
    assert not list(tmp_path.glob("*.tmp"))


def test_settings_page_saves_paths_and_keeps_input_on_validation_error():
    run_python("""
        import time
        from pathlib import Path
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication, QLineEdit
        from xaydungso.application.settings import Settings
        from xaydungso.core.paths import data_directory, template_path
        from xaydungso.infrastructure.preferences import FilePreferences
        from xaydungso.presentation.settings import SettingsPage
        from xaydungso.presentation.tasks import TaskRunner

        app = QApplication([])
        directory = data_directory()
        store = FilePreferences(directory)
        service = Settings(store, directory, template_path())
        runner = TaskRunner()
        page = SettingsPage(service, runner, directory / 'so_theo_doi.xlsx')
        page.show()
        def idle():
            deadline = time.monotonic() + 5
            while runner.busy:
                assert time.monotonic() < deadline
                QTest.qWait(10)
        idle()
        assert page.token.echoMode() == QLineEdit.EchoMode.Password
        page.token.setText('fake-not-sent')
        page.save_button.click()
        idle()
        assert page.token.text() == 'fake-not-sent'
        assert page.feedback.text()
        assert not store.path.exists()
        page.token.clear()
        output = directory / 'existing.xlsx'
        output.write_bytes(template_path().read_bytes())
        page.excel_file.setText(str(output))
        assert not hasattr(page, 'excel_policy')
        page.save_button.click()
        idle()
        assert Path(store.load().excel_file).samefile(output)
        page.close()
    """)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows DPAPI")
def test_worker_uses_saved_credentials_without_sending(tmp_path, monkeypatch):
    from xaydungso import worker

    FilePreferences(tmp_path).save(Preferences("", "fake-saved-token", "-100999"))
    monkeypatch.setenv("XAYDUNGSO_TELEGRAM_BOT_TOKEN", "fake-env-token")
    monkeypatch.setenv("XAYDUNGSO_TELEGRAM_CHAT_ID", "999")
    monkeypatch.setattr(sys, "argv", ["worker", "--once", "--data-dir", str(tmp_path)])
    observed = []

    class Engine:
        def __init__(self, store, transports, **kwargs):
            observed.append(
                (transports["telegram"].token, transports["telegram"].chat_id)
            )

        def tick(self):
            pass

    monkeypatch.setattr(worker, "ReminderEngine", Engine)
    assert worker.main() == 0
    assert observed == [("fake-saved-token", "-100999")]


def test_application_uses_selected_existing_file_on_startup():
    run_python("""
        from PyQt6.QtCore import QTimer
        from xaydungso import main
        from xaydungso.application.settings import Preferences
        from xaydungso.core.paths import data_directory, template_path
        from xaydungso.infrastructure.preferences import FilePreferences
        from xaydungso.presentation.main_window import MainWindow

        target = data_directory() / 'existing.xlsx'
        target.write_bytes(template_path().read_bytes())
        FilePreferences(data_directory()).save(Preferences(str(target), excel_policy="replace"))
        original_show = MainWindow.show
        def show_and_close(window):
            assert window.stackedWidget.count() == 5  # 4 sidebar pages + Cấu hình mẫu
            assert window.records_page.output_path == target
            assert window.records_page.service.exporter.destination == target
            window.switchTo(window.settings_page)
            original_show(window)
            def close_when_idle():
                if window.runner.busy:
                    QTimer.singleShot(50, close_when_idle)
                else:
                    window.close()
            QTimer.singleShot(100, close_when_idle)
        MainWindow.show = show_and_close
        assert main() == 0
    """)


def test_settings_connection_check_uses_inputs_without_saving_or_sending():
    run_python("""
        import time
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtTest import QTest
        from xaydungso.application.settings import Settings
        from xaydungso.application.ports import NotificationError
        from xaydungso.core.paths import data_directory, template_path
        from xaydungso.infrastructure.preferences import FilePreferences
        from xaydungso.presentation.settings import SettingsPage
        from xaydungso.presentation.tasks import TaskRunner
        app = QApplication([])
        store = FilePreferences(data_directory())
        calls = []
        def check(token, chat):
            calls.append((token,chat))
            raise NotificationError('Chat ID sai: chọn ID người nhận.')
        service = Settings(store, data_directory(), template_path(), telegram_checker=check)
        runner = TaskRunner()
        page = SettingsPage(service,runner,None)
        def idle():
            deadline = time.monotonic()+5
            while runner.busy:
                assert time.monotonic()<deadline
                QTest.qWait(10)
        idle()
        page.token.setText('fake-token')
        page.chat_id.setText('999')
        page.check_button.click()
        idle()
        assert calls == [('fake-token','999')]
        assert 'Chat ID sai' in page.feedback.text()
        assert page.check_button.isEnabled()
        assert not store.path.exists()
        page.close()
    """)


def test_telegram_test_button_sends_once_with_unsaved_inputs_and_never_saves():
    run_python("""
        import threading,time
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtTest import QTest
        from xaydungso.application.settings import Settings
        from xaydungso.application.ports import NotificationError
        from xaydungso.core.paths import data_directory,template_path
        from xaydungso.infrastructure.preferences import FilePreferences
        from xaydungso.presentation.settings import SettingsPage
        from xaydungso.presentation.tasks import TaskRunner
        app=QApplication([])
        calls=[]
        ready=threading.Event()
        def send(token,chat):
            calls.append((token,chat))
            assert ready.wait(5)
        store=FilePreferences(data_directory())
        service=Settings(store,data_directory(),template_path(),telegram_tester=send)
        runner=TaskRunner()
        page=SettingsPage(service,runner,None)
        def idle():
            deadline=time.monotonic()+5
            while runner.busy:
                assert time.monotonic()<deadline
                QTest.qWait(10)
        idle()
        page.token.setText('unsaved-fake-token')
        page.chat_id.setText('123')
        page.test_button.click()
        assert not page.test_button.isEnabled()
        assert not page.check_button.isEnabled()
        page.test_button.click()  # Disabled while the first request is in progress.
        ready.set()
        idle()
        assert calls==[('unsaved-fake-token','123')]
        assert page.test_button.isEnabled()
        assert page.check_button.isEnabled()
        assert not store.path.exists()
        def fail(token,chat):
            calls.append((token,chat))
            raise NotificationError('Telegram từ chối yêu cầu kiểm tra.')
        service.telegram_tester=fail
        page.test_button.click()
        idle()
        assert len(calls)==2
        assert 'Telegram từ chối' in page.feedback.text()
        assert page.test_button.isEnabled()
        assert not store.path.exists()
        page.close()
    """)
