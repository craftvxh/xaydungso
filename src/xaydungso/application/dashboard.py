"""Read-only Dashboard use case; calendar semantics live outside widgets."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from xaydungso.domain.reminders import LOCAL_ZONE, local_time


@dataclass(frozen=True)
class UpcomingReminder:
    id: str
    title: str
    record_code: str | None
    notify_at: datetime


@dataclass(frozen=True)
class DashboardSnapshot:
    as_of: datetime
    total_records: int
    incomplete_records: int
    completed_records: int
    todays_reminders: int
    upcoming: tuple[UpcomingReminder, ...]


class DashboardReader(Protocol):
    def read(
        self, as_of: datetime, day_start: datetime, day_end: datetime
    ) -> DashboardSnapshot: ...


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
        return self.reader.read(instant, start, start + timedelta(days=1))
