"""SQLite connection lifecycle and atomic, forward-only schema migrations."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

APPLICATION_ID = 0x5844534F  # XDSO; reject accidental use of another app's database.


class DatabaseVersionError(RuntimeError):
    """Database ownership or schema version is incompatible."""


@dataclass(frozen=True)
class Migration:
    version: int
    statements: tuple[str, ...]


# Keep version 1 immutable so existing Foundation databases upgrade in place.
MIGRATIONS = (
    Migration(1, ()),
    Migration(
        2,
        (
            """CREATE TABLE records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_code TEXT NOT NULL UNIQUE CHECK(length(trim(record_code)) > 0),
            applicant_name TEXT NOT NULL CHECK(length(trim(applicant_name)) > 0),
            phone TEXT NOT NULL DEFAULT '', address TEXT NOT NULL DEFAULT '',
            received_at TEXT NOT NULL DEFAULT '',
            processing_duration INTEGER CHECK(processing_duration IS NULL OR
                (typeof(processing_duration)='integer' AND processing_duration > 0)),
            reminder_tracking_time TEXT NOT NULL DEFAULT '',
            overall_processing_time TEXT NOT NULL DEFAULT '',
            drawing_stamp_status INTEGER NOT NULL DEFAULT 0 CHECK(drawing_stamp_status IN (0,1)),
            permit_stamp_status INTEGER NOT NULL DEFAULT 0 CHECK(permit_stamp_status IN (0,1)),
            handover_at TEXT NOT NULL DEFAULT '',
            signature_status INTEGER NOT NULL DEFAULT 0 CHECK(signature_status IN (0,1)),
            recipient_name TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Chưa hoàn thành'
                CHECK(status IN ('Chưa hoàn thành', 'Đã hoàn thành')),
            notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
        )""",
            "CREATE INDEX records_order ON records(created_at, id)",
        ),
    ),
    Migration(
        3,
        (
            """CREATE TABLE reminders (
            id TEXT PRIMARY KEY NOT NULL,
            record_id INTEGER REFERENCES records(id) ON DELETE SET NULL,
            title TEXT NOT NULL CHECK(length(trim(title)) > 0),
            start_at TEXT NOT NULL, duration INTEGER NOT NULL CHECK(typeof(duration)='integer' AND duration > 0),
            deadline_at TEXT NOT NULL, notify_at TEXT NOT NULL, created_at TEXT NOT NULL,
            cancelled INTEGER NOT NULL DEFAULT 0 CHECK(cancelled IN (0,1))
        )""",
            """CREATE TABLE reminder_deliveries (
            reminder_id TEXT NOT NULL REFERENCES reminders(id) ON DELETE CASCADE,
            channel TEXT NOT NULL CHECK(channel IN ('telegram','windows')),
            state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','sending','sent','failed')),
            attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts >= 0),
            next_attempt_at TEXT NOT NULL, lease_until TEXT,
            claim_token TEXT, sent_at TEXT, last_error TEXT NOT NULL DEFAULT '',
            PRIMARY KEY(reminder_id, channel)
        )""",
            "CREATE INDEX reminders_due ON reminders(cancelled, notify_at)",
            "CREATE INDEX deliveries_due ON reminder_deliveries(state, next_attempt_at)",
        ),
    ),
)


class Database:
    """Open short-lived connections; callers explicitly own each transaction."""

    def __init__(
        self, path: Path, migrations: tuple[Migration, ...] = MIGRATIONS
    ) -> None:
        if not migrations or tuple(item.version for item in migrations) != tuple(
            range(1, len(migrations) + 1)
        ):
            raise ValueError("Migrations must start at 1 and be consecutive")
        self.path = Path(path)
        self.migrations = migrations

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Enable foreign keys on every connection and always close it."""
        connection = sqlite3.connect(self.path, timeout=5)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.row_factory = sqlite3.Row
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        """Migrate under one write lock; failures roll back schema and version."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                application_id = connection.execute("PRAGMA application_id").fetchone()[
                    0
                ]
                version = connection.execute("PRAGMA user_version").fetchone()[0]
                if application_id not in (0, APPLICATION_ID):
                    raise DatabaseVersionError(
                        "Database belongs to another application"
                    )
                if application_id == 0 and (
                    version
                    or connection.execute(
                        "SELECT 1 FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
                    ).fetchone()
                ):
                    raise DatabaseVersionError("Refusing an unrecognized database")
                if version > len(self.migrations):
                    raise DatabaseVersionError("Database requires a newer application")
                if application_id == APPLICATION_ID and version < 1:
                    raise DatabaseVersionError("Database baseline version is missing")
                for migration in self.migrations[version:]:
                    for statement in migration.statements:
                        connection.execute(statement)
                    connection.execute(f"PRAGMA user_version = {migration.version}")
                connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
                connection.commit()
            except BaseException:
                connection.rollback()
                raise
