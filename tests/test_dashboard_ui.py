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
        assert page.upcoming_table.rowCount() == 0

        service.fail = False
        page.refresh_button.click()
        idle()
        assert all(label.text() == '0' for label in page.metric_values.values())
        assert 'Không có lịch' in page.upcoming_message.text()
        assert 'Không tải được' not in page.feedback.text()

        service.fail = True
        page.refresh_button.click()
        assert all(label.text() == '—' for label in page.metric_values.values())
        idle()
        assert 'Không tải được' in page.feedback.text()
        page.timer.stop()
        page.close()
    """)
