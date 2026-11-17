"""Real supplied workbook; these tests do not approve unresolved mappings."""

from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

import pytest

from xaydungso.domain.records import RecordStatus
from xaydungso.infrastructure import excel
from xaydungso.infrastructure.excel import ExcelExportError, export_tracking_snapshot

TEMPLATE = (
    Path(__file__).resolve().parents[1]
    / "docs/modules/excel/templates/so_theo_doi.xlsx"
)
NS = {"s": excel.NAMESPACE}


def mapped_row(code="0001"):
    # Rendered fixture, not a CPXD model or an approved display policy.
    row = dict.fromkeys(excel.COLUMNS, "")
    row.update(
        B=code,
        C="Nguyễn Văn Mẫu",
        D="0123456789",
        E="Địa chỉ mẫu",
        N="Người nhận mẫu",
        O=RecordStatus.INCOMPLETE.value,
        P="=1+1 <ghi chú> & mẫu",
    )
    return row


def sheet(path):
    with ZipFile(path) as archive:
        return ElementTree.fromstring(archive.read(excel.SHEET_PART))


def text_at(root, reference):
    cell = root.find(f".//s:c[@r='{reference}']", NS)
    assert cell is not None
    return "".join(cell.itertext())


def test_snapshot_preserves_template_parts_layout_and_text(tmp_path):
    before = TEMPLATE.read_bytes()
    destination = tmp_path / "output.xlsx"
    export_tracking_snapshot(
        TEMPLATE, destination, (mapped_row("002"), mapped_row("001"))
    )
    assert TEMPLATE.read_bytes() == before
    with ZipFile(TEMPLATE) as source, ZipFile(destination) as output:
        assert source.namelist() == output.namelist()
        for name in source.namelist():
            if name != excel.SHEET_PART:
                assert source.read(name) == output.read(name)
    original, rendered = sheet(TEMPLATE), sheet(destination)
    for tag in ("mergeCells", "cols", "pageSetup", "pageMargins", "sheetViews"):
        assert ElementTree.tostring(
            original.find(f"s:{tag}", NS)
        ) == ElementTree.tostring(rendered.find(f"s:{tag}", NS))
    for index in range(1, 5):
        assert ElementTree.tostring(
            original.find(f"s:sheetData/s:row[@r='{index}']", NS)
        ) == (
            ElementTree.tostring(rendered.find(f"s:sheetData/s:row[@r='{index}']", NS))
        )
    assert text_at(rendered, "A5") == "1"
    assert text_at(rendered, "A6") == "2"
    assert text_at(rendered, "B5") == "002"  # Caller order is explicit, not guessed.
    assert text_at(rendered, "B6") == "001"
    assert text_at(rendered, "C5") == "Nguyễn Văn Mẫu"
    assert text_at(rendered, "D5") == "0123456789"
    assert text_at(rendered, "P5") == "=1+1 <ghi chú> & mẫu"
    assert rendered.findall(".//s:f", NS) == []
    assert rendered.find(".//s:c[@r='D5']", NS).get("t") == "inlineStr"
    assert rendered.find(".//s:row[@r='6']", NS).get("ht") == "22.5"
    assert rendered.find(".//s:c[@r='B6']", NS).get("s") == "1"


def test_regeneration_reflects_updates_and_removes_old_rows(tmp_path):
    destination = tmp_path / "output.xlsx"
    export_tracking_snapshot(
        TEMPLATE, destination, tuple(mapped_row(str(i)) for i in range(25))
    )
    changed = mapped_row("updated")
    changed["O"] = RecordStatus.COMPLETE.value
    export_tracking_snapshot(TEMPLATE, destination, (changed,))
    root = sheet(destination)
    assert text_at(root, "B5") == "updated"
    assert text_at(root, "O5") == "Đã hoàn thành"
    assert root.find(".//s:row[@r='6']", NS) is None
    export_tracking_snapshot(TEMPLATE, destination, ())
    root = sheet(destination)
    assert len(root.findall("s:sheetData/s:row", NS)) == 5
    assert root.findall("s:sheetData/s:row[@r='5']/s:c", NS) == []


def test_locked_output_is_preserved_and_full_retry_succeeds(tmp_path, monkeypatch):
    destination = tmp_path / "output.xlsx"
    export_tracking_snapshot(TEMPLATE, destination, (mapped_row("old"),))
    before = destination.read_bytes()

    def locked(*args):
        raise PermissionError("Simulated locked output")

    with monkeypatch.context() as patch:
        patch.setattr(excel.os, "replace", locked)
        with pytest.raises(ExcelExportError):
            export_tracking_snapshot(TEMPLATE, destination, (mapped_row("new"),))
    assert destination.read_bytes() == before
    assert list(tmp_path.iterdir()) == [destination]
    export_tracking_snapshot(TEMPLATE, destination, (mapped_row("new"),))
    assert text_at(sheet(destination), "B5") == "new"


def test_corrupt_generated_file_never_replaces_output(tmp_path, monkeypatch):
    destination = tmp_path / "output.xlsx"
    destination.write_bytes(b"previous output")
    monkeypatch.setattr(excel, "_worksheet", lambda *args: b"invalid XML")
    with pytest.raises(ExcelExportError):
        export_tracking_snapshot(TEMPLATE, destination, (mapped_row(),))
    assert destination.read_bytes() == b"previous output"
    assert list(tmp_path.iterdir()) == [destination]


@pytest.mark.parametrize("alias", ["same", "hardlink", "symlink"])
def test_refuses_template_aliases(tmp_path, alias):
    template = tmp_path / "template.xlsx"
    template.write_bytes(TEMPLATE.read_bytes())
    destination = tmp_path / "alias.xlsx"
    if alias == "hardlink":
        destination.hardlink_to(template)
    elif alias == "symlink":
        try:
            destination.symlink_to(template)
        except OSError:
            pytest.skip("Symlinks are unavailable on this platform")
    else:
        destination = template
    before = template.read_bytes()
    with pytest.raises(ExcelExportError):
        export_tracking_snapshot(template, destination, (mapped_row(),))
    assert template.read_bytes() == before


@pytest.mark.parametrize(
    "invalid", ["missing", "status", "type", "control", "oversize"]
)
def test_invalid_input_preserves_output(tmp_path, invalid):
    row = mapped_row()
    if invalid == "missing":
        del row["H"]
    elif invalid == "status":
        row["O"] = "Unapproved status"
    elif invalid == "type":
        row["F"] = 42
    elif invalid == "control":
        row["C"] = "Invalid\x00text"
    else:
        row["P"] = "x" * 32768
    destination = tmp_path / "output.xlsx"
    destination.write_bytes(b"previous output")
    with pytest.raises(ExcelExportError):
        export_tracking_snapshot(TEMPLATE, destination, (row,))
    assert destination.read_bytes() == b"previous output"


def test_missing_template_is_reported_without_substitution(tmp_path):
    destination = tmp_path / "output.xlsx"
    with pytest.raises(ExcelExportError):
        export_tracking_snapshot(
            TEMPLATE.with_name("missing_template.xlsx"), destination, (mapped_row(),)
        )
    assert not destination.exists()
