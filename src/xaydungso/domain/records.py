"""Approved CPXD record data and validation, independent of adapters."""

from dataclasses import dataclass
from enum import StrEnum


class RecordStatus(StrEnum):
    INCOMPLETE = "Chưa hoàn thành"
    COMPLETE = "Đã hoàn thành"


class ValidationError(ValueError):
    """A user-correctable input error."""


class DuplicateRecordCode(ValidationError):
    pass


class RecordNotFound(ValidationError):
    pass


def validate_duration(seconds: int) -> int:
    if (
        isinstance(seconds, bool)
        or not isinstance(seconds, int)
        or not 0 < seconds < 2**63
    ):
        raise ValidationError("Thời lượng phải là số giây nguyên dương hợp lệ.")
    return seconds


def format_duration(seconds: int | None) -> str:
    if seconds is None:
        return ""
    validate_duration(seconds)
    if seconds % 3600 == 0:
        return f"{seconds // 3600} giờ"
    if seconds % 60 == 0:
        return f"{seconds // 60} phút"
    return f"{seconds} giây"


@dataclass(frozen=True)
class RecordData:
    record_code: str
    applicant_name: str
    phone: str = ""
    address: str = ""
    received_at: str = ""
    processing_duration: int | None = None
    reminder_tracking_time: str = ""
    overall_processing_time: str = ""
    drawing_stamp_status: bool = False
    permit_stamp_status: bool = False
    handover_at: str = ""
    signature_status: bool = False
    recipient_name: str = ""
    status: RecordStatus = RecordStatus.INCOMPLETE
    notes: str = ""

    def __post_init__(self) -> None:
        for field in (
            "record_code",
            "applicant_name",
            "phone",
            "address",
            "received_at",
            "reminder_tracking_time",
            "overall_processing_time",
            "handover_at",
            "recipient_name",
            "notes",
        ):
            if not isinstance(getattr(self, field), str):
                raise ValidationError("Thông tin theo dõi phải là văn bản.")
        for field, label in (
            ("record_code", "Mã hồ sơ"),
            ("applicant_name", "Họ và tên"),
        ):
            value = getattr(self, field).strip()
            if not value:
                raise ValidationError(f"{label} không được để trống.")
            object.__setattr__(self, field, value)
        try:
            object.__setattr__(self, "status", RecordStatus(self.status))
        except ValueError as error:
            raise ValidationError("Trạng thái hồ sơ không hợp lệ.") from error
        for field in (
            "drawing_stamp_status",
            "permit_stamp_status",
            "signature_status",
        ):
            if not isinstance(getattr(self, field), bool):
                raise ValidationError("Giá trị đóng dấu/ký nhận không hợp lệ.")
        if self.processing_duration is not None:
            validate_duration(self.processing_duration)


@dataclass(frozen=True)
class Record:
    id: int
    created_at: str
    data: RecordData
