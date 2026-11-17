"""Record validation, real migrations, CRUD and committed-snapshot export."""

import sqlite3
from dataclasses import replace
from xml.etree import ElementTree
from zipfile import ZipFile

import pytest

from xaydungso.application.records import Records
from xaydungso.domain.records import (
    DuplicateRecordCode,
    RecordData,
    RecordNotFound,
    RecordStatus,
    ValidationError,
)
from xaydungso.infrastructure import excel
from xaydungso.infrastructure.database import MIGRATIONS, Database
from xaydungso.infrastructure.records import SqliteRecords
from xaydungso.infrastructure.tracking_export import (
    SqliteTrackingExporter,
    tracking_row,
)


def test_upgrades_existing_foundation_database(tmp_path):
    path = tmp_path / "old.sqlite3"
    Database(path, MIGRATIONS[:1]).initialize()
    database = Database(path)
    database.initialize()
    database.initialize()
    with database.connect() as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert {"records", "reminders", "reminder_deliveries"} <= tables


@pytest.mark.parametrize(
    "values",
    [
        dict(record_code=" ", applicant_name="A"),
        dict(record_code="A", applicant_name=""),
        dict(record_code="A", applicant_name="A", status="Other"),
        dict(record_code="A", applicant_name="A", processing_duration=0),
    ],
)
def test_validation(values):
    with pytest.raises(ValidationError):
        RecordData(**values)


def test_crud_search_filter_and_uniqueness(database):
    repository = SqliteRecords(database)
    first = repository.save(
        RecordData(
            " 001 ", " Nguyễn Văn Mẫu ", phone="0123456789", received_at="18/11/2026"
        )
    )
    second = repository.save(RecordData("002", "Tên thứ hai", address="Đường Mẫu"))
    assert first.data.record_code == "001"
    assert first.data.phone == "0123456789"
    assert first.data.status is RecordStatus.INCOMPLETE
    with pytest.raises(DuplicateRecordCode):
        repository.save(RecordData("001", "Trùng"))
    with pytest.raises(DuplicateRecordCode):
        repository.save(replace(second.data, record_code="001"), second.id)
    assert repository.get(second.id) == second
    changed = repository.save(
        replace(first.data, status=RecordStatus.COMPLETE, drawing_stamp_status=True),
        first.id,
    )
    assert changed.created_at == first.created_at
    assert repository.list("NGUYỄN") == [changed]
    assert repository.list("0123", RecordStatus.COMPLETE) == [changed]
    assert repository.list("ĐƯỜNG") == [second]
    assert repository.list("%") == []  # Literal search, not SQL wildcard syntax.
    assert repository.list(status=RecordStatus.INCOMPLETE) == [second]
    repository.delete(first.id)
    assert repository.list() == [second]
    with pytest.raises(RecordNotFound):
        repository.get(first.id)
    with pytest.raises(RecordNotFound):
        repository.save(first.data, first.id)
    with pytest.raises(RecordNotFound):
        repository.delete(first.id)


def test_stamp_and_signature_do_not_automatically_complete(database):
    record = SqliteRecords(database).save(
        RecordData(
            "001",
            "Mẫu",
            drawing_stamp_status=True,
            permit_stamp_status=True,
            signature_status=True,
        )
    )
    assert record.data.status is RecordStatus.INCOMPLETE


@pytest.mark.parametrize(
    "column,value",
    [
        ("record_code", ""),
        ("applicant_name", " "),
        ("status", "Other"),
        ("drawing_stamp_status", 3),
        ("processing_duration", -2),
    ],
)
def test_sqlite_constraints(database, column, value):
    repository = SqliteRecords(database)
    record = repository.save(RecordData("001", "Mẫu"))
    with database.connect() as connection:
        with pytest.raises(sqlite3.IntegrityError), connection:
            connection.execute(
                f"UPDATE records SET {column}=? WHERE id=?", (value, record.id)
            )
    assert repository.get(record.id) == record


def test_mapping_all_columns_and_manual_tracking():
    data = RecordData(
        "001",
        "Nguyễn Mẫu",
        phone="0123456789",
        address="Địa chỉ",
        received_at="18/11/2026 08:00",
        processing_duration=43200,
        reminder_tracking_time="Nhập tay H",
        overall_processing_time="15 ngày theo dõi",
        drawing_stamp_status=True,
        permit_stamp_status=False,
        handover_at="19/11/2026",
        signature_status=True,
        recipient_name="Người nhận",
        status=RecordStatus.COMPLETE,
        notes="Ghi chú",
    )
    assert tracking_row(data) == dict(
        zip(
            "BCDEFGHIJKLMNOP",
            (
                "001",
                "Nguyễn Mẫu",
                "0123456789",
                "Địa chỉ",
                "18/11/2026 08:00",
                "12 giờ",
                "Nhập tay H",
                "15 ngày theo dõi",
                "Có",
                "Chưa",
                "19/11/2026",
                "Đã ký",
                "Người nhận",
                "Đã hoàn thành",
                "Ghi chú",
            ),
            strict=True,
        )
    )


def test_crud_export_and_failure_do_not_rollback_commit(
    database, template, tmp_path, monkeypatch
):
    repository = SqliteRecords(database)
    output = tmp_path / "so_theo_doi.xlsx"
    service = Records(repository, SqliteTrackingExporter(repository, template, output))
    before = template.read_bytes()
    assert service.export() is None  # Empty database.
    first = service.save(RecordData("B", "Tên mẫu", phone="0123456789"))
    assert first.export_error is None
    old_output = output.read_bytes()

    def locked(*args):
        raise PermissionError("Simulated Excel lock")

    with monkeypatch.context() as patch:
        patch.setattr(excel.os, "replace", locked)
        second = service.save(RecordData("A", "Tên mới"))
    assert second.export_error is not None
    assert len(repository.list()) == 2
    assert output.read_bytes() == old_output
    assert service.export() is None
    with ZipFile(output) as archive:
        root = ElementTree.fromstring(archive.read(excel.SHEET_PART))
    ns = {"s": excel.NAMESPACE}
    assert "".join(root.find(".//s:c[@r='B5']", ns).itertext()) == "B"
    assert "".join(root.find(".//s:c[@r='B6']", ns).itertext()) == "A"
    assert (
        service.save(
            replace(first.record.data, notes="Đã sửa"), first.record.id
        ).export_error
        is None
    )
    assert service.delete(second.record.id).export_error is None
    with ZipFile(output) as archive:
        root = ElementTree.fromstring(archive.read(excel.SHEET_PART))
    assert root.find(".//s:row[@r='6']", ns) is None
    assert "".join(root.find(".//s:c[@r='P5']", ns).itertext()) == "Đã sửa"
    assert template.read_bytes() == before
