"""Template-preserving writer for explicitly rendered tracking snapshots.

This is an output adapter, not a record mapper: the application must supply
every B–P value and an explicitly ordered snapshot after its schema and display
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
COLUMNS = tuple("BCDEFGHIJKLMNOP")
INVALID_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")
logger = logging.getLogger(__name__)


class ExcelExportError(RuntimeError):
    """Output was not replaced; callers may retry the entire snapshot."""


def _validate_rows(rows: Sequence[Mapping[str, str]]) -> None:
    if len(rows) > 1_048_572:
        raise ValueError("Snapshot exceeds the Excel worksheet row limit")
    for row in rows:
        if set(row) != set(COLUMNS):
            raise ValueError("Every row must explicitly map each column B–P")
        for value in row.values():
            if not isinstance(value, str):
                raise ValueError("Values must be explicitly rendered strings")
            if INVALID_XML.search(value) or len(value.encode("utf-16-le")) // 2 > 32767:
                raise ValueError("Value cannot be represented safely in an Excel cell")
        if row["O"] not in RecordStatus:
            raise ValueError("Unsupported record status")


def _worksheet(source: bytes, rows: Sequence[Mapping[str, str]]) -> bytes:
    """Change only sheetData and dimension; preserve all other XML verbatim."""
    document = minidom.parseString(source)
    data_nodes = document.getElementsByTagName("sheetData")
    dimensions = document.getElementsByTagName("dimension")
    if len(data_nodes) != 1 or len(dimensions) != 1:
        raise ValueError("Template worksheet layout is not supported")
    data = data_nodes[0]
    original_rows = list(data.getElementsByTagName("row"))
    if [row.getAttribute("r") for row in original_rows] != ["1", "2", "3", "4", "5"]:
        raise ValueError("Expected four header rows and one empty data row")
    prototype = original_rows[-1]
    if any(
        cell.getElementsByTagName(tag)
        for cell in prototype.getElementsByTagName("c")
        for tag in ("v", "f", "is")
    ):
        raise ValueError("Template data region must be empty")
    styles = {
        re.sub(r"\d", "", cell.getAttribute("r")): cell.getAttribute("s")
        for cell in prototype.getElementsByTagName("c")
        if cell.hasAttribute("s")
    }
    for column in document.getElementsByTagName("col"):
        if column.hasAttribute("style"):
            for number in range(
                int(column.getAttribute("min")),
                min(int(column.getAttribute("max")), 16) + 1,
            ):
                styles.setdefault(chr(64 + number), column.getAttribute("style"))
    data.removeChild(prototype)
    for index, values in enumerate(rows, 5):
        row = prototype.cloneNode(deep=True)
        row.setAttribute("r", str(index))
        while row.firstChild:
            row.removeChild(row.firstChild)
        for column in "ABCDEFGHIJKLMNOP":
            cell = document.createElement("c")
            cell.setAttribute("r", f"{column}{index}")
            if column in styles:
                cell.setAttribute("s", styles[column])
            if column == "A":
                value = document.createElement("v")
                value.appendChild(document.createTextNode(str(index - 4)))
                cell.appendChild(value)
            else:
                # inlineStr preserves phone/code leading zeroes and treats '=' as text.
                cell.setAttribute("t", "inlineStr")
                inline = document.createElement("is")
                text = document.createElement("t")
                text.setAttribute("xml:space", "preserve")
                text.appendChild(document.createTextNode(values[column]))
                inline.appendChild(text)
                cell.appendChild(inline)
            row.appendChild(cell)
        data.appendChild(row)
    if not rows:
        data.appendChild(prototype)
    dimension = dimensions[0].cloneNode(deep=True)
    dimension.setAttribute("ref", f"A1:P{max(5, len(rows) + 4)}")
    # Preserve original headers, namespace declarations, relationships, and print setup.
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
        raise ValueError("Template worksheet serialization is not supported")
    return text.encode("utf-8")


def export_tracking_snapshot(
    template: Path, destination: Path, ordered_rows: Sequence[Mapping[str, str]]
) -> None:
    """Write caller-rendered B–P values in caller-selected deterministic order.

    The application snapshot mapper supplies the approved field rendering and
    creation order. All values are text except generated numeric STT in column A.
    """
    template, destination = Path(template), Path(destination)
    temporary: Path | None = None
    try:
        if template.resolve() == destination.resolve() or (
            destination.exists() and os.path.samefile(template, destination)
        ):
            raise ValueError("Destination must not overwrite the template")
        if destination.is_symlink():
            raise ValueError("Destination must not be a symbolic link")
        # Freeze input so concurrent caller changes cannot alter the output mid-write.
        rows = tuple(dict(row) for row in ordered_rows)
        _validate_rows(rows)
        with ZipFile(template) as original:
            if len(original.namelist()) != len(set(original.namelist())):
                raise ValueError("Template contains duplicate archive members")
            if original.testzip() is not None:
                raise ValueError("Template archive failed integrity validation")
            workbook = ElementTree.fromstring(original.read("xl/workbook.xml"))
            sheets = workbook.findall(f"{{{NAMESPACE}}}sheets/{{{NAMESPACE}}}sheet")
            if len(sheets) != 1 or sheets[0].get("name") != "Sheet1":
                raise ValueError("Expected the approved single Sheet1 workbook")
            relationships = ElementTree.fromstring(
                original.read("xl/_rels/workbook.xml.rels")
            )
            relationship_id = sheets[0].get(
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
            rendered = _worksheet(original.read(SHEET_PART), rows)
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
        os.replace(temporary, destination)
    except (
        OSError,
        ValueError,
        KeyError,
        BadZipFile,
        ElementTree.ParseError,
        ExpatError,
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
