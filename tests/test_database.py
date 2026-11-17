"""Real SQLite files, including rollback and forward-version protection."""

import sqlite3

import pytest

from xaydungso.infrastructure.database import (
    APPLICATION_ID,
    Database,
    DatabaseVersionError,
    Migration,
)
from xaydungso.infrastructure.database import MIGRATIONS as ALL_MIGRATIONS

MIGRATIONS = ALL_MIGRATIONS[:1]


def test_baseline_is_idempotent_and_foreign_keys_are_enabled(tmp_path):
    database = Database(tmp_path / "nested" / "app.sqlite3", MIGRATIONS)
    database.initialize()
    database.initialize()
    with database.connect() as connection:
        assert (
            connection.execute("PRAGMA application_id").fetchone()[0] == APPLICATION_ID
        )
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("SELECT name FROM sqlite_master").fetchall() == []
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


def test_upgrade_preserves_data_and_constraints(tmp_path):
    # Synthetic schema used only to exercise the migration mechanism.
    migrations = MIGRATIONS + (
        Migration(
            2, ("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT NOT NULL)",)
        ),
        Migration(3, ("CREATE UNIQUE INDEX sample_value ON sample(value)",)),
    )
    database = Database(tmp_path / "app.sqlite3", migrations[:2])
    database.initialize()
    with database.connect() as connection, connection:
        connection.execute(
            "INSERT INTO sample(value) VALUES (?)", ("Unicode: tiếng Việt",)
        )
    Database(database.path, migrations).initialize()
    with database.connect() as connection:
        assert connection.execute("SELECT value FROM sample").fetchone()[0] == (
            "Unicode: tiếng Việt"
        )
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
        with pytest.raises(sqlite3.IntegrityError), connection:
            connection.execute("INSERT INTO sample(value) VALUES (NULL)")
        with pytest.raises(sqlite3.IntegrityError), connection:
            connection.execute(
                "INSERT INTO sample(value) VALUES (?)", ("Unicode: tiếng Việt",)
            )


def test_failed_migration_rolls_back_ddl_and_version(tmp_path):
    path = tmp_path / "app.sqlite3"
    Database(path, MIGRATIONS).initialize()
    invalid = MIGRATIONS + (
        Migration(2, ("CREATE TABLE sample (id INTEGER)", "INVALID SQL")),
    )
    with pytest.raises(sqlite3.OperationalError):
        Database(path, invalid).initialize()
    with Database(path).connect() as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        assert connection.execute("SELECT name FROM sqlite_master").fetchall() == []


@pytest.mark.parametrize("application_id, version", [(42, 0), (APPLICATION_ID, 99)])
def test_refuses_foreign_or_future_database(tmp_path, application_id, version):
    path = tmp_path / "app.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(f"PRAGMA application_id = {application_id}")
        connection.execute(f"PRAGMA user_version = {version}")
    before = path.read_bytes()
    with pytest.raises(DatabaseVersionError):
        Database(path).initialize()
    assert path.read_bytes() == before


def test_refuses_to_adopt_existing_unidentified_schema(tmp_path):
    path = tmp_path / "other.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE unrelated (value TEXT)")
    with pytest.raises(DatabaseVersionError):
        Database(path).initialize()


def test_transaction_rolls_back_on_failure(tmp_path):
    database = Database(
        tmp_path / "app.sqlite3",
        MIGRATIONS + (Migration(2, ("CREATE TABLE sample (value TEXT UNIQUE)",)),),
    )
    database.initialize()
    with database.connect() as connection:
        with pytest.raises(sqlite3.IntegrityError), connection:
            connection.execute("INSERT INTO sample VALUES ('test')")
            connection.execute("INSERT INTO sample VALUES ('test')")
        assert connection.execute("SELECT * FROM sample").fetchall() == []


def test_rejects_nonconsecutive_migrations(tmp_path):
    with pytest.raises(ValueError):
        Database(tmp_path / "app.sqlite3", (Migration(2, ()),))
    with pytest.raises(ValueError):
        Database(tmp_path / "app.sqlite3", ())
