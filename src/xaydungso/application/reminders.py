"""Scheduler policy independent of Qt, Excel, and notification transports."""

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Protocol

from xaydungso.domain.reminders import LOCAL_ZONE, make_reminder, permitted


class ReminderStore(Protocol):
    def save(self, reminder, *, editing: bool = False) -> None: ...
    def list(self) -> list[dict]: ...
    def cancel(self, reminder_id: str) -> None: ...
    def claim(self, now: datetime): ...
    def active(self, delivery) -> bool: ...
    def finish(self, delivery, now: datetime, error: str = "") -> None: ...


class NotificationChannel(Protocol):
    def send(self, title: str, message: str) -> None: ...


class Reminders:
    def __init__(self, store: ReminderStore):
        self.store = store

    def save(
        self,
        title: str,
        duration: int,
        *,
        start_at=None,
        record_id=None,
        reminder_id=None,
    ):
        reminder = make_reminder(
            title,
            duration,
            start_at=start_at,
            record_id=record_id,
            reminder_id=reminder_id,
        )
        self.store.save(reminder, editing=reminder_id is not None)
        return reminder

    def list(self):
        return self.store.list()

    def cancel(self, reminder_id: str):
        self.store.cancel(reminder_id)


class ReminderEngine:
    def __init__(
        self,
        store: ReminderStore,
        channels: Mapping[str, NotificationChannel],
        clock: Callable[[], datetime] = lambda: datetime.now(LOCAL_ZONE),
        should_stop: Callable[[], bool] = lambda: False,
    ):
        self.store, self.channels, self.clock = store, channels, clock
        self.should_stop = should_stop

    def tick(self, limit: int = 50) -> int:
        delivered = 0
        for _ in range(limit):
            if self.should_stop():
                break
            now = self.clock()
            if not permitted(now):
                break
            delivery = self.store.claim(now)
            if delivery is None:
                break
            if not self.store.active(delivery):
                continue
            try:
                deadline = datetime.fromisoformat(delivery.deadline_at).astimezone(
                    LOCAL_ZONE
                )
                self.channels[delivery.channel].send(
                    "Xây Dựng Số — Nhắc nhở",
                    f"{delivery.title}\nĐến hạn: {deadline:%d/%m/%Y %H:%M:%S}\nMã nhắc: {delivery.reminder_id}",
                )
            except Exception:
                # Never persist transport exceptions: URLs may contain bot credentials.
                self.store.finish(
                    delivery,
                    self.clock(),
                    "Kênh chưa cấu hình hoặc gửi thất bại; sẽ thử lại.",
                )
            else:
                self.store.finish(delivery, self.clock())
                delivered += 1
        return delivered
