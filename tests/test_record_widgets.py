"""Display rules for the records page deadline column and detail pane."""

from datetime import datetime

from xaydungso.domain.records import RecordData, RecordStatus
from xaydungso.domain.reminders import LOCAL_ZONE
from xaydungso.presentation.record_widgets import deadline_info

NOW = datetime(2026, 11, 18, 10, 0, tzinfo=LOCAL_ZONE)


def data(deadline_at, status=RecordStatus.INCOMPLETE):
    return RecordData("001", "Tên", deadline_at=deadline_at, status=status)


def test_deadline_hint_counts_calendar_days_in_vietnam_time():
    # 20/11/2026 14:30 Vietnam time.
    assert deadline_info(data("2026-11-20T07:30:00+00:00"), NOW) == (
        "20/11/2026 14:30",
        "Còn 02 ngày",
        False,
    )
    assert deadline_info(data("2026-11-18T09:00:00+00:00"), NOW)[1] == "Hôm nay"


def test_past_deadline_is_overdue_only_while_incomplete():
    past = "2026-11-17T02:00:00+00:00"  # 17/11/2026 09:00
    assert deadline_info(data(past), NOW) == (
        "17/11/2026 09:00",
        "Quá hạn 01 ngày",
        True,
    )
    earlier_today = "2026-11-18T01:00:00+00:00"
    assert deadline_info(data(earlier_today), NOW)[1:] == ("Quá hạn", True)
    assert deadline_info(data(past, RecordStatus.COMPLETE), NOW) == (
        "17/11/2026 09:00",
        "",
        False,
    )


def test_missing_deadline_has_no_hint():
    assert deadline_info(data(""), NOW) == ("", "", False)
