"""Approved real-time reminder rules in Asia/Ho_Chi_Minh."""

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from xaydungso.domain.records import ValidationError, validate_duration

LOCAL_ZONE = ZoneInfo("Asia/Ho_Chi_Minh")


def local_time(value: datetime) -> datetime:
    """Naive user inputs represent the approved application timezone."""
    return (
        value.replace(tzinfo=LOCAL_ZONE)
        if value.tzinfo is None
        else value.astimezone(LOCAL_ZONE)
    )


def timestamp(value: datetime) -> str:
    """Canonical UTC strings are chronologically sortable in SQLite."""
    return local_time(value).astimezone(UTC).isoformat(timespec="microseconds")


def permitted(value: datetime) -> bool:
    return time(7) <= local_time(value).time() <= time(23)


def next_morning(value: datetime) -> datetime:
    return (local_time(value) + timedelta(days=1)).replace(
        hour=7, minute=0, second=0, microsecond=0
    )


def notification_time(
    deadline: datetime, created_at: datetime | None = None
) -> datetime:
    """Adjust deadline; if its send time has passed at creation, use next 07:00."""
    deadline = local_time(deadline)
    try:
        result = (
            deadline
            if permitted(deadline)
            else (deadline - timedelta(days=1)).replace(
                hour=22, minute=0, second=0, microsecond=0
            )
        )
        if created_at is not None and result < local_time(created_at):
            result = next_morning(created_at)
    except OverflowError as error:
        raise ValidationError(
            "Thời điểm nhắc nằm ngoài khoảng ngày được hỗ trợ."
        ) from error
    return result


@dataclass(frozen=True)
class Reminder:
    id: str
    title: str
    record_id: int | None
    start_at: datetime
    duration: int
    deadline_at: datetime
    notify_at: datetime
    created_at: datetime


def make_reminder(
    title: str,
    duration: int,
    *,
    start_at: datetime | None = None,
    created_at: datetime | None = None,
    record_id: int | None = None,
    reminder_id: str | None = None,
) -> Reminder:
    validate_duration(duration)
    if not title.strip():
        raise ValidationError("Nội dung nhắc không được để trống.")
    created = local_time(created_at or datetime.now(LOCAL_ZONE))
    start = local_time(start_at or created)
    try:
        deadline = (start.astimezone(UTC) + timedelta(seconds=duration)).astimezone(
            LOCAL_ZONE
        )
    except (OverflowError, ValueError) as error:
        raise ValidationError("Thời lượng vượt quá khoảng ngày được hỗ trợ.") from error
    return Reminder(
        reminder_id or str(uuid4()),
        title.strip(),
        record_id,
        start,
        duration,
        deadline,
        notification_time(deadline, created),
        created,
    )
