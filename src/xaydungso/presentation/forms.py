"""Fluent input widgets with validation delegated to the domain."""

from datetime import datetime

from PyQt6.QtCore import QDateTime, pyqtSignal
from PyQt6.QtWidgets import (
    QDateTimeEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    ComboBox,
    FluentStyleSheet,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SubtitleLabel,
    TextEdit,
)

from xaydungso.domain.records import RecordData, RecordStatus, ValidationError
from xaydungso.domain.reminders import LOCAL_ZONE


class DurationInput(QWidget):
    def __init__(self, seconds=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.presets = ComboBox(self)
        self.presets.addItems(
            ["Tự nhập (giây)", "10 giây (test)", "1 giờ", "12 giờ", "24 giờ"]
        )
        self.seconds = LineEdit(self)
        self.seconds.setPlaceholderText("Số giây; có thể để trống")
        self.seconds.setText("" if seconds is None else str(seconds))
        self.presets.currentIndexChanged.connect(self._preset)
        layout.addWidget(self.presets)
        layout.addWidget(self.seconds, 1)

    def _preset(self, index):
        value = (None, 10, 3600, 43200, 86400)[index]
        if value is not None:
            self.seconds.setText(str(value))

    def value(self, required=False):
        text = self.seconds.text().strip()
        if not text and not required:
            return None
        try:
            value = int(text)
        except ValueError:
            raise ValidationError("Thời lượng phải là số giây nguyên dương.") from None
        if value <= 0:
            raise ValidationError("Thời lượng phải lớn hơn 0.")
        return value


class EditorDialog(QDialog):
    submitted = pyqtSignal(object)

    def __init__(self, title, parent=None):
        super().__init__(parent)
        FluentStyleSheet.DIALOG.apply(self)
        self.setWindowTitle(title)
        self.resize(720, 720)
        self.saving = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.addWidget(SubtitleLabel(title, self))
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        content = QWidget(scroll)
        self.form = QFormLayout(content)
        self.form.setSpacing(12)
        scroll.setWidget(content)
        scroll.enableTransparentBackground()
        outer.addWidget(scroll, 1)
        self.error = BodyLabel(self)
        self.error.setWordWrap(True)
        outer.addWidget(self.error)
        buttons = QHBoxLayout()
        self.cancel_button = PushButton("Đóng", self)
        self.save_button = PrimaryPushButton("Lưu", self)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self._submit)
        buttons.addStretch()
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.save_button)
        outer.addLayout(buttons)

    def _submit(self):
        try:
            value = self.value()
        except ValidationError as error:
            self.error.setText(str(error))
            return
        self.set_saving(True)
        self.submitted.emit(value)

    def set_saving(self, saving):
        self.saving = saving
        self.save_button.setEnabled(not saving)
        self.cancel_button.setEnabled(not saving)

    def reject(self):
        if not self.saving:
            super().reject()

    def closeEvent(self, event):
        if self.saving:
            event.ignore()
        else:
            super().closeEvent(event)


