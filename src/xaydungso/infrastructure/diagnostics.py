"""Read-only facts shown on the Cài đặt page (no writes, no backup/repair)."""

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from xaydungso.domain.reminders import LOCAL_ZONE, timestamp
from xaydungso.infrastructure.database import Database


@dataclass(frozen=True)
class DatabaseStatus:
    path: Path
    size_bytes: int
    sqlite_version: str
    schema_version: int
    records: int
    integrity: str  # "ok" or the first quick_check message.
    checked_at: datetime


@dataclass(frozen=True)
class ExcelStatus:
    exists: bool
    modified_at: datetime | None
    written_records: int


class SqliteDiagnostics:
    def __init__(self, database: Database):
        self.database = database

    def database_status(self) -> DatabaseStatus:
        with self.database.connect() as connection:
            schema = connection.execute("PRAGMA user_version").fetchone()[0]
            records = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
            # quick_check is read-only; it reports problems but repairs nothing.
            integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
        path = Path(self.database.path)
        return DatabaseStatus(
            path,
            path.stat().st_size if path.exists() else 0,
            sqlite3.sqlite_version,
            schema,
            records,
            integrity,
            datetime.now(LOCAL_ZONE),
        )

    def telegram_sent_today(self) -> int:
        start = datetime.now(LOCAL_ZONE).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        with self.database.connect() as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM reminder_deliveries WHERE channel='telegram' "
                "AND state='sent' AND sent_at>=? AND sent_at<?",
                (timestamp(start), timestamp(start + timedelta(days=1))),
            ).fetchone()[0]

    def excel_status(self, workbook: Path | None) -> ExcelStatus:
        if workbook is None or not Path(workbook).is_file():
            return ExcelStatus(False, None, 0)
        path = Path(workbook).resolve()
        modified = datetime.fromtimestamp(path.stat().st_mtime, LOCAL_ZONE)
        key = os.path.normcase(str(path))  # Same key the exporter stores.
        with self.database.connect() as connection:
            written = connection.execute(
                "SELECT COUNT(*) FROM excel_record_links WHERE workbook_path=?", (key,)
            ).fetchone()[0]
        return ExcelStatus(True, modified, written)
