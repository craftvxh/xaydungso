"""SQLite record persistence; all statements use bound user parameters."""

import sqlite3
from dataclasses import asdict, fields
from datetime import UTC, datetime

from xaydungso.domain.records import (
    DuplicateRecordCode,
    Record,
    RecordData,
    RecordNotFound,
    RecordStatus,
)
from xaydungso.infrastructure.database import Database

FIELDS = tuple(field.name for field in fields(RecordData))


def _record(row: sqlite3.Row) -> Record:
    values = {name: row[name] for name in FIELDS}
    for name in ("drawing_stamp_status", "permit_stamp_status", "signature_status"):
        values[name] = bool(values[name])
    return Record(row["id"], row["created_at"], RecordData(**values))


class SqliteRecords:
    def __init__(self, database: Database):
        self.database = database

    def list(
        self, search: str = "", status: RecordStatus | None = None
    ) -> list[Record]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM records"
                + (" WHERE status = ?" if status else "")
                + " ORDER BY created_at ASC, id ASC",
                (status.value,) if status else (),
            ).fetchall()
        # Python casefold handles Vietnamese Unicode consistently across SQLite builds.
        needle = search.strip().casefold()
        records = [_record(row) for row in rows]
        return [
            record
            for record in records
            if not needle
            or any(
                needle in text.casefold()
                for text in (
                    record.data.record_code,
                    record.data.applicant_name,
                    record.data.phone,
                    record.data.address,
                    record.data.recipient_name,
                    record.data.notes,
                )
            )
        ]

    def get(self, record_id: int) -> Record:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM records WHERE id = ?", (record_id,)
            ).fetchone()
        if row is None:
            raise RecordNotFound("Hồ sơ không còn tồn tại. Hãy tải lại danh sách.")
        return _record(row)

    def save(self, data: RecordData, record_id: int | None = None) -> Record:
        values = asdict(data)
        try:
            with self.database.connect() as connection, connection:
                if record_id is None:
                    created = datetime.now(UTC).isoformat(timespec="microseconds")
                    cursor = connection.execute(
                        f"INSERT INTO records ({','.join(FIELDS)},created_at) "
                        f"VALUES ({','.join('?' for _ in FIELDS)},?)",
                        (*values.values(), created),
                    )
                    record_id = cursor.lastrowid
                else:
                    cursor = connection.execute(
                        f"UPDATE records SET {','.join(name + '=?' for name in FIELDS)} WHERE id=?",
                        (*values.values(), record_id),
                    )
                    if cursor.rowcount != 1:
                        raise RecordNotFound("Hồ sơ không còn tồn tại.")
        except sqlite3.IntegrityError as error:
            if "records.record_code" in str(error):
                raise DuplicateRecordCode(
                    "Mã hồ sơ đã tồn tại. Vui lòng chọn mã khác."
                ) from None
            raise
        return self.get(record_id)

    def delete(self, record_id: int) -> None:
        with self.database.connect() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "UPDATE reminders SET cancelled=1 WHERE record_id=? AND EXISTS "
                "(SELECT 1 FROM reminder_deliveries d WHERE d.reminder_id=reminders.id AND d.state!='sent')",
                (record_id,),
            )
            cursor = connection.execute("DELETE FROM records WHERE id=?", (record_id,))
            if cursor.rowcount != 1:
                raise RecordNotFound("Hồ sơ không còn tồn tại.")