class RecordDialog(EditorDialog):
    def __init__(self, record=None, parent=None):
        super().__init__(
            "Thêm hồ sơ" if record is None else "Chi tiết / sửa hồ sơ", parent
        )
        data = record.data if record else RecordData("Mới", "Mới")
        self.inputs = {}
        for field, label in (
            ("record_code", "Mã hồ sơ *"),
            ("applicant_name", "Họ và tên *"),
            ("phone", "Số điện thoại"),
            ("address", "Địa chỉ"),
            ("received_at", "Thời gian nhận"),
            ("reminder_tracking_time", "Thời gian nhắc (theo dõi)"),
            ("overall_processing_time", "Thời hạn toàn quy trình (theo dõi)"),
            ("handover_at", "Thời gian giao nhận"),
            ("recipient_name", "Người ký nhận"),
        ):
            edit = LineEdit(self)
            edit.setText(getattr(data, field) if record else "")
            if field in (
                "received_at",
                "reminder_tracking_time",
                "overall_processing_time",
                "handover_at",
            ):
                edit.setPlaceholderText(
                    "Nhập thông tin theo dõi; giữ nguyên nội dung khi xuất"
                )
            self.inputs[field] = edit
            self.form.addRow(label, edit)
        self.duration = DurationInput(data.processing_duration, self)
        self.form.addRow("Thời hạn xử lý", self.duration)
        for field, label in (
            ("drawing_stamp_status", "Bản vẽ đã đóng dấu"),
            ("permit_stamp_status", "Giấy phép đã đóng dấu"),
            ("signature_status", "Đã ký nhận"),
        ):
            checkbox = CheckBox(label, self)
            checkbox.setChecked(getattr(data, field))
            self.inputs[field] = checkbox
            self.form.addRow("", checkbox)
        self.status = ComboBox(self)
        self.status.addItems([status.value for status in RecordStatus])
        self.status.setCurrentText(data.status.value)
        self.form.addRow("Trạng thái", self.status)
        self.notes = TextEdit(self)
        self.notes.setMinimumHeight(90)
        self.notes.setPlainText(data.notes)
        self.form.addRow("Ghi chú", self.notes)
        self.form.addRow(
            BodyLabel(
                "* Bắt buộc. Hoàn thành do bạn chủ động chọn; không tự chuyển trạng thái.",
                self,
            )
        )

    def value(self):
        values = {
            field: widget.isChecked() if isinstance(widget, CheckBox) else widget.text()
            for field, widget in self.inputs.items()
        }
        return RecordData(
            **values,
            processing_duration=self.duration.value(),
            status=self.status.currentText(),
            notes=self.notes.toPlainText(),
        )


class ReminderDialog(EditorDialog):
    def __init__(self, records, reminder=None, record=None, parent=None):
        super().__init__("Sửa lịch nhắc" if reminder else "Tạo lịch nhắc", parent)
        self.resize(720, 500)
        self.title = LineEdit(self)
        self.title.setText(
            reminder["title"]
            if reminder
            else (
                f"Hồ sơ {record.data.record_code} — {record.data.applicant_name}"
                if record
                else ""
            )
        )
        self.form.addRow("Nội dung nhắc *", self.title)
        self.link = ComboBox(self)
        self.link.addItem("Không liên kết hồ sơ", userData=None)
        for item in records:
            self.link.addItem(
                f"{item.data.record_code} — {item.data.applicant_name}",
                userData=item.id,
            )
        record_id = (
            reminder["record_id"] if reminder else (record.id if record else None)
        )
        self.link.setCurrentIndex(max(0, self.link.findData(record_id)))
        self.form.addRow("Hồ sơ", self.link)
        self.start = QDateTimeEdit(self)
        self.start.setCalendarPopup(True)
        self.start.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        initial = (
            datetime.fromisoformat(reminder["start_at"]).astimezone(LOCAL_ZONE)
            if reminder
            else datetime.now(LOCAL_ZONE)
        )
        self.start.setDateTime(
            QDateTime.fromString(
                initial.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd HH:mm:ss"
            )
        )
        self.start_changed = reminder is not None
        self.start.dateTimeChanged.connect(
            lambda _: setattr(self, "start_changed", True)
        )
        self.form.addRow("Bắt đầu (giờ Việt Nam)", self.start)
        seconds = (
            reminder["duration"]
            if reminder
            else (record.data.processing_duration if record else None)
        )
        self.duration = DurationInput(seconds or 3600, self)
        self.form.addRow("Thời lượng *", self.duration)
        help_text = BodyLabel(
            "Gửi qua Telegram và Windows Notification. 10 giây chỉ để thử.\n"
            "Ngoài 07:00–23:00, giờ gửi được điều chỉnh theo quy tắc.\n"
            "Cột thời gian nhắc theo dõi của hồ sơ không tự thay đổi.",
            self,
        )
        help_text.setWordWrap(True)
        self.form.addRow(help_text)

    def value(self):
        if not self.title.text().strip():
            raise ValidationError("Nội dung nhắc không được để trống.")
        return dict(
            title=self.title.text(),
            duration=self.duration.value(True),
            start_at=self.start.dateTime().toPyDateTime().replace(tzinfo=None)
            if self.start_changed
            else None,
            record_id=self.link.currentData(),
        )
