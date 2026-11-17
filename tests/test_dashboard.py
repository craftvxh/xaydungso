"""Read model semantics against real SQLite, independent of Excel and widgets."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from xaydungso.application.dashboard import Dashboard
from xaydungso.domain.records import RecordData, RecordStatus
from xaydungso.domain.reminders import local_time, make_reminder, timestamp
from xaydungso.infrastructure.dashboard import SqliteDashboard
from xaydungso.infrastructure.records import SqliteRecords
from xaydungso.infrastructure.reminders import SqliteReminders


def view(database, now):
    return Dashboard(SqliteDashboard(database), lambda: now).load()


def schedule(database, when, name, record_id=None):
    reminder = make_reminder(
        name,
        10,
        created_at=when - timedelta(seconds=10),
        record_id=record_id,
        reminder_id=name,
    )
    SqliteReminders(database).save(reminder)
    # Explicit query-boundary fixtures, including midnight; time calculation is
    # separately verified in reminder rules tests, not inferred by this adapter.
    with database.connect() as connection, connection:
        connection.execute(
            "UPDATE reminders SET notify_at=? WHERE id=?", (timestamp(when), name)
        )
    return reminder


def test_empty_database(database):
    snapshot = view(database, datetime(2026, 11, 18, 9))
    assert (
        snapshot.total_records,
        snapshot.incomplete_records,
        snapshot.completed_records,
        snapshot.todays_reminders,
    ) == (0, 0, 0, 0)
    assert snapshot.upcoming == ()


def test_record_counts_follow_status_changes_and_permanent_deletion(database):
    records = SqliteRecords(database)
    first = records.save(RecordData("001", "Mẫu"))
    second = records.save(RecordData("002", "Mẫu", status=RecordStatus.COMPLETE))
    now = datetime(2026, 11, 18, 9)
    assert view(database, now).total_records == 2
    assert view(database, now).incomplete_records == 1
    assert view(database, now).completed_records == 1
    records.save(replace(first.data, status=RecordStatus.COMPLETE), first.id)
    assert view(database, now).completed_records == 2
    records.delete(second.id)
    snapshot = view(database, now)
    assert (
        snapshot.total_records
        == snapshot.incomplete_records + snapshot.completed_records
        == 1
    )


def test_today_is_half_open_vietnam_day_not_utc_day(database):
    start = local_time(datetime(2026, 11, 18))
    schedule(database, start - timedelta(microseconds=1), "before")
    schedule(database, start, "start")
    schedule(database, start + timedelta(days=1, microseconds=-1), "last")
    schedule(database, start + timedelta(days=1), "end")
    # 17th in UTC, already 18th locally.
    snapshot = view(database, datetime(2026, 11, 17, 18, tzinfo=UTC))
    assert snapshot.as_of.date() == start.date()
    assert snapshot.todays_reminders == 2


def test_count_schedules_once_and_filter_upcoming(database):
    now = local_time(datetime(2026, 11, 18, 9))
    record = SqliteRecords(database).save(RecordData("HS-001", "Mẫu"))
    schedule(database, now, "at-now", record.id)
    schedule(database, now + timedelta(hours=1), "partial")
    schedule(database, now + timedelta(hours=2), "sent")
    schedule(database, now + timedelta(hours=3), "cancelled")
    schedule(database, now - timedelta(seconds=1), "overdue")
    schedule(database, now + timedelta(days=1), "tomorrow")
    with database.connect() as connection, connection:
        connection.execute("UPDATE reminders SET cancelled=1 WHERE id='cancelled'")
        connection.execute(
            "UPDATE reminder_deliveries SET state='sent' WHERE reminder_id='sent'"
        )
        connection.execute(
            "UPDATE reminder_deliveries SET state='sent' WHERE reminder_id='partial' AND channel='telegram'"
        )
    snapshot = view(database, now)
    assert (
        snapshot.todays_reminders == 4
    )  # Includes sent/overdue, excludes cancelled/tomorrow.
    assert [reminder.id for reminder in snapshot.upcoming] == [
        "at-now",
        "partial",
        "tomorrow",
    ]
    assert snapshot.upcoming[0].record_code == "HS-001"
    assert snapshot.upcoming[1].record_code is None


def test_upcoming_order_tie_break_and_limit(database):
    now = local_time(datetime(2026, 11, 18, 9))
    for index in reversed(range(12)):
        schedule(database, now + timedelta(hours=1), f"reminder-{index:02d}")
    snapshot = view(database, now)
    assert snapshot.todays_reminders == 12
    assert [item.id for item in snapshot.upcoming] == [
        f"reminder-{index:02d}" for index in range(10)
    ]


def test_deletion_cancels_linked_schedule_without_hiding_standalone(database):
    now = local_time(datetime(2026, 11, 18, 9))
    records = SqliteRecords(database)
    record = records.save(RecordData("001", "Mẫu"))
    schedule(database, now + timedelta(hours=1), "linked", record.id)
    schedule(database, now + timedelta(hours=1), "standalone")
    records.delete(record.id)
    snapshot = view(database, now)
    assert snapshot.todays_reminders == 1
    assert [item.id for item in snapshot.upcoming] == ["standalone"]
