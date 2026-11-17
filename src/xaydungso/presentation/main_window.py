"""Fluent navigation into the record and reminder use cases."""

from qfluentwidgets import FluentIcon, FluentWindow

from xaydungso.core.config import AppSettings
from xaydungso.presentation.dashboard import DashboardPage
from xaydungso.presentation.pages import RecordsPage, RemindersPage
from xaydungso.presentation.tasks import TaskRunner


class MainWindow(FluentWindow):
    def __init__(
        self,
        settings: AppSettings,
        records,
        reminders,
        background,
        output_path,
        dashboard,
    ):
        super().__init__()
        self.setWindowTitle(settings.window_title)
        self.resize(settings.window_width, settings.window_height)
        self.runner = TaskRunner(self)
        self.dashboard_page = DashboardPage(dashboard, self.runner, self)
        self.records_page = RecordsPage(records, self.runner, output_path, self)
        self.reminders_page = RemindersPage(
            reminders, records, background, self.runner, self
        )
        self.addSubInterface(self.dashboard_page, FluentIcon.HOME, "Tổng quan")
        self.addSubInterface(self.records_page, FluentIcon.DOCUMENT, "Hồ sơ")
        self.addSubInterface(self.reminders_page, FluentIcon.HISTORY, "Nhắc nhở")
        self.switchTo(self.dashboard_page)
        self.dashboard_page.open_records.connect(
            lambda: self.switchTo(self.records_page)
        )
        self.dashboard_page.open_reminders.connect(
            lambda: self.switchTo(self.reminders_page)
        )
        self.records_page.changed.connect(self.reminders_page.refresh)
        self.records_page.changed.connect(self.dashboard_page.refresh)
        self.reminders_page.changed.connect(self.dashboard_page.refresh)
        self.stackedWidget.currentChanged.connect(self._page_changed)
        self.records_page.remind.connect(self._remind)

    def _remind(self, record):
        self.switchTo(self.reminders_page)
        self.reminders_page.edit(record=record)

    def _page_changed(self, *_):
        if self.stackedWidget.currentWidget() is self.dashboard_page:
            self.dashboard_page.refresh()

    def closeEvent(self, event):
        if self.runner.busy:
            self.stackedWidget.currentWidget().feedback.setText(
                "Đang xử lý dữ liệu. Vui lòng đợi hoàn tất rồi đóng cửa sổ."
            )
            event.ignore()
            return
        self.dashboard_page.timer.stop()
        self.reminders_page.timer.stop()
        super().closeEvent(event)
