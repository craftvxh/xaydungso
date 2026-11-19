"""Overall reminder status shown on the Nhắc nhở page, from per-channel states."""

import pytest

from xaydungso.presentation.reminders_page import (
    CANCELLED,
    FAILED,
    PENDING,
    SENT,
    reminder_status,
)


def reminder(telegram, windows, cancelled=0):
    return {
        "cancelled": cancelled,
        "deliveries": {"telegram": {"state": telegram}, "windows": {"state": windows}},
    }


@pytest.mark.parametrize(
    "states, expected",
    [
        (("pending", "pending"), PENDING),
        (("sent", "pending"), PENDING),
        (("sending", "sent"), PENDING),
        (("sent", "sent"), SENT),
        (("failed", "sent"), FAILED),
        (("pending", "failed"), FAILED),
    ],
)
def test_status_from_channels(states, expected):
    assert reminder_status(reminder(*states)) == expected


def test_cancelled_wins_over_channel_states():
    assert reminder_status(reminder("failed", "sent", cancelled=1)) == CANCELLED


def test_reminder_dialog_template_preview_and_value():
    from test_foundation import run_python

    run_python("""
        from PyQt6.QtWidgets import QApplication
        from xaydungso.domain.records import Record, RecordData
        from xaydungso.domain.templates import Template
        from xaydungso.presentation.reminder_dialog import ReminderDialog
        app = QApplication([])
        record = Record(1, '2026-11-01T00:00:00+00:00', RecordData(
            'HS-089', 'Nguyễn Văn Hùng', deadline_at='2099-11-20T07:30:00+00:00'))
        templates = [
            Template(1, 'Ngắn gọn', 'Hồ sơ {{ma_ho_so}} — {{ho_ten}}', True),
            Template(2, 'Sắp hạn', 'Hồ sơ {{ma_ho_so}} sắp đến hạn xử lý.' + chr(10) + 'Hạn: {{han_xu_ly}}'),
        ]
        dialog = ReminderDialog([record], record=record, templates=templates)
        assert dialog.template.currentText() == 'Ngắn gọn  (Mặc định)'
        assert dialog.title.text() == 'Hồ sơ HS-089 — Nguyễn Văn Hùng'
        assert dialog.duration.presets.currentText() == 'Trước 24 giờ'
        assert not dialog.duration.seconds.isVisibleTo(dialog)
        assert dialog.notify_time.text() == '19/11/2099 14:30'
        assert dialog.notify_chip.text() == 'Hợp lệ'
        dialog.template.setCurrentIndex(1)
        assert dialog.title.text() == 'Hồ sơ HS-089 sắp đến hạn xử lý.' + chr(10) + 'Hạn: 20/11/2099 14:30'
        assert 'sắp đến hạn xử lý' in dialog.message_text.text()
        from PyQt6.QtCore import QDateTime
        dialog.deadline.setDateTime(QDateTime.fromString('2099-11-21 09:00', 'yyyy-MM-dd HH:mm'))
        assert dialog.title.text().endswith('Hạn: 21/11/2099 09:00')  # Follows deadline.
        dialog.title.setText('Tự sửa nội dung')
        dialog.deadline.setDateTime(QDateTime.fromString('2099-11-20 14:30', 'yyyy-MM-dd HH:mm'))
        assert dialog.title.text() == 'Tự sửa nội dung'  # Edited text is kept.
        assert dialog.message_due.text() == 'Đến hạn: 20/11/2099 14:30:00'
        dialog.duration.presets.setCurrentIndex(0)  # Custom seconds.
        assert dialog.duration.seconds.isVisibleTo(dialog)
        dialog.duration.seconds.setText('abc')
        assert dialog.notify_chip.text() == 'Chưa hợp lệ'
        dialog.duration.seconds.setText('3600')
        value = dialog.value()
        assert value['record_id'] == 1 and value['lead_seconds'] == 3600
        dialog.close()
    """)


def test_reminders_page_checkboxes_and_bulk_delete():
    from test_foundation import run_python

    run_python("""
        import time
        from datetime import datetime, timedelta
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication
        from xaydungso.application.reminders import Reminders
        from xaydungso.core.paths import data_directory
        from xaydungso.infrastructure.database import Database
        from xaydungso.infrastructure.records import SqliteRecords
        from xaydungso.infrastructure.reminders import SqliteReminders
        import xaydungso.presentation.reminders_page as module
        from xaydungso.presentation.tasks import TaskRunner

        class Background:
            def running(self): return False
            def start(self): pass
            def stop(self): pass

        app = QApplication([])
        db = Database(data_directory() / 'rem.sqlite3')
        db.initialize()
        service = Reminders(SqliteReminders(db))
        deadline = datetime(2099, 11, 20, 15, 0)
        for title in ('Lịch A', 'Lịch B', 'Lịch C'):
            service.save(title, deadline_at=deadline, lead_seconds=3600)
        runner = TaskRunner()
        page = module.RemindersPage(service, SqliteRecords(db), Background(), runner)
        page.show()

        def idle():
            limit = time.monotonic() + 5
            QTest.qWait(10)
            while runner.busy:
                assert time.monotonic() < limit
                QTest.qWait(10)

        idle()
        assert page.reminders_table.rowCount() == 3
        assert not page.bulk_bar.isVisible()
        page._cell_clicked(0, 0)
        page._cell_clicked(1, 0)
        assert page.bulk_bar.isVisible() and 'Đã chọn 2' in page.bulk_text.text()
        module.ConfirmBox.exec = lambda self: 0  # Keep: nothing deleted.
        page.bulk_delete_button.click()
        idle()
        assert len(service.list()) == 3
        module.ConfirmBox.exec = lambda self: 1
        page.bulk_delete_button.click()
        idle()
        assert len(service.list()) == 1 and 'Đã xóa 2' in page.feedback.text()
        assert page.reminders_table.rowCount() == 1 and not page.bulk_bar.isVisible()
        page._header_clicked(0)  # Select all on the page.
        assert 'Đã chọn 1' in page.bulk_text.text()
        page.timer.stop()
        page.close()
    """)


def test_table_shows_only_first_non_empty_line_of_a_message():
    from xaydungso.presentation.reminders_page import first_line

    message = chr(10).join(["", "  🔔 THÔNG BÁO  ", "📁 Mã hồ sơ: HS-1", ""])
    assert first_line(message) == "🔔 THÔNG BÁO"
    assert first_line("Một dòng") == "Một dòng"
    assert first_line("") == ""
