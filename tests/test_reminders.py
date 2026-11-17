"""Approved boundaries, durations, timezone and late-creation exception."""

from datetime import datetime, timezone

import pytest

from xaydungso.domain.reminders import (
    local_time,
    make_reminder,
    notification_time,
    permitted,
)


@pytest.mark.parametrize(
    "deadline, expected",
    [
        ("2026-11-18T09:00:00", "2026-11-18T09:00:00"),
        ("2026-11-18T02:00:00", "2026-11-17T22:00:00"),
        ("2026-11-18T06:30:00", "2026-11-17T22:00:00"),
        ("2026-11-18T23:30:00", "2026-11-17T22:00:00"),
        ("2026-11-18T07:00:00", "2026-11-18T07:00:00"),
        ("2026-11-18T22:59:59.999999", "2026-11-18T22:59:59.999999"),
        ("2027-01-01T00:00:00", "2026-12-31T22:00:00"),
        ("2028-03-01T06:59:59", "2028-02-29T22:00:00"),
    ],
)
def test_adjustment(deadline, expected):
    assert notification_time(datetime.fromisoformat(deadline)) == local_time(
        datetime.fromisoformat(expected)
    )


@pytest.mark.parametrize("second", [0, 1, 59])
def test_23_boundary_is_inclusive_only_at_exact_endpoint(second):
    deadline = datetime(2026, 11, 18, 23, 0, second)
    expected = deadline if second == 0 else datetime(2026, 11, 17, 22)
    assert notification_time(deadline) == local_time(expected)


def test_timezone_conversion():
    assert notification_time(
        datetime(2026, 11, 18, 2, tzinfo=timezone.utc)
    ) == local_time(datetime(2026, 11, 18, 9))


def test_previous_day_overflow_is_reported():
    with pytest.raises(ValueError):
        notification_time(datetime.min)


@pytest.mark.parametrize("duration", [10, 3600, 43200, 86400])
def test_real_elapsed_duration(duration):
    created = datetime(2026, 11, 20, 9)
    reminder = make_reminder("Nhắc thử", duration, created_at=created)
    assert (reminder.deadline_at - reminder.start_at).total_seconds() == duration
    assert reminder.start_at == local_time(created)


def test_late_creation_and_past_adjusted_time():
    reminder = make_reminder(
        "Nhắc thử", 3600, created_at=datetime(2026, 11, 17, 23, 30)
    )
    assert reminder.deadline_at == local_time(datetime(2026, 11, 18, 0, 30))
    assert reminder.notify_at == local_time(datetime(2026, 11, 18, 7))


@pytest.mark.parametrize(
    "clock, allowed",
    [("07:00:00", True), ("23:00:00", True), ("23:00:01", False), ("06:59:59", False)],
)
def test_delivery_window(clock, allowed):
    assert permitted(datetime.fromisoformat("2026-11-18T" + clock)) is allowed


@pytest.mark.parametrize("duration", [0, -1, 0.5, True, 10**20])
def test_invalid_duration(duration):
    with pytest.raises(ValueError):
        make_reminder("Nhắc thử", duration)
