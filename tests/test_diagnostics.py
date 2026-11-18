"""Read-only facts for the Cài đặt page."""

from datetime import datetime

from xaydungso.domain.records import RecordData
from xaydungso.domain.reminders import LOCAL_ZONE, make_reminder, timestamp
from xaydungso.infrastructure.diagnostics import SqliteDiagnostics
from xaydungso.infrastructure.records import SqliteRecords
from xaydungso.infrastructure.reminders import SqliteReminders


def test_database_status_reports_facts_without_changing_anything(database):
    SqliteRecords(database).save(RecordData("HS-1", "Tên"))
    before = database.path.read_bytes()
    status = SqliteDiagnostics(database).database_status()
    assert status.records == 1 and status.integrity == "ok"
    assert status.schema_version == 7 and status.size_bytes > 0
    assert status.sqlite_version.count(".") == 2
    assert database.path.read_bytes() == before


def test_telegram_sent_today_counts_only_sent_telegram_deliveries(database):
    store = SqliteReminders(database)
    reminder = make_reminder("Lịch", 10)
    store.save(reminder)
    now = timestamp(datetime.now(LOCAL_ZONE))
    with database.connect() as connection, connection:
        connection.execute(
            "UPDATE reminder_deliveries SET state='sent', sent_at=? WHERE reminder_id=?",
            (now, reminder.id),
        )
    # Both channels are 'sent', but only the Telegram one counts.
    assert SqliteDiagnostics(database).telegram_sent_today() == 1


def test_excel_status_for_missing_and_existing_file(database, tmp_path):
    diagnostics = SqliteDiagnostics(database)
    assert not diagnostics.excel_status(tmp_path / "missing.xlsx").exists
    workbook = tmp_path / "book.xlsx"
    workbook.write_bytes(b"x")
    status = diagnostics.excel_status(workbook)
    assert status.exists and status.modified_at and status.written_records == 0


def test_settings_page_sections_status_tiles_and_telegram_chip():
    from test_foundation import run_python

    run_python("""
        import time
        from pathlib import Path
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication
        from xaydungso.application.settings import Settings
        from xaydungso.core.paths import data_directory, template_path
        from xaydungso.infrastructure.database import Database
        from xaydungso.infrastructure.diagnostics import SqliteDiagnostics
        from xaydungso.infrastructure.preferences import FilePreferences
        from xaydungso.presentation.settings import SettingsPage
        from xaydungso.presentation.tasks import TaskRunner

        app = QApplication([])
        directory = data_directory()
        directory.mkdir(parents=True, exist_ok=True)
        database = Database(directory / 'xaydungso.sqlite3')
        database.initialize()
        service = Settings(
            FilePreferences(directory), directory, template_path(),
            telegram_checker=lambda token, chat: ('Hợp lệ.', 'Ban QLDA Số 4'))
        runner = TaskRunner()
        exported = []
        page = SettingsPage(service, runner, template_path(),
                            diagnostics=SqliteDiagnostics(database),
                            export=lambda: exported.append(1))
        page.show()

        def idle():
            limit = time.monotonic() + 5
            QTest.qWait(10)
            while runner.busy:
                assert time.monotonic() < limit
                QTest.qWait(10)

        idle()
        assert page.stack.currentIndex() == 0 and 'Dữ liệu' in page.crumb.text()
        assert 'bình thường' in page.data_chip.text()
        assert page.data_tiles['integrity'].value.text() == 'OK'
        assert page.data_tiles['schema'].value.text() == 'v7'
        assert page.excel_tiles['auto'].value.text() == 'Bật'
        page.nav_buttons[1].click()
        assert page.stack.currentIndex() == 1 and 'Telegram' in page.crumb.text()
        page.token.setText('fake-token')
        page.chat_id.setText('-100123')
        page.check_button.click()
        idle()
        assert 'Đã kết nối' in page.telegram_chip.text()
        assert page.telegram_tiles['chat'].value.text() == 'Ban QLDA Số 4'
        assert page.telegram_tiles['latency'].unit.text() == 'ms'
        page.nav_buttons[2].click()
        page.export_button.click()
        idle()
        assert exported == [1] and 'Đã ghi lại' in page.feedback.text()
        page.close()
    """)
