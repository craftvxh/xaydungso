"""Shared locations for GUI and GUI-independent reminder worker."""

import os
import sys
from pathlib import Path


def data_directory() -> Path:
    override = os.environ.get("XAYDUNGSO_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        return Path(os.environ["LOCALAPPDATA"]) / "xaydungso"
    return (
        Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        / "xaydungso"
    )


def template_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "templates/so_theo_doi.xlsx"
    return (
        Path(__file__).resolve().parents[3]
        / "docs/modules/excel/templates/so_theo_doi.xlsx"
    )
