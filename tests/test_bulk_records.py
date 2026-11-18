"""Bulk delete / status change: one Excel write, committed work kept on failure."""

import pytest

from xaydungso.application.records import Records
from xaydungso.domain.records import RecordData, RecordNotFound, RecordStatus
from xaydungso.infrastructure.records import SqliteRecords


class CountingExporter:
    def __init__(self):
        self.calls = 0

    def export(self):
        self.calls += 1


@pytest.fixture
def service(database):
    return Records(SqliteRecords(database), CountingExporter())


def add(service, *codes):
    return [service.save(RecordData(code, "Tên")).record.id for code in codes]


def test_set_status_changes_only_selected_and_exports_once(service):
    first, second, third = add(service, "A", "B", "C")
    service.exporter.calls = 0
    result = service.set_status([first, third], RecordStatus.COMPLETE)
    assert result.export_error is None
    assert service.exporter.calls == 1
    statuses = {r.data.record_code: r.data.status for r in service.list()}
    assert statuses == {
        "A": RecordStatus.COMPLETE,
        "B": RecordStatus.INCOMPLETE,
        "C": RecordStatus.COMPLETE,
    }
    service.set_status([first], RecordStatus.INCOMPLETE)
    assert service.get(first).data.status is RecordStatus.INCOMPLETE
    assert service.get(second).data.status is RecordStatus.INCOMPLETE


def test_delete_many_is_permanent_and_exports_once(service):
    first, second, third = add(service, "A", "B", "C")
    service.exporter.calls = 0
    service.delete_many([first, third])
    assert service.exporter.calls == 1
    assert [r.data.record_code for r in service.list()] == ["B"]
    with pytest.raises(RecordNotFound):
        service.get(first)


def test_failure_keeps_committed_deletes_and_still_exports(service):
    (first,) = add(service, "A")
    service.exporter.calls = 0
    with pytest.raises(RecordNotFound):
        service.delete_many([first, 999_999])
    assert service.list() == []  # The committed delete is not rolled back.
    assert service.exporter.calls == 1  # Excel reflects what was committed.
