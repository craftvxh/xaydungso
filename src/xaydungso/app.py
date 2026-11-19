"""Composition root and Qt application lifecycle."""

import logging
import sqlite3
import sys

from PyQt6 import sip
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from xaydungso.application.dashboard import Dashboard
from xaydungso.application.records import Records
from xaydungso.application.reminders import Reminders
from xaydungso.application.settings import Settings
from xaydungso.application.templates import Templates
from xaydungso.core.config import AppSettings
from xaydungso.core.logging import configure_logging
from xaydungso.core.paths import data_directory, template_path
from xaydungso.infrastructure.dashboard import SqliteDashboard
from xaydungso.infrastructure.database import Database
from xaydungso.infrastructure.diagnostics import SqliteDiagnostics
from xaydungso.infrastructure.notifications import TelegramNotification
from xaydungso.infrastructure.preferences import FilePreferences
from xaydungso.infrastructure.records import SqliteRecords
from xaydungso.infrastructure.reminders import SqliteReminders
from xaydungso.infrastructure.startup import StartupShortcut
from xaydungso.infrastructure.templates import SqliteTemplates
from xaydungso.infrastructure.tracking_export import SqliteTrackingExporter
from xaydungso.infrastructure.worker_process import BackgroundReminders
from xaydungso.presentation.icons import LOGO
from xaydungso.presentation.main_window import MainWindow
from xaydungso.presentation.single_instance import (
    InstanceServer,
    instance_name,
    notify_running,
)
from xaydungso.presentation.taskbar import set_taskbar_identity
from xaydungso.presentation.theme import configure_theme

logger = logging.getLogger(__name__)


def check_telegram(token, chat):
    """Validate Telegram; returns (message, receiving chat name) for Cài đặt."""
    channel = TelegramNotification(token, chat)
    message = channel.validate_connection()
    return message, channel.chat_name


def main() -> int:
    """Configure and run the single desktop application."""
    settings = AppSettings()
    configure_logging(settings.log_level)
    app = QApplication(sys.argv)
    directory = data_directory()
    instance = instance_name(directory)
    if notify_running(instance):
        logger.info("Already running; showed the open window")
        return 0
    configure_theme(app)
    app.setApplicationName(settings.app_name)
    app.setApplicationDisplayName(settings.window_title)
    app.setWindowIcon(QIcon(str(LOGO)))

    database = Database(directory / "xaydungso.sqlite3")
    user_settings = Settings(
        FilePreferences(directory),
        directory,
        template_path(),
        telegram_checker=check_telegram,
        telegram_tester=lambda token, chat: TelegramNotification(token, chat).send(
            "Xây Dựng Số — Kiểm tra kết nối Telegram", ""
        ),
    )
    try:
        database.initialize()
        preferences = user_settings.load()
    except (OSError, RuntimeError, sqlite3.Error):
        logger.error("Database initialization failed")
        QMessageBox.critical(
            None,
            settings.window_title,
            "Không thể mở cơ sở dữ liệu hoặc cài đặt. Vui lòng kiểm tra quyền truy cập "
            "và phiên bản ứng dụng.",
        )
        return 1

    repository = SqliteRecords(database)
    output_path = user_settings.export_path(preferences)
    records = Records(
        repository,
        SqliteTrackingExporter(
            repository, template_path(), output_path, preferences.excel_policy
        ),
    )
    reminders = Reminders(SqliteReminders(database))
    startup = StartupShortcut(directory)
    try:
        # First start only: run the reminder worker at Windows sign-in.
        if startup.ensure_first_run():
            logger.info("Reminder worker added to Windows startup")
    except RuntimeError:
        logger.warning("Could not add the reminder worker to Windows startup")
    window = MainWindow(
        settings,
        records,
        reminders,
        BackgroundReminders(directory),
        output_path,
        Dashboard(SqliteDashboard(database)),
        user_settings,
        Templates(SqliteTemplates(database)),
        SqliteDiagnostics(database),
        startup,
    )
    set_taskbar_identity(window)  # Taskbar shows the app logo, not Python's.
    window.show()
    server = InstanceServer(window.bring_to_front, instance, app)
    logger.info("Application started")
    exit_code = app.exec()
    logger.info("Application stopped (exit code %s)", exit_code)
    # Delete the window (with its tray icon) while QApplication still exists. The
    # tray and the instance server keep Python references to the window, so it
    # would otherwise be destroyed at interpreter exit, after QApplication, and
    # crash in Qt6Widgets (0xC0000005) after a clean exit.
    server.close()
    sip.delete(window)
    return exit_code
