"""Template-preserving writer for explicitly rendered tracking snapshots.

This is an output adapter, not a record mapper: the application must supply
every A–N value and an explicitly ordered snapshot after its schema and display
policies are approved. No Excel values are ever imported into persistence.
"""

import logging
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from xml.dom import minidom
from xml.etree import ElementTree
from xml.parsers.expat import ExpatError
from zipfile import BadZipFile, ZipFile

from xaydungso.domain.records import RecordStatus

SHEET_PART = "xl/worksheets/sheet1.xml"
NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
COLUMNS = tuple("ABCDEFGHIJKLMN")
INVALID_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")
logger = logging.getLogger(__name__)


class ExcelExportError(RuntimeError):
    """Output was not replaced; callers may retry the entire snapshot."""


def _validate_rows(rows: Sequence[Mapping[str, str]]) -> None:
    if len(rows) > 1_048_572:
        raise ValueError("Snapshot exceeds the Excel worksheet row limit")
    for row in rows:
        if set(row) != set(COLUMNS):
            raise ValueError("Every row must explicitly map each column A–N")
        for value in row.values():
            if not isinstance(value, str):
                raise ValueError("Values must be explicitly rendered strings")
            if INVALID_XML.search(value) or len(value.encode("utf-16-le")) // 2 > 32767:
                raise ValueError("Value cannot be represented safely in an Excel cell")
        if row["M"] not in RecordStatus:
            raise ValueError("Unsupported record status")


def _cell_text(cell, shared_strings):
    kind = cell.getAttribute("t")
    if kind == "inlineStr":
        return "".join(
            node.firstChild.data if node.firstChild else ""
            for node in cell.getElementsByTagName("t")
        )
    values = cell.getElementsByTagName("v")
    text = values[0].firstChild.data if values and values[0].firstChild else ""
    return shared_strings[int(text)] if kind == "s" else text


