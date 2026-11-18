"""Update an existing register while retaining unmanaged rows and workbook parts."""

from dataclasses import replace
from zipfile import ZipFile

import pytest
from test_excel import TEMPLATE, mapped_row, sheet, text_at

from xaydungso.domain.records import RecordData
from xaydungso.infrastructure import excel
from xaydungso.infrastructure.excel import (
    ExcelExportError,
    export_tracking_snapshot,
    update_tracking_workbook,
)
from xaydungso.infrastructure.records import SqliteRecords
from xaydungso.infrastructure.tracking_export import SqliteTrackingExporter


def test_merge_preserves_foreign_rows_and_deletes_only_previously_written_records(
    database, tmp_path
):
    destination = tmp_path / "Existing register.xlsx"
    export_tracking_snapshot(TEMPLATE, destination, (mapped_row("foreign"),))
    # A user-specific workbook part must survive; writer must read the chosen file.
    with ZipFile(destination, "a") as archive:
        archive.comment = b"User register"
        archive.writestr("customXml/user-data.xml", b"<data>Keep me</data>")
    repo = SqliteRecords(database)
    exporter = SqliteTrackingExporter(repo, TEMPLATE, destination, "merge")
    record = repo.save(
        RecordData(
            "app",
            "First",
            deadline_at="2099-11-18T09:00:00+07:00",
            reminder_lead_seconds=3600,
        )
    )
    exporter.export()
    assert text_at(sheet(destination), "A5") == "foreign"
    assert text_at(sheet(destination), "A6") == "app"
    assert text_at(sheet(destination), "F6") == "18/11/2099 09:00:00"
    repo.save(replace(record.data, applicant_name="Updated"), record.id)
    exporter.export()
    exporter.export()  # Retry must not append duplicate rows.
    assert text_at(sheet(destination), "B6") == "Updated"
    with ZipFile(destination) as archive:
        assert archive.comment == b"User register"
        assert archive.read("customXml/user-data.xml") == b"<data>Keep me</data>"
    repo.delete(record.id)
    exporter.export()
    root = sheet(destination)
    assert text_at(root, "A5") == "foreign"
    assert "app" not in "".join(root.itertext())


def test_replace_updates_same_file_and_missing_file_is_not_created(tmp_path):
    path = tmp_path / "register.xlsx"
    with pytest.raises(ExcelExportError):
        update_tracking_workbook(TEMPLATE, path, (mapped_row(),), policy="replace")
    assert not path.exists()
    export_tracking_snapshot(TEMPLATE, path, ())
    update_tracking_workbook(
        TEMPLATE, path, (mapped_row("first"), mapped_row("second")), policy="replace"
    )
    update_tracking_workbook(TEMPLATE, path, (mapped_row("only"),), policy="replace")
    assert text_at(sheet(path), "A5") == "only"
    assert "second" not in "".join(sheet(path).itertext())


def test_so_theo_doi_can_be_its_own_working_file(tmp_path):
    path = tmp_path / "so_theo_doi.xlsx"
    export_tracking_snapshot(TEMPLATE, path, ())
    update_tracking_workbook(path, path, (mapped_row("001"),), policy="merge")
    update_tracking_workbook(path, path, (mapped_row("002"),), policy="merge")
    assert text_at(sheet(path), "A5") == "001"
    assert text_at(sheet(path), "A6") == "002"


def test_existing_file_lock_preserves_workbook_and_binding_state(
    database, tmp_path, monkeypatch
):
    path = tmp_path / "register.xlsx"
    export_tracking_snapshot(TEMPLATE, path, ())
    repo = SqliteRecords(database)
    repo.save(RecordData("app", "Test"))
    exporter = SqliteTrackingExporter(repo, TEMPLATE, path, "merge")
    before = path.read_bytes()

    def fail(*args):
        raise PermissionError("locked")

    with monkeypatch.context() as patch:
        patch.setattr(excel.os, "replace", fail)
        with pytest.raises(ExcelExportError):
            exporter.export()
    assert path.read_bytes() == before
    with database.connect() as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM excel_record_links").fetchone()[0]
            == 0
        )
    exporter.export()
    assert text_at(sheet(path), "A5") == "app"


def test_default_writer_preserves_existing_register_rows(database, tmp_path):
    path = tmp_path / "register.xlsx"
    export_tracking_snapshot(TEMPLATE, path, (mapped_row("foreign"),))
    SqliteTrackingExporter(SqliteRecords(database), TEMPLATE, path).export()
    assert text_at(sheet(path), "A5") == "foreign"


def test_duplicate_codes_and_old_layout_are_rejected_without_writing(tmp_path):
    path = tmp_path / "register.xlsx"
    export_tracking_snapshot(
        TEMPLATE, path, (mapped_row("duplicate"), mapped_row("duplicate"))
    )
    before = path.read_bytes()
    with pytest.raises(ExcelExportError):
        update_tracking_workbook(TEMPLATE, path, (mapped_row("new"),), policy="merge")
    assert path.read_bytes() == before
    with ZipFile(path) as archive:
        parts = [(entry, archive.read(entry)) for entry in archive.infolist()]
    with ZipFile(path, "w") as archive:
        for entry, content in parts:
            if entry.filename == excel.SHEET_PART:
                content = content.replace(
                    b"</row>",
                    b'<c r="O4" t="inlineStr"><is><t>Old column</t></is></c></row>',
                    1,
                )
            archive.writestr(entry, content)
    before = path.read_bytes()
    with pytest.raises(ExcelExportError):
        update_tracking_workbook(TEMPLATE, path, (mapped_row("new"),), policy="replace")
    assert path.read_bytes() == before
