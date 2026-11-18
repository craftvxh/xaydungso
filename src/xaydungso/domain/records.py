"""Approved CPXD record data and validation, independent of adapters."""

from dataclasses import dataclass
from datetime import UTC, datetime
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
    return_appointment_date: str = ""
    drawing_stamp_status: bool = False
    permit_stamp_status: bool = False
    handover_at: str = ""
    signature_status: bool = False
    recipient_name: str = ""
    status: RecordStatus = RecordStatus.INCOMPLETE
    notes: str = ""
    deadline_at: str = ""
    reminder_lead_seconds: int | None = None

    def __post_init__(self) -> None:
        for field in (
            "record_code",
            "applicant_name",
            "phone",
            "address",
            "received_at",
            "reminder_tracking_time",
            "return_appointment_date",
            "handover_at",
            "recipient_name",
            "notes",
            "deadline_at",
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
        if self.deadline_at:
            try:
                deadline = datetime.fromisoformat(self.deadline_at)
                if deadline.tzinfo is None:
                    raise ValueError("Timezone required")
                object.__setattr__(
                    self, "deadline_at", deadline.astimezone(UTC).isoformat()
                )
            except (TypeError, ValueError):
                raise ValidationError(
                    "Thời hạn xử lý phải là ngày/giờ hợp lệ."
                ) from None
        if self.reminder_lead_seconds is not None:
            validate_duration(self.reminder_lead_seconds)
            if not self.deadline_at:
                raise ValidationError("Cần có deadline để đặt khoảng nhắc trước hạn.")


@dataclass(frozen=True)
class Record:
    id: int
    created_at: str
    data: RecordData
