"""Boundaries needed by the record use cases."""

from typing import Protocol

from xaydungso.domain.records import Record, RecordData, RecordStatus


class RecordRepository(Protocol):
    def list(
        self, search: str = "", status: RecordStatus | None = None
    ) -> list[Record]: ...
    def get(self, record_id: int) -> Record: ...
    def save(self, data: RecordData, record_id: int | None = None) -> Record: ...
    def delete(self, record_id: int) -> None: ...


class TrackingExporter(Protocol):
    def export(self) -> None: ...
