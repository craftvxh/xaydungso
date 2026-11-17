from pathlib import Path

import pytest

from xaydungso.infrastructure.database import Database


@pytest.fixture
def database(tmp_path):
    database = Database(tmp_path / "xaydungso.sqlite3")
    database.initialize()
    return database


@pytest.fixture
def template():
    return (
        Path(__file__).resolve().parents[1]
        / "docs/modules/excel/templates/so_theo_doi.xlsx"
    )
