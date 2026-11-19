"""Shared locations for GUI and GUI-independent reminder worker (Windows)."""

import os
import sys
from pathlib import Path


def data_directory() -> Path:
    override = os.environ.get("XAYDUNGSO_DATA_DIR")
    if override:
        return Path(override).expanduser()
    return Path(os.environ["LOCALAPPDATA"]) / "xaydungso"


def template_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "templates/so_theo_doi.xlsx"
    return (
        Path(__file__).resolve().parents[3]
        / "docs/modules/excel/templates/so_theo_doi.xlsx"
    )
