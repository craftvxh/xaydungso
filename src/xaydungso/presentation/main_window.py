"""Fluent navigation into the record and reminder use cases."""

from PyQt6.QtGui import QColor
from qfluentwidgets import FluentWindow, NavigationItemPosition

from xaydungso.core.config import AppSettings
from xaydungso.presentation.dashboard import DashboardPage
from xaydungso.presentation.icons import Icon
from xaydungso.presentation.pages import RecordsPage, RemindersPage
from xaydungso.presentation.settings import SettingsPage
from xaydungso.presentation.shell import nav_badge, set_badge, style_shell
from xaydungso.presentation.tasks import TaskRunner
from xaydungso.presentation.templates_page import TemplatesPage


class MainWindow(FluentWindow):
    def _normalBackgroundColor(self):
        return QColor("#ffffff")

    def __init__(
        self,
        settings: AppSettings,
        records,
        reminders,
        background,
        output_path,
        dashboard,
        user_settings=None,
        templates=None,
        diagnostics=None,
    ):
        super().__init__()
        self.setMicaEffectEnabled(False)
        self.setCustomBackgroundColor("#ffffff", "#ffffff")
        self.setWindowTitle(settings.window_title)
        self.setWindowIcon(Icon.LAYOUT.icon())
        style_shell(self, settings.window_title)
        self.resize(settings.window_width, settings.window_height)
        # Keep the navigation panel expanded by default; the menu button still collapses it.
        self.navigationInterface.setExpandWidth(220)
        self.navigationInterface.setMinimumExpandWidth(0)
        self.navigationInterface.expand(useAni=False)
        self.runner = TaskRunner(self)
        self.dashboard_page = DashboardPage(dashboard, self.runner, self)
        self.records_page = RecordsPage(records, self.runner, output_path, self)
        self.reminders_page = RemindersPage(
            reminders, records, background, self.runner, self, templates
        )
        self.addSubInterface(self.dashboard_page, Icon.HOME, "Tổng quan")
        self.addSubInterface(self.records_page, Icon.FOLDER, "Quản lý hồ sơ")
        self.addSubInterface(self.reminders_page, Icon.RINGER, "Nhắc nhở")
        if user_settings is not None:
            self.settings_page = SettingsPage(
                user_settings,
                self.runner,
                output_path,
                self,
                diagnostics=diagnostics,
                export=records.export,
            )
            self.addSubInterface(
                self.settings_page,
                Icon.SETTING,
                "Cài đặt",
                NavigationItemPosition.BOTTOM,
            )
        self.records_badge = nav_badge(self, self.records_page)
        self.reminders_badge = nav_badge(self, self.reminders_page, alert=True)
        self.dashboard_page.loaded.connect(self._badges)
        self.switchTo(self.dashboard_page)
        self.dashboard_page.open_records.connect(
            lambda: self.switchTo(self.records_page)
        )
        self.dashboard_page.open_reminders.connect(
            lambda: self.switchTo(self.reminders_page)
        )
        self.dashboard_page.add_record.connect(self._add_record)
        if templates is not None:
            # Shown inside the Nhắc nhở tab (no sidebar item of its own).
            self.templates_page = TemplatesPage(templates, self.runner, self)
            self.stackedWidget.addWidget(self.templates_page)
            self.reminders_page.open_templates.connect(
                lambda: self.switchTo(self.templates_page)
            )
            self.templates_page.back.connect(self._back_to_reminders)
        else:
            self.reminders_page.settings_button.hide()
        self.dashboard_page.open_record.connect(self._open_record)
        self.records_page.changed.connect(self.reminders_page.refresh)
        self.records_page.changed.connect(self.dashboard_page.refresh)
        self.reminders_page.changed.connect(self.dashboard_page.refresh)
        self.stackedWidget.currentChanged.connect(self._page_changed)
        self.records_page.remind.connect(self._remind)

    def _badges(self, snapshot):
        # Same figures as the Dashboard cards: open records, reminders due today.
        set_badge(self.records_badge, snapshot.incomplete_records)
        set_badge(self.reminders_badge, snapshot.todays_reminders)

    def _back_to_reminders(self):
        self.switchTo(self.reminders_page)
        self.reminders_page.refresh()

    def _add_record(self):
        self.switchTo(self.records_page)
        self.records_page.edit(None)

    def _open_record(self, record_id):
        self.switchTo(self.records_page)
        self.records_page.focus_record(record_id)

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