def _worksheet(source, rows, *, policy="replace", shared_strings=(), removed_codes=()):
    """Update only the 14-column register; preserve workbook and sheet layout."""
    document = minidom.parseString(source)
    data_nodes = document.getElementsByTagName("sheetData")
    dimensions = document.getElementsByTagName("dimension")
    if len(data_nodes) != 1 or len(dimensions) != 1:
        raise ValueError("Workbook worksheet layout is not supported")
    data = data_nodes[0]
    original_rows = list(data.getElementsByTagName("row"))
    headers = [row for row in original_rows if int(row.getAttribute("r")) < 5]
    if [row.getAttribute("r") for row in headers] != ["1", "2", "3", "4"]:
        raise ValueError("Expected four register header rows")
    header_cells = {
        c.getAttribute("r"): c for row in headers for c in row.getElementsByTagName("c")
    }
    for reference, expected in (
        ("A2", "mã hồ sơ"),
        ("F3", "thời hạn xử lý"),
        ("M3", "trạng thái"),
        ("N2", "ghi chú"),
    ):
        if (
            reference not in header_cells
            or " ".join(
                _cell_text(header_cells[reference], shared_strings).split()
            ).casefold()
            != expected
        ):
            raise ValueError(
                "Workbook headers do not match the approved 14-column register"
            )
    body = [row for row in original_rows if int(row.getAttribute("r")) >= 5]
    # Refuse older layouts (e.g. with an STT column) rather than shifting user data.
    for row in original_rows:
        for cell in row.getElementsByTagName("c"):
            column = re.sub(r"\d", "", cell.getAttribute("r"))
            if len(column) != 1 or column > "N":
                raise ValueError("Expected the approved 14-column workbook")
    prototype = body[0].cloneNode(deep=True) if body else document.createElement("row")
    styles = {
        re.sub(r"\d", "", cell.getAttribute("r")): cell.getAttribute("s")
        for cell in prototype.getElementsByTagName("c")
        if cell.hasAttribute("s")
    }
    for column in document.getElementsByTagName("col"):
        if column.hasAttribute("style"):
            for number in range(
                int(column.getAttribute("min")),
                min(int(column.getAttribute("max")), 14) + 1,
            ):
                styles.setdefault(chr(64 + number), column.getAttribute("style"))

    def fill(row, values, number):
        row.setAttribute("r", str(number))
        row_styles = dict(styles)
        row_styles.update(
            {
                re.sub(r"\d", "", c.getAttribute("r")): c.getAttribute("s")
                for c in row.getElementsByTagName("c")
                if c.hasAttribute("s")
            }
        )
        while row.firstChild:
            row.removeChild(row.firstChild)
        for column in COLUMNS:
            cell = document.createElement("c")
            cell.setAttribute("r", f"{column}{number}")
            if column in row_styles:
                cell.setAttribute("s", row_styles[column])
            cell.setAttribute("t", "inlineStr")
            inline = document.createElement("is")
            text = document.createElement("t")
            text.setAttribute("xml:space", "preserve")
            text.appendChild(document.createTextNode(values[column]))
            inline.appendChild(text)
            cell.appendChild(inline)
            row.appendChild(cell)

    if policy == "replace":
        for row in body:
            data.removeChild(row)
        for number, values in enumerate(rows, 5):
            row = prototype.cloneNode(deep=True)
            fill(row, values, number)
            data.appendChild(row)
        if not rows:
            row = prototype.cloneNode(deep=True)
            while row.firstChild:
                row.removeChild(row.firstChild)
            row.setAttribute("r", "5")
            data.appendChild(row)
    elif policy == "merge":
        existing = {}
        for row in body:
            cells = {
                re.sub(r"\d", "", c.getAttribute("r")): c
                for c in row.getElementsByTagName("c")
            }
            code = _cell_text(cells["A"], shared_strings) if "A" in cells else ""
            if code:
                if code in existing:
                    raise ValueError("Duplicate record codes in workbook")
                existing[code] = row
        for code in removed_codes:
            if code in existing:
                data.removeChild(existing.pop(code))
        remaining = list(data.getElementsByTagName("row"))
        last_number = max(
            (
                int(r.getAttribute("r"))
                for r in remaining
                if r.getElementsByTagName("c")
            ),
            default=4,
        )
        for values in rows:
            row = existing.get(values["A"])
            if row is None:
                last_number += 1
                row = prototype.cloneNode(deep=True)
                fill(row, values, last_number)
                # Remove an empty placeholder at the same row number.
                for empty in list(data.getElementsByTagName("row")):
                    if empty.getAttribute("r") == str(
                        last_number
                    ) and not empty.getElementsByTagName("c"):
                        data.removeChild(empty)
                data.appendChild(row)
            else:
                fill(row, values, int(row.getAttribute("r")))
    else:
        raise ValueError("Select an Excel update policy")
    last = max(
        5, *(int(row.getAttribute("r")) for row in data.getElementsByTagName("row"))
    )
    if last > 1_048_576:
        raise ValueError("Worksheet row limit exceeded")
    dimension = dimensions[0].cloneNode(deep=True)
    dimension.setAttribute("ref", f"A1:N{last}")
    text = source.decode("utf-8")
    text, count = re.subn(
        r"<sheetData(?:\s[^>]*)?>.*?</sheetData>",
        lambda _: data.toxml(),
        text,
        flags=re.DOTALL,
    )
    text, dimension_count = re.subn(
        r"<dimension\b[^>]*/>", lambda _: dimension.toxml(), text
    )
    if count != 1 or dimension_count != 1:
        raise ValueError("Worksheet serialization is not supported")
    return text.encode("utf-8")


