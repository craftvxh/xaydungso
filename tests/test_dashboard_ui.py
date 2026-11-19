"""Loading/error/retry and navigation without exposing adapter errors."""

from test_foundation import run_python


def test_dashboard_loading_error_recovery_and_navigation():
    run_python("""
        import threading
        import time
        from datetime import datetime
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication
        from xaydungso.application.dashboard import DashboardSnapshot
        from xaydungso.domain.reminders import local_time
        from xaydungso.presentation.dashboard import DashboardPage
        from xaydungso.presentation.tasks import TaskRunner

        app = QApplication([])
        ready = threading.Event()
        class Service:
            fail = True
            def load(self):
                assert ready.wait(5)
                if self.fail:
                    raise OSError('private database path and SQL details')
                return DashboardSnapshot(local_time(datetime(2026, 11, 18, 9)), 0, 0, 0, 0, ())

        service = Service()
        runner = TaskRunner()
        page = DashboardPage(service, runner)
        page.show()
        assert page.loading
        assert all(label.text() == '—' for label in page.metric_values.values())
        assert 'Đang tải' in page.feedback.text()
        assert not page.refresh_button.isEnabled()
        navigations = []
        page.open_records.connect(lambda: navigations.append('records'))
        page.open_reminders.connect(lambda: navigations.append('reminders'))
        page.records_button.click()
        page.reminders_button.click()
        assert navigations == ['records', 'reminders']

        def idle():
            deadline = time.monotonic() + 5
            while runner.busy:
                assert time.monotonic() < deadline
                QTest.qWait(10)

        ready.set()
        idle()
        assert not page.loading
        assert page.refresh_button.isEnabled()
        assert 'Không tải được' in page.feedback.text()
        assert 'private' not in page.feedback.text()
        assert all(label.text() == '—' for label in page.metric_values.values())
        assert page.upcoming_items == []

        service.fail = False
        page.refresh_button.click()
        idle()
        assert all(label.text() == '0' for label in page.metric_values.values())
        assert 'Không có lịch' in page.upcoming_empty.title.text()
        assert 'Không tải được' not in page.feedback.text()

        service.fail = True
        page.refresh_button.click()
        assert all(label.text() == '—' for label in page.metric_values.values())
        idle()
        assert 'Không tải được' in page.feedback.text()
        page.timer.stop()
        page.close()
    """)


def test_dashboard_attention_table_overdue_card_and_detail_link():
    run_python("""
        import time
        from datetime import datetime, timedelta
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication
        from xaydungso.application.dashboard import (
            DashboardSnapshot, OpenDeadline, UpcomingReminder)
        from xaydungso.domain.reminders import local_time
        from xaydungso.presentation.dashboard import DashboardPage
        from xaydungso.presentation.tasks import TaskRunner

        app = QApplication([])
        now = local_time(datetime(2026, 11, 18, 10))
        late = OpenDeadline(7, 'HS-021', 'Nguyễn Văn A', 'Số 142', now - timedelta(hours=3))
        soon = OpenDeadline(9, 'HS-027', 'Trần Văn B', 'Lô B2', now + timedelta(hours=2))
        reminder = UpcomingReminder('r1', 'Nhắc kiểm tra', 'HS-027', now + timedelta(hours=1), 'Trần Văn B')
        class Service:
            def load(self):
                return DashboardSnapshot(now, 4, 3, 1, 1, (reminder,), (),
                                         overdue_records=1, attention=(late, soon),
                                         attention_total=2)
        runner = TaskRunner()
        page = DashboardPage(Service(), runner)
        page.show()
        deadline = time.monotonic() + 5
        QTest.qWait(10)
        while runner.busy:
            assert time.monotonic() < deadline
            QTest.qWait(10)
        assert page.metric_values['overdue_records'].text() == '1'
        assert not page.metric_chips['incomplete_records'].isVisible()  # No % chip.
        assert page.metric_chips['overdue_records'].isVisible()
        assert page.attention_count.text() == '2 hồ sơ'
        assert page.attention_table.rowCount() == 2
        assert page.attention_table.item(0, 0).text() == 'HS-021'
        badge = page.attention_table.cellWidget(1, 4).layout().itemAt(0).widget()
        assert badge.text() == 'Sắp hạn (Còn 2 giờ)'
        opened = []
        page.open_record.connect(opened.append)
        page.attention_table.cellWidget(0, 5).layout().itemAt(0).widget().click()
        assert opened == [7]
        assert len(page.upcoming_items) == 1 and 'Đồng bộ: 10:00' in page.sync.text()
        page.timer.stop()
        page.close()
    """)
