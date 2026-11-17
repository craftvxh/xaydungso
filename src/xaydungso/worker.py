"""GUI-independent reminder process: python -m xaydungso.worker."""

import argparse
import logging
import sqlite3
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from xaydungso.application.reminders import ReminderEngine
from xaydungso.core.logging import configure_logging
from xaydungso.core.paths import data_directory
from xaydungso.infrastructure.database import Database, DatabaseVersionError
from xaydungso.infrastructure.notifications import (
    TelegramNotification,
    WindowsNotification,
)
from xaydungso.infrastructure.reminders import SqliteReminders
from xaydungso.infrastructure.worker_process import worker_lock


def main() -> int:
    parser = argparse.ArgumentParser(description="Tiến trình nhắc nhở Xây Dựng Số")
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument(
        "--once", action="store_true", help="Xử lý lịch đến hạn một lần rồi thoát"
    )
    args = parser.parse_args()
    directory = args.data_dir or data_directory()
    configure_logging()
    with worker_lock(directory) as acquired:
        if not acquired:
            return 0
        (directory / "reminder-worker.stop").unlink(missing_ok=True)
        handler = RotatingFileHandler(
            directory / "reminders.log",
            maxBytes=256_000,
            backupCount=1,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logging.getLogger().addHandler(handler)
        logger = logging.getLogger(__name__)
        database = Database(directory / "xaydungso.sqlite3")
        try:
            database.initialize()
        except (OSError, sqlite3.Error, DatabaseVersionError):
            logger.error("Database initialization failed; reminder worker stopped")
            logging.getLogger().removeHandler(handler)
            handler.close()
            return 1
        stop_file = directory / "reminder-worker.stop"
        engine = ReminderEngine(
            SqliteReminders(database),
            {
                "telegram": TelegramNotification(),
                "windows": WindowsNotification(),
            },
            should_stop=stop_file.exists,
        )
        logger.info("Reminder worker started")
        while not stop_file.exists():
            try:
                engine.tick()
            except Exception:
                logger.error("Reminder tick failed; will retry")
            if args.once:
                break
            time.sleep(1)
        logger.info("Reminder worker stopped")
        logging.getLogger().removeHandler(handler)
        handler.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
