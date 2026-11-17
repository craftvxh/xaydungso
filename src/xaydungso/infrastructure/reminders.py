"""Durable reminder schedules and independently claimed channel deliveries."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from xaydungso.domain.records import ValidationError
from xaydungso.domain.reminders import Reminder, timestamp
from xaydungso.infrastructure.database import Database

CHANNELS = ("telegram", "windows")


@dataclass(frozen=True)
class Delivery:
    reminder_id: str
    channel: str
    title: str
    deadline_at: str
    claim_token: str
    attempts: int


class SqliteReminders:
    def __init__(self, database: Database):
        self.database = database

    def save(self, reminder: Reminder, *, editing: bool = False) -> None:
        with self.database.connect() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            if (
                reminder.record_id is not None
                and not connection.execute(
                    "SELECT 1 FROM records WHERE id=?", (reminder.record_id,)
                ).fetchone()
            ):
                raise ValidationError("Hồ sơ liên kết không còn tồn tại.")
            values = (
                reminder.record_id,
                reminder.title,
                timestamp(reminder.start_at),
                reminder.duration,
                timestamp(reminder.deadline_at),
                timestamp(reminder.notify_at),
            )
            if editing:
                row = connection.execute(
                    "SELECT * FROM reminders WHERE id=?", (reminder.id,)
                ).fetchone()
                if row is None or row["cancelled"]:
                    raise ValidationError("Lịch nhắc không còn hoạt động.")
                if connection.execute(
                    "SELECT 1 FROM reminder_deliveries WHERE reminder_id=? AND state IN ('sent','sending')",
                    (reminder.id,),
                ).fetchone():
                    raise ValidationError(
                        "Không thể sửa lịch đã gửi hoặc đang được gửi."
                    )
                connection.execute(
                    "UPDATE reminders SET record_id=?,title=?,start_at=?,duration=?,deadline_at=?,notify_at=? WHERE id=?",
                    (*values, reminder.id),
                )
                connection.execute(
                    "UPDATE reminder_deliveries SET state='pending',next_attempt_at=?,lease_until=NULL,claim_token=NULL,last_error='' WHERE reminder_id=?",
                    (timestamp(reminder.notify_at), reminder.id),
                )
            else:
                connection.execute(
                    "INSERT INTO reminders(record_id,title,start_at,duration,deadline_at,notify_at,id,created_at) VALUES (?,?,?,?,?,?,?,?)",
                    (*values, reminder.id, timestamp(reminder.created_at)),
                )
                connection.executemany(
                    "INSERT INTO reminder_deliveries(reminder_id,channel,next_attempt_at) VALUES (?,?,?)",
                    [
                        (reminder.id, channel, timestamp(reminder.notify_at))
                        for channel in CHANNELS
                    ],
                )

    def list(self) -> list[dict]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT r.*, d.channel,d.state,d.attempts,d.last_error,d.sent_at FROM reminders r "
                "JOIN reminder_deliveries d ON d.reminder_id=r.id ORDER BY r.created_at DESC,r.id,d.channel"
            ).fetchall()
        result = {}
        for row in rows:
            item = result.setdefault(row["id"], {**dict(row), "deliveries": {}})
            item["deliveries"][row["channel"]] = {
                key: row[key] for key in ("state", "attempts", "last_error", "sent_at")
            }
        return list(result.values())

    def cancel(self, reminder_id: str) -> None:
        with self.database.connect() as connection, connection:
            connection.execute(
                "UPDATE reminders SET cancelled=1 WHERE id=?", (reminder_id,)
            )

    def claim(self, now: datetime) -> Delivery | None:
        instant = timestamp(now)
        token = str(uuid4())
        with self.database.connect() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT d.*,r.title,r.deadline_at FROM reminder_deliveries d "
                "JOIN reminders r ON r.id=d.reminder_id WHERE r.cancelled=0 AND r.notify_at<=? "
                "AND ((d.state IN ('pending','failed') AND d.next_attempt_at<=?) "
                "OR (d.state='sending' AND d.lease_until<=?)) "
                "ORDER BY r.notify_at,r.id,d.channel LIMIT 1",
                (instant, instant, instant),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                "UPDATE reminder_deliveries SET state='sending',attempts=attempts+1,claim_token=?,lease_until=? "
                "WHERE reminder_id=? AND channel=?",
                (
                    token,
                    timestamp(now + timedelta(seconds=60)),
                    row["reminder_id"],
                    row["channel"],
                ),
            )
            return Delivery(
                row["reminder_id"],
                row["channel"],
                row["title"],
                row["deadline_at"],
                token,
                row["attempts"] + 1,
            )

    def active(self, delivery: Delivery) -> bool:
        with self.database.connect() as connection:
            return (
                connection.execute(
                    "SELECT 1 FROM reminder_deliveries d JOIN reminders r ON r.id=d.reminder_id "
                    "WHERE r.cancelled=0 AND d.reminder_id=? AND d.channel=? AND d.claim_token=? AND d.state='sending'",
                    (delivery.reminder_id, delivery.channel, delivery.claim_token),
                ).fetchone()
                is not None
            )

    def finish(self, delivery: Delivery, now: datetime, error: str = "") -> None:
        retry = now + timedelta(
            seconds=min(300, 5 * 2 ** min(delivery.attempts - 1, 6))
        )
        with self.database.connect() as connection, connection:
            connection.execute(
                "UPDATE reminder_deliveries SET state=?,sent_at=?,last_error=?,next_attempt_at=?,lease_until=NULL,claim_token=NULL "
                "WHERE reminder_id=? AND channel=? AND state='sending' AND claim_token=?",
                (
                    "failed" if error else "sent",
                    None if error else timestamp(now),
                    error,
                    timestamp(retry),
                    delivery.reminder_id,
                    delivery.channel,
                    delivery.claim_token,
                ),
            )
