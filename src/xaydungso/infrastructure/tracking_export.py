"""Explicit approved A–P mapping from a committed SQLite snapshot."""

from pathlib import Path

from xaydungso.application.ports import RecordRepository
from xaydungso.domain.records import RecordData, format_duration
from xaydungso.infrastructure.excel import export_tracking_snapshot


def tracking_row(data: RecordData) -> dict[str, str]:
    return {
        "B": data.record_code,
        "C": data.applicant_name,
        "D": data.phone,
        "E": data.address,
        "F": data.received_at,
        "G": format_duration(data.processing_duration),
        "H": data.reminder_tracking_time,
        "I": data.overall_processing_time,
        "J": "Có" if data.drawing_stamp_status else "Chưa",
        "K": "Có" if data.permit_stamp_status else "Chưa",
        "L": data.handover_at,
        "M": "Đã ký" if data.signature_status else "Chưa ký",
        "N": data.recipient_name,
        "O": data.status.value,
        "P": data.notes,
    }


class SqliteTrackingExporter:
    def __init__(self, repository: RecordRepository, template: Path, destination: Path):
        self.repository, self.template, self.destination = (
            repository,
            template,
            destination,
        )

    def export(self) -> None:
        # list() materializes one SELECT snapshot ordered by created_at, id.
        rows = tuple(tracking_row(record.data) for record in self.repository.list())
        export_tracking_snapshot(self.template, self.destination, rows)
