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
    Migration(
        4,
        (
            "ALTER TABLE records ADD COLUMN deadline_at TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE records ADD COLUMN reminder_lead_seconds INTEGER CHECK(reminder_lead_seconds IS NULL OR (typeof(reminder_lead_seconds)='integer' AND reminder_lead_seconds > 0))",
            "ALTER TABLE reminders ADD COLUMN lead_seconds INTEGER CHECK(lead_seconds IS NULL OR (typeof(lead_seconds)='integer' AND lead_seconds > 0))",
            "ALTER TABLE reminders ADD COLUMN record_managed INTEGER NOT NULL DEFAULT 0 CHECK(record_managed IN (0,1))",
            "CREATE TABLE excel_record_links (workbook_path TEXT NOT NULL, record_id INTEGER NOT NULL, record_code TEXT NOT NULL, PRIMARY KEY(workbook_path, record_id))",
        ),
    ),
    Migration(5, ("UPDATE reminders SET record_managed=0 WHERE record_managed=1",)),
    # Column G is now "Ngày hẹn trả"; the rename keeps existing manual text values.
    Migration(
        6,
        (
            "ALTER TABLE records RENAME COLUMN overall_processing_time"
            " TO return_appointment_date",
        ),
    ),
    # Notification templates managed on the Nhắc nhở > Cấu hình screen.
    Migration(
        7,
        (
            """CREATE TABLE notification_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL CHECK(length(trim(name)) > 0),
            body TEXT NOT NULL CHECK(length(trim(body)) > 0),
            is_default INTEGER NOT NULL DEFAULT 0 CHECK(is_default IN (0,1)),
            updated_at TEXT NOT NULL
        )""",
            # At most one default template.
            "CREATE UNIQUE INDEX one_default_template ON notification_templates"
            "(is_default) WHERE is_default=1",
            "INSERT INTO notification_templates(name,body,is_default,updated_at) VALUES "
            "('Nhắc hồ sơ sắp đến hạn',"
            " '🔔 THÔNG BÁO HỒ SƠ SẮP ĐẾN HẠN' || char(10) ||"
            " '📁 Mã hồ sơ: {{ma_ho_so}}' || char(10) ||"
            " '👤 Người nộp: {{ho_ten}}' || char(10) ||"
            " '📅 Hạn xử lý: {{han_xu_ly}}' || char(10) ||"
            " '⚠️ Vui lòng kiểm tra và hoàn thiện hồ sơ đúng thời hạn quy định.',"
            " 1, strftime('%Y-%m-%dT%H:%M:%S+00:00','now')),"
            "('Ngắn gọn: mã hồ sơ — người nộp', 'Hồ sơ {{ma_ho_so}} — {{ho_ten}}', 0,"
            " strftime('%Y-%m-%dT%H:%M:%S+00:00','now')),"
            "('Kiểm tra tiến độ', 'Kiểm tra tiến độ hồ sơ {{ma_ho_so}} — {{ho_ten}}.', 0,"
            " strftime('%Y-%m-%dT%H:%M:%S+00:00','now')),"
            "('Hẹn trả kết quả', 'Chuẩn bị trả kết quả hồ sơ {{ma_ho_so}} cho {{ho_ten}}.',"
            " 0, strftime('%Y-%m-%dT%H:%M:%S+00:00','now'))",
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
