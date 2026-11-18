"""Read-only Dashboard use case; calendar semantics live outside widgets."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Protocol

from xaydungso.domain.reminders import LOCAL_ZONE, local_time

# User-approved (18/11/2026): an unfinished record is "sắp hạn" when its
# deadline falls within the next 24 hours.
DUE_SOON = timedelta(hours=24)
ATTENTION_LIMIT = 10


@dataclass(frozen=True)
class UpcomingReminder:
    id: str
    title: str
    record_code: str | None
    notify_at: datetime
    record_name: str | None = None


@dataclass(frozen=True)
class OpenDeadline:
    """An unfinished record that has a deadline (input for attention rules)."""

    id: int
    record_code: str
    applicant_name: str
    address: str
    deadline_at: datetime


@dataclass(frozen=True)
class DashboardSnapshot:
    as_of: datetime
    total_records: int
    incomplete_records: int
    completed_records: int
    todays_reminders: int
    upcoming: tuple[UpcomingReminder, ...]
    open_deadlines: tuple[OpenDeadline, ...] = ()
    overdue_records: int = 0
    attention: tuple[OpenDeadline, ...] = ()
    attention_total: int = 0


class DashboardReader(Protocol):
    def read(
        self, as_of: datetime, day_start: datetime, day_end: datetime
    ) -> DashboardSnapshot: ...


def is_overdue(item: OpenDeadline, as_of: datetime) -> bool:
    return item.deadline_at < as_of


class Dashboard:
    def __init__(
        self,
        reader: DashboardReader,
        clock: Callable[[], datetime] = lambda: datetime.now(LOCAL_ZONE),
    ):
        self.reader, self.clock = reader, clock

    def load(self) -> DashboardSnapshot:
        instant = local_time(self.clock())
        start = instant.replace(hour=0, minute=0, second=0, microsecond=0)
        snapshot = self.reader.read(instant, start, start + timedelta(days=1))
        overdue = sorted(
            (item for item in snapshot.open_deadlines if is_overdue(item, instant)),
            key=lambda item: (item.deadline_at, item.id),
        )
        due_soon = sorted(
            (
                item
                for item in snapshot.open_deadlines
                if instant <= item.deadline_at < instant + DUE_SOON
            ),
            key=lambda item: (item.deadline_at, item.id),
        )
        attention = overdue + due_soon
        return replace(
            snapshot,
            overdue_records=len(overdue),
            attention=tuple(attention[:ATTENTION_LIMIT]),
            attention_total=len(attention),
        )
