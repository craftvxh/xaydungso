"""Deadline-driven scheduling and atomic record/reminder updates."""

from dataclasses import replace
from datetime import datetime

import pytest

from xaydungso.application.reminders import Reminders
from xaydungso.domain.records import RecordData, ValidationError
from xaydungso.domain.reminders import local_time, make_deadline_reminder
from xaydungso.infrastructure.database import MIGRATIONS, Database
from xaydungso.infrastructure.records import SqliteRecords
from xaydungso.infrastructure.reminders import SqliteReminders


@pytest.mark.parametrize("lead", [10, 3600, 43200, 86400])
def test_notify_is_deadline_minus_lead(lead):
    reminder = make_deadline_reminder(
        "Test", datetime(2026, 11, 20, 20), lead, created_at=datetime(2026, 11, 17, 9)
    )
    assert reminder.deadline_at == local_time(datetime(2026, 11, 20, 20))
    assert (reminder.deadline_at - reminder.notify_at).total_seconds() == lead


def test_window_adjustment_uses_requested_notify_time():
    reminder = make_deadline_reminder(
        "Test", datetime(2026, 11, 20, 8), 7200, created_at=datetime(2026, 11, 17, 9)
    )
    assert reminder.notify_at == local_time(datetime(2026, 11, 19, 22))


@pytest.mark.parametrize(
    "values",
    [
        dict(deadline_at="not-a-date"),
        dict(deadline_at="2026-11-18T09:00:00"),
        dict(reminder_lead_seconds=3600),
    ],
)
def test_deadline_validation(values):
    with pytest.raises(ValidationError):
        RecordData("001", "Test", **values)


def test_record_changes_do_not_create_or_change_reminders(database):
    repo = SqliteRecords(database)
    store = SqliteReminders(database)
    record = repo.save(
        RecordData("001", "Test", deadline_at="2099-11-18T09:00:00+07:00")
    )
    assert store.list() == []
    reminder = Reminders(store).save(
        "Manual schedule",
        deadline_at=datetime(2099, 11, 18, 9),
        lead_seconds=3600,
        record_id=record.id,
    )
    original = store.list()[0]
    changed = repo.save(
        replace(record.data, deadline_at="2099-11-19T09:00:00+07:00", notes="Updated"),
        record.id,
    )
    assert store.list() == [original]
    Reminders(store).save(
        "Edited separately",
        deadline_at=datetime(2099, 11, 19, 9),
        lead_seconds=7200,
        record_id=record.id,
        reminder_id=reminder.id,
    )
    assert store.list()[0]["lead_seconds"] == 7200
    assert repo.get(record.id) == changed
    repo.delete(record.id)
    assert store.list()[0]["cancelled"] == 1


def test_v4_auto_schedules_become_editable_without_losing_delivery_history(tmp_path):
    from xaydungso.infrastructure.reminders import insert_reminder

    path = tmp_path / "v4.sqlite3"
    old = Database(path, MIGRATIONS[:4])
    old.initialize()
    reminder = make_deadline_reminder(
        "Existing schedule", datetime(2099, 11, 18, 9), 3600
    )
    with old.connect() as connection, connection:
        insert_reminder(connection, reminder, record_managed=True)
    upgraded = Database(path)
    upgraded.initialize()
    store = SqliteReminders(upgraded)
    assert store.list()[0]["record_managed"] == 0
    assert store.list()[0]["cancelled"] == 0
    store.save(
        make_deadline_reminder(
            "Edited", datetime(2099, 11, 18, 10), 3600, reminder_id=reminder.id
        ),
        editing=True,
    )
    assert store.list()[0]["title"] == "Edited"


def test_v3_upgrade_keeps_old_data_without_inventing_deadline(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    old = Database(path, MIGRATIONS[:3])
    old.initialize()
    with old.connect() as connection, connection:
        connection.execute(
            "INSERT INTO records(record_code,applicant_name,processing_duration,reminder_tracking_time,created_at) VALUES ('001','Legacy',3600,'manual text','2026-11-17T00:00:00+00:00')"
        )
    upgraded = Database(path)
    upgraded.initialize()
    record = SqliteRecords(upgraded).list()[0]
    assert record.data.processing_duration == 3600
    assert record.data.reminder_tracking_time == "manual text"
    assert record.data.deadline_at == ""
    assert record.data.reminder_lead_seconds is None
    assert SqliteReminders(upgraded).list() == []
