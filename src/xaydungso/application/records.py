"""CRUD followed by a separately retryable export of committed records."""

from dataclasses import dataclass

from xaydungso.application.ports import RecordRepository, TrackingExporter
from xaydungso.domain.records import Record, RecordData, RecordStatus


@dataclass(frozen=True)
class SaveResult:
    record: Record | None
    export_error: str | None = None


class Records:
    def __init__(self, repository: RecordRepository, exporter: TrackingExporter):
        self.repository = repository
        self.exporter = exporter

    def list(
        self, search: str = "", status: RecordStatus | None = None
    ) -> list[Record]:
        return self.repository.list(search, status)

    def get(self, record_id: int) -> Record:
        return self.repository.get(record_id)

    def save(self, data: RecordData, record_id: int | None = None) -> SaveResult:
        record = self.repository.save(data, record_id)
        return SaveResult(record, self._export())

    def delete(self, record_id: int) -> SaveResult:
        self.repository.delete(record_id)
        return SaveResult(None, self._export())

    def export(self) -> str | None:
        return self._export()

    def _export(self) -> str | None:
        try:
            self.exporter.export()
        except (OSError, RuntimeError, ValueError):
            return "Excel chưa cập nhật. Dữ liệu SQLite vẫn được giữ. Hãy đóng file Excel và chọn Xuất lại Excel."
        return None