def export_tracking_snapshot(
    template: Path,
    destination: Path,
    ordered_rows: Sequence[Mapping[str, str]],
    *,
    existing=False,
    policy="replace",
    removed_codes=(),
) -> None:
    """Write caller-rendered A–N values in caller-selected deterministic order.

    The application snapshot mapper supplies the approved field rendering and
    creation order. All values are written as text; there is no STT column.
    """
    template, destination = Path(template), Path(destination)
    temporary: Path | None = None
    try:
        if not existing and (
            template.resolve() == destination.resolve()
            or (destination.exists() and os.path.samefile(template, destination))
        ):
            raise ValueError("Destination must not overwrite the template")
        if destination.is_symlink():
            raise ValueError("Destination must not be a symbolic link")
        # Freeze input so concurrent caller changes cannot alter the output mid-write.
        rows = tuple(dict(row) for row in ordered_rows)
        _validate_rows(rows)
        if existing and not destination.is_file():
            raise ValueError("Select an existing workbook")
        source_path = destination if existing else template
        before = source_path.stat()
        with ZipFile(source_path) as original:
            if len(original.namelist()) != len(set(original.namelist())):
                raise ValueError("Template contains duplicate archive members")
            if original.testzip() is not None:
                raise ValueError("Template archive failed integrity validation")
            workbook = ElementTree.fromstring(original.read("xl/workbook.xml"))
            sheets = workbook.findall(f"{{{NAMESPACE}}}sheets/{{{NAMESPACE}}}sheet")
            selected = [sheet for sheet in sheets if sheet.get("name") == "Sheet1"]
            if len(selected) != 1:
                raise ValueError("Expected the approved single Sheet1 workbook")
            relationships = ElementTree.fromstring(
                original.read("xl/_rels/workbook.xml.rels")
            )
            relationship_id = selected[0].get(
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            )
            targets = [
                item.get("Target")
                for item in relationships
                if item.get("Id") == relationship_id
            ]
            if targets not in (
                ["worksheets/sheet1.xml"],
                ["/xl/worksheets/sheet1.xml"],
            ):
                raise ValueError("Sheet1 relationship is not supported")
            shared = ()
            if "xl/sharedStrings.xml" in original.namelist():
                shared = tuple(
                    "".join(item.itertext())
                    for item in ElementTree.fromstring(
                        original.read("xl/sharedStrings.xml")
                    )
                )
            rendered = _worksheet(
                original.read(SHEET_PART),
                rows,
                policy=policy,
                shared_strings=shared,
                removed_codes=removed_codes,
            )
            descriptor, filename = tempfile.mkstemp(
                prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
            )
            temporary = Path(filename)
            with os.fdopen(descriptor, "w+b") as stream:
                with ZipFile(stream, "w") as output:
                    output.comment = original.comment
                    for entry in original.infolist():
                        output.writestr(
                            entry,
                            rendered
                            if entry.filename == SHEET_PART
                            else original.read(entry),
                        )
                stream.flush()
                os.fsync(stream.fileno())
        with ZipFile(temporary) as output:
            if output.testzip() is not None or output.read(SHEET_PART) != rendered:
                raise ValueError("Generated workbook failed integrity validation")
            ElementTree.fromstring(output.read(SHEET_PART))
        if existing:
            current = destination.stat()
            if (before.st_mtime_ns, before.st_size) != (
                current.st_mtime_ns,
                current.st_size,
            ):
                raise ValueError("Workbook changed while writing; retry")
        os.replace(temporary, destination)
    except (
        OSError,
        ValueError,
        KeyError,
        BadZipFile,
        ElementTree.ParseError,
        ExpatError,
        IndexError,
    ) as error:
        # No row values are included in exceptions or logs (may contain personal data).
        raise ExcelExportError(
            "Excel export failed; previous output is preserved"
        ) from error
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                logger.warning("Could not remove an Excel export temporary file")


def update_tracking_workbook(
    template, destination, ordered_rows, *, policy, removed_codes=()
):
    """Modify the selected existing workbook, never regenerate it from template."""
    export_tracking_snapshot(
        template,
        destination,
        ordered_rows,
        existing=True,
        policy=policy,
        removed_codes=removed_codes,
    )
