"""Approved A–N mapping and writes to the selected existing register."""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

from xaydungso.domain.records import RecordData
from xaydungso.domain.reminders import LOCAL_ZONE
from xaydungso.infrastructure.excel import update_tracking_workbook
from xaydungso.infrastructure.records import SqliteRecords


def tracking_row(data: RecordData) -> dict[str, str]:
    return {
        "A": data.record_code,
        "B": data.applicant_name,
        "C": data.phone,
        "D": data.address,
        "E": data.received_at,
        "F": datetime.fromisoformat(data.deadline_at)
        .astimezone(LOCAL_ZONE)
        .strftime("%d/%m/%Y %H:%M:%S")
        if data.deadline_at
        else "",
        "G": data.return_appointment_date,
        "H": "Có" if data.drawing_stamp_status else "Chưa",
        "I": "Có" if data.permit_stamp_status else "Chưa",
        "J": data.handover_at,
        "K": "Đã ký" if data.signature_status else "Chưa ký",
        "L": data.recipient_name,
        "M": data.status.value,
        "N": data.notes,
    }


class SqliteTrackingExporter:
    def __init__(
        self,
        repository: SqliteRecords,
        template: Path,
        destination: Path | None,
        policy: str = "merge",
    ):
        self.repository, self.template, self.destination = (
            repository,
            template,
            destination,
        )
        self.policy = policy

    def export(self) -> None:
        try:
            self._export()
        except sqlite3.Error:
            raise RuntimeError(
                "Không thể cập nhật liên kết dòng Excel; hãy thử ghi lại."
            ) from None

    def _export(self) -> None:
        if self.destination is None or not self.destination.is_file():
            raise RuntimeError("Chọn file Excel có sẵn trong Cài đặt.")
        if self.policy not in ("merge", "replace"):
            raise RuntimeError("Cách ghi Excel không hợp lệ.")
        # list() materializes one SELECT snapshot ordered by created_at, id.
        records = self.repository.list()
        rows = tuple(tracking_row(record.data) for record in records)
        path_key = os.path.normcase(str(self.destination.resolve()))
        database = self.repository.database
        with database.connect() as connection:
            previous = connection.execute(
                "SELECT record_id,record_code FROM excel_record_links WHERE workbook_path=?",
                (path_key,),
            ).fetchall()
        current_codes = {record.data.record_code for record in records}
        removed = {row["record_code"] for row in previous} - current_codes
        update_tracking_workbook(
            self.template,
            self.destination,
            rows,
            policy=self.policy,
            removed_codes=removed,
        )
        with database.connect() as connection, connection:
            connection.execute(
                "DELETE FROM excel_record_links WHERE workbook_path=?", (path_key,)
            )
            connection.executemany(
                "INSERT INTO excel_record_links(workbook_path,record_id,record_code) VALUES (?,?,?)",
                [(path_key, record.id, record.data.record_code) for record in records],
            )
