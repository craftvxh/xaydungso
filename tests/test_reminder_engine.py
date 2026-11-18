"""Real SQLite and fake transports: no external messages sent by tests."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pytest

from xaydungso.application.ports import NotificationError
from xaydungso.application.reminders import ReminderEngine
from xaydungso.domain.records import RecordData, ValidationError
from xaydungso.domain.reminders import local_time, make_reminder
from xaydungso.infrastructure.records import SqliteRecords
from xaydungso.infrastructure.reminders import SqliteReminders


class Channel:
    def __init__(self, failures=0):
        self.calls = []
        self.failures = failures

    def send(self, title, message):
        if self.failures:
            self.failures -= 1
            raise RuntimeError("Sensitive transport error must not be stored")
        self.calls.append((title, message))


def scheduled(database, record_id=None):
    now = local_time(datetime(2026, 11, 18, 9))
    store = SqliteReminders(database)
    reminder = make_reminder("Lịch thử", 10, created_at=now, record_id=record_id)
    store.save(reminder)
    return store, reminder, now + timedelta(seconds=10)


def test_due_once_per_channel_retry_and_restart(database):
    store, reminder, now = scheduled(database)
    telegram, windows = Channel(1), Channel()
    clock = [now]
    engine = ReminderEngine(
        store, {"telegram": telegram, "windows": windows}, lambda: clock[0]
    )
    assert engine.tick() == 1
    assert engine.tick() == 0
    assert len(windows.calls) == 1
    states = store.list()[0]["deliveries"]
    assert states["telegram"]["state"] == "failed"
    assert "Sensitive" not in states["telegram"]["last_error"]
    clock[0] += timedelta(seconds=6)
    assert engine.tick() == 1
    assert len(telegram.calls) == len(windows.calls) == 1
    restarted = ReminderEngine(
        SqliteReminders(database),
        {"telegram": telegram, "windows": windows},
        lambda: clock[0],
    )
    assert restarted.tick() == 0
    assert all(
        result["state"] == "sent" for result in store.list()[0]["deliveries"].values()
    )
    assert reminder.id in telegram.calls[0][1]


def test_safe_telegram_diagnostic_is_visible_on_delivery(database):
    store, _, now = scheduled(database)

    class Misconfigured:
        def send(self, title, message):
            raise NotificationError("Chat ID đang là ID của chính bot.")

    engine = ReminderEngine(
        store, {"telegram": Misconfigured(), "windows": Channel()}, lambda: now
    )
    assert engine.tick() == 1
    state = store.list()[0]["deliveries"]
    assert state["telegram"]["last_error"] == "Chat ID đang là ID của chính bot."
    assert state["windows"]["state"] == "sent"


def test_missed_schedule_waits_until_permitted_window(database):
    store, _, now = scheduled(database)
    channels = {"telegram": Channel(), "windows": Channel()}
    clock = [now + timedelta(days=1)]
    clock[0] = clock[0].replace(hour=6)
    engine = ReminderEngine(store, channels, lambda: clock[0])
    assert engine.tick() == 0
    clock[0] = clock[0].replace(hour=7)
    assert engine.tick() == 2
    assert engine.tick() == 0


def test_edit_unsent_recalculates_and_cannot_edit_sent(database):
    store, reminder, now = scheduled(database)
    edited = make_reminder("Sửa", 3600, created_at=now, reminder_id=reminder.id)
    store.save(edited, editing=True)
    assert store.list()[0]["notify_at"] != reminder.notify_at.isoformat()
    engine = ReminderEngine(
        store, {"telegram": Channel(), "windows": Channel()}, lambda: edited.notify_at
    )
    assert engine.tick() == 2
    with pytest.raises(ValidationError):
        store.save(edited, editing=True)


def test_cancel_and_delete_record_prevent_unsent_deliveries(database):
    records = SqliteRecords(database)
    record = records.save(RecordData("001", "Tên mẫu"))
    store, reminder, now = scheduled(database, record.id)
    records.delete(record.id)
    row = store.list()[0]
    assert row["cancelled"] == 1
    assert row["record_id"] is None
    assert (
        ReminderEngine(
            store, {"telegram": Channel(), "windows": Channel()}, lambda: now
        ).tick()
        == 0
    )
    other = make_reminder("Không liên kết", 10, created_at=now)
    store.save(other)
    store.cancel(other.id)
    assert store.claim(now + timedelta(seconds=20)) is None
    with pytest.raises(ValidationError):
        store.save(make_reminder("Mất hồ sơ", 10, record_id=record.id))


def test_two_engines_do_not_claim_successful_channel_twice(database):
    store, _, now = scheduled(database)
    channels = {"telegram": Channel(), "windows": Channel()}
    engines = [
        ReminderEngine(SqliteReminders(database), channels, lambda: now)
        for _ in range(2)
    ]
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sum(executor.map(lambda engine: engine.tick(), engines)) == 2
    assert all(len(channel.calls) == 1 for channel in channels.values())


def test_expired_claim_is_recoverable_and_old_token_cannot_finish(database):
    store, _, now = scheduled(database)
    first = store.claim(now)
    second = store.claim(now)
    assert first.channel != second.channel
    assert store.claim(now) is None
    reclaimed = store.claim(now + timedelta(seconds=61))
    assert reclaimed.reminder_id == first.reminder_id
    assert reclaimed.channel == first.channel
    assert reclaimed.claim_token != first.claim_token
    store.finish(first, now)
    assert store.active(reclaimed)
    store.finish(reclaimed, now + timedelta(seconds=61))
    assert not store.active(reclaimed)


def test_stop_request_does_not_begin_additional_deliveries(database):
    store, _, now = scheduled(database)
    stopped = [False]

    class StopAfterFirst(Channel):
        def send(self, title, message):
            super().send(title, message)
            stopped[0] = True

    channels = {"telegram": StopAfterFirst(), "windows": StopAfterFirst()}
    engine = ReminderEngine(store, channels, lambda: now, lambda: stopped[0])
    assert engine.tick() == 1
    assert sum(len(channel.calls) for channel in channels.values()) == 1
    assert sorted(item["state"] for item in store.list()[0]["deliveries"].values()) == [
        "pending",
        "sent",
    ]


def test_delete_is_permanent_removes_deliveries_and_skips_in_progress(database):
    store, reminder, now = scheduled(database)
    other = make_reminder("Lịch khác", 10, created_at=now - timedelta(seconds=10))
    store.save(other)
    claimed = store.claim(now)  # One channel of the first due reminder is sending.
    assert claimed is not None
    sending_id = claimed.reminder_id
    idle_id = other.id if sending_id == reminder.id else reminder.id
    assert store.delete([sending_id, idle_id]) == 1
    assert [item["id"] for item in store.list()] == [sending_id]
    with database.connect() as connection:
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM reminder_deliveries WHERE reminder_id=?",
                (idle_id,),
            ).fetchone()[0]
            == 0
        )
    store.finish(claimed, now)  # Finishing the kept send still works.
    assert store.delete([sending_id]) == 1
    assert store.list() == []
    channel = Channel()
    engine = ReminderEngine(
        store, {"telegram": channel, "windows": channel}, lambda: now
    )
    assert engine.tick() == 0 and channel.calls == []
