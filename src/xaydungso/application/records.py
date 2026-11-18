"""CRUD followed by a separately retryable export of committed records."""

from dataclasses import dataclass, replace

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

    def delete_many(self, record_ids) -> SaveResult:
        """Permanently delete several records, then update Excel once."""
        return self._each(record_ids, self.repository.delete)

    def set_status(self, record_ids, status: RecordStatus) -> SaveResult:
        """Change the status of several records, then update Excel once."""

        def change(record_id):
            data = self.repository.get(record_id).data
            if data.status is not status:
                self.repository.save(replace(data, status=status), record_id)

        return self._each(record_ids, change)

    def _each(self, record_ids, action) -> SaveResult:
        # Each record commits on its own; Excel still reflects whatever committed
        # before a failure, and the error is re-raised for the caller to report.
        try:
            for record_id in tuple(record_ids):
                action(record_id)
        except Exception:
            self._export()
            raise
        return SaveResult(None, self._export())

    def export(self) -> str | None:
        return self._export()

    def _export(self) -> str | None:
        try:
            self.exporter.export()
        except (OSError, RuntimeError, ValueError):
            return "Hồ sơ đã lưu, nhưng Excel chưa cập nhật. Kiểm tra File Excel làm việc trong Cài đặt, đóng file nếu đang mở; Excel sẽ được ghi lại ở lần lưu/sửa/xóa hồ sơ tiếp theo."
        return None
