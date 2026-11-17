"""Composition root and Qt application lifecycle."""

import logging
import sqlite3
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from xaydungso.application.dashboard import Dashboard
from xaydungso.application.records import Records
from xaydungso.application.reminders import Reminders
from xaydungso.core.config import AppSettings
from xaydungso.core.logging import configure_logging
from xaydungso.core.paths import data_directory, template_path
from xaydungso.infrastructure.dashboard import SqliteDashboard
from xaydungso.infrastructure.database import Database
from xaydungso.infrastructure.records import SqliteRecords
from xaydungso.infrastructure.reminders import SqliteReminders
from xaydungso.infrastructure.tracking_export import SqliteTrackingExporter
from xaydungso.infrastructure.worker_process import BackgroundReminders
from xaydungso.presentation.main_window import MainWindow

logger = logging.getLogger(__name__)


def main() -> int:
    """Configure and run the single desktop application."""
    settings = AppSettings()
    configure_logging(settings.log_level)
    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    app.setApplicationDisplayName(settings.window_title)

    directory = data_directory()
    database = Database(directory / "xaydungso.sqlite3")
    try:
        database.initialize()
    except (OSError, RuntimeError, sqlite3.Error):
        logger.error("Database initialization failed")
        QMessageBox.critical(
            None,
            settings.window_title,
            "Không thể mở cơ sở dữ liệu. Vui lòng kiểm tra quyền truy cập "
            "và phiên bản ứng dụng.",
        )
        return 1

    repository = SqliteRecords(database)
    output_path = directory / "so_theo_doi.xlsx"
    records = Records(
        repository, SqliteTrackingExporter(repository, template_path(), output_path)
    )
    reminders = Reminders(SqliteReminders(database))
    window = MainWindow(
        settings,
        records,
        reminders,
        BackgroundReminders(directory),
        output_path,
        Dashboard(SqliteDashboard(database)),
    )
    window.show()
    logger.info("Application started")
    exit_code = app.exec()
    logger.info("Application stopped (exit code %s)", exit_code)
    return exit_code
