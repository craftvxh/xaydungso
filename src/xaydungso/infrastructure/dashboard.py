"""Consistent read-only SQLite dashboard snapshot; no Excel dependency."""

from datetime import datetime

from xaydungso.application.dashboard import DashboardSnapshot, UpcomingReminder
from xaydungso.domain.records import RecordStatus
from xaydungso.domain.reminders import timestamp
from xaydungso.infrastructure.database import Database


class SqliteDashboard:
    def __init__(self, database: Database):
        self.database = database

    def read(
        self, as_of: datetime, day_start: datetime, day_end: datetime
    ) -> DashboardSnapshot:
        with self.database.connect() as connection, connection:
            connection.execute("BEGIN")
            records = connection.execute(
                "SELECT COUNT(*) AS total, COALESCE(SUM(status=?),0) AS incomplete, "
                "COALESCE(SUM(status=?),0) AS completed FROM records",
                (RecordStatus.INCOMPLETE.value, RecordStatus.COMPLETE.value),
            ).fetchone()
            today = connection.execute(
                "SELECT COUNT(*) FROM reminders WHERE cancelled=0 AND notify_at>=? AND notify_at<?",
                (timestamp(day_start), timestamp(day_end)),
            ).fetchone()[0]
            upcoming = connection.execute(
                "SELECT r.id,r.title,r.notify_at,records.record_code FROM reminders r "
                "LEFT JOIN records ON records.id=r.record_id "
                "WHERE r.cancelled=0 AND r.notify_at>=? AND EXISTS "
                "(SELECT 1 FROM reminder_deliveries d WHERE d.reminder_id=r.id AND d.state!='sent') "
                "ORDER BY r.notify_at ASC,r.id ASC LIMIT 10",
                (timestamp(as_of),),
            ).fetchall()
        return DashboardSnapshot(
            as_of,
            records["total"],
            records["incomplete"],
            records["completed"],
            today,
            tuple(
                UpcomingReminder(
                    row["id"],
                    row["title"],
                    row["record_code"],
                    datetime.fromisoformat(row["notify_at"]),
                )
                for row in upcoming
            ),
        )
