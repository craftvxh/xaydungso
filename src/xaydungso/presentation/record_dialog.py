"""Add / edit record dialog laid out like the approved Stitch design."""

from datetime import UTC, datetime, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CheckBox,
    LineEdit,
    RadioButton,
    TextEdit,
)

from xaydungso.domain.records import RecordData, RecordStatus
from xaydungso.domain.reminders import LOCAL_ZONE
from xaydungso.presentation.card_dialog import CardDialog
from xaydungso.presentation.forms import TIME_FORMAT, parse_time, time_text
from xaydungso.presentation.icons import Icon, colored_icon
from xaydungso.presentation.record_widgets import compact_checkbox
from xaydungso.presentation.theme import COLORS, set_mono

TIME_PLACEHOLDER = "dd/mm/yyyy hh:mm"
# Manually typed date fields: new or changed values must use TIME_FORMAT;
# older free text is kept as-is while it is not edited.
TIMED_FIELDS = (
    ("received_at", "Ngày tiếp nhận"),
    ("return_appointment_date", "Ngày hẹn trả kết quả"),
    ("handover_at", "Thời gian giao nhận"),
)

SHEET = """
QLabel[role="section"] { font-size: @fs_tiny; font-weight: 700; }
QFrame[role="sectionBar"] { background: @primary; border: none; }
QFrame[role="rule"] { background: @outline_soft; border: none; max-height: 1px; }
QLabel[role="field"] { font-size: @fs_body; font-weight: 600; }
QLabel[role="required"] { color: @error; font-size: @fs_small; }
QLabel[role="formatHint"] { background: @surface_container; color: @muted;
    border-radius: 6px; padding: 3px 8px; font-size: @fs_tiny; }
QPushButton[role="choice"] { background: @surface; border: 1px solid @outline;
    border-radius: 6px; text-align: left; }
QPushButton[role="choice"]:hover { background: @surface_faint; }
QPushButton[role="choice"]:checked { background: @surface_container;
    border: 2px solid @primary; }
QLabel[role="choiceTitle"] { font-size: @fs_body; font-weight: 600; }
QLabel[role="choiceHint"] { color: @muted; font-size: @fs_small; }
"""


class ChoiceCard(QPushButton):
    """Bordered option with a radio/check mark, a title and a hint line."""

    def __init__(self, title, hint, radio, parent=None):
        super().__init__(parent)
        self.setProperty("role", "choice")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(46)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(4)
        self.mark = RadioButton(self) if radio else compact_checkbox(CheckBox(self))
        self.mark.setFixedWidth(26)
        texts = QVBoxLayout()
        texts.setSpacing(0)
        self.title = QLabel(title, self)
        self.title.setProperty("role", "choiceTitle")
        hint_label = QLabel(hint, self)
        hint_label.setProperty("role", "choiceHint")
        texts.addWidget(self.title)
        texts.addWidget(hint_label)
        for widget in (self.mark, self.title, hint_label):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.mark)
        layout.addLayout(texts, 1)
        self.toggled.connect(self.mark.setChecked)


class StatusChoice(QWidget):
    """Two exclusive status cards with a ComboBox-like text API."""

    HINTS = {
        RecordStatus.INCOMPLETE: "Đang thẩm tra",
        RecordStatus.COMPLETE: "Cấp phép đạt",
    }

    def __init__(self, status, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.group = QButtonGroup(self)
        self.cards = {}
        for item in RecordStatus:
            card = ChoiceCard(item.value, self.HINTS[item], True, self)
            self.group.addButton(card)
            layout.addWidget(card)
            self.cards[item.value] = card
        self.setCurrentText(status.value)

    def currentText(self):
        return next(text for text, card in self.cards.items() if card.isChecked())

    def setCurrentText(self, text):
        self.cards[text].setChecked(True)


class RecordDialog(CardDialog):
    def __init__(self, record=None, parent=None):
        super().__init__(
            "Thêm hồ sơ mới"
            if record is None
            else f"Sửa hồ sơ {record.data.record_code}",
            Icon.ADD if record is None else Icon.EDIT,
            save_text="Lưu hồ sơ",
            cancel_text="Hủy thao tác",
            size=(900, 780),
            sheet=SHEET,
            parent=parent,
        )
        self.body.setContentsMargins(28, 20, 28, 20)
        self.body.setSpacing(14)
        data = record.data if record else RecordData("Mới", "Mới")
        self.original_data = data
        self.inputs = {}

        # 1. Applicant & location.
        required = QLabel("* Trường bắt buộc điền")
        required.setProperty("role", "required")
        grid = self._section("1. THÔNG TIN NGƯỜI NỘP & ĐỊA ĐIỂM", required, 2)
        self._text(grid, 0, 0, "record_code", "Mã hồ sơ", "VD: HS-2026-001", True)
        self._text(
            grid,
            0,
            1,
            "applicant_name",
            "Họ và tên người nộp / Chủ đầu tư",
            "Nhập họ và tên...",
            True,
        )
        self._text(
            grid, 1, 0, "phone", "Số điện thoại", "Nhập số điện thoại liên hệ..."
        )
        self._text(
            grid,
            1,
            1,
            "address",
            "Địa chỉ xây dựng công trình",
            "Số nhà, tên đường, phường/xã, quận/huyện...",
        )
        set_mono(self.inputs["record_code"])

        # 2. Process & dates.
        hint = QLabel("ⓘ  Định dạng bắt buộc: dd/MM/yyyy HH:mm")
        hint.setProperty("role", "formatHint")
        grid = self._section("2. QUY TRÌNH & THỜI GIAN XỬ LÝ", hint, 3)
        self._text(grid, 0, 0, "received_at", "Ngày tiếp nhận", TIME_PLACEHOLDER)
        self.original_deadline = (
            datetime.fromisoformat(data.deadline_at)
            .astimezone(LOCAL_ZONE)
            .strftime(TIME_FORMAT)
            if data.deadline_at
            else ""
        )
        self.deadline = self._edit(TIME_PLACEHOLDER + " (để trống nếu chưa có)")
        self._place(grid, 0, 1, "Hạn xử lý", self.deadline)
        self._text(
            grid,
            0,
            2,
            "return_appointment_date",
            "Ngày hẹn trả kết quả",
            TIME_PLACEHOLDER,
        )
        for field, icon_kind in (
            ("received_at", Icon.HISTORY),
            ("return_appointment_date", Icon.CALENDAR),
        ):
            self._lead_icon(self.inputs[field], icon_kind)
        self._lead_icon(self.deadline, Icon.CALENDAR)
        for field in ("record_code", "applicant_name", "phone", "address"):
            self.inputs[field].setText(getattr(data, field) if record else "")
        for field, _ in TIMED_FIELDS:
            if field in self.inputs:
                self.inputs[field].setText(getattr(data, field) if record else "")
        if record is None:
            # New records start with the current Vietnam time; users may edit or clear it.
            self.inputs["received_at"].setText(time_text())
        self.deadline.setText(
            self.original_deadline if record else time_text(timedelta(days=1))
        )

        # 3. Review status & results.
        grid = self._section("3. TÌNH TRẠNG THẨM ĐỊNH & KẾT QUẢ", None, 2)
        self.status = StatusChoice(data.status)
        self._place(grid, 0, 0, "Trạng thái xử lý", self.status)
        stamps = QWidget()
        stamp_row = QHBoxLayout(stamps)
        stamp_row.setContentsMargins(0, 0, 0, 0)
        stamp_row.setSpacing(8)
        for field, label in (
            ("drawing_stamp_status", "Bản vẽ kỹ thuật"),
            ("permit_stamp_status", "Giấy phép XD"),
        ):
            choice = ChoiceCard(label, "Đã đóng dấu", False, stamps)
            choice.setChecked(getattr(data, field))
            self.inputs[field] = choice
            stamp_row.addWidget(choice)
        self._place(grid, 0, 1, "Tình trạng đóng dấu giấy tờ", stamps)

        handover = QWidget()
        handover_row = QGridLayout(handover)
        handover_row.setContentsMargins(0, 0, 0, 0)
        handover_row.setHorizontalSpacing(16)
        handover_row.setVerticalSpacing(6)
        self._text(
            handover_row, 0, 0, "handover_at", "Thời gian giao nhận", TIME_PLACEHOLDER
        )
        self._lead_icon(self.inputs["handover_at"], Icon.HISTORY)
        self.inputs["handover_at"].setText(data.handover_at if record else time_text())
        self._text(
            handover_row,
            0,
            1,
            "recipient_name",
            "Người ký nhận",
            "Họ và tên người ký nhận...",
        )
        self.inputs["recipient_name"].setText(data.recipient_name if record else "")
        signature = ChoiceCard("Chữ ký", "Đã ký nhận", False, handover)
        signature.setChecked(data.signature_status)
        self.inputs["signature_status"] = signature
        self._place(handover_row, 0, 2, "Ký nhận", signature)
        for column in range(3):
            handover_row.setColumnStretch(column, 1)
        grid.addWidget(handover, 2, 0, 1, 2)

        notes_label = QLabel("Ghi chú")
        notes_label.setProperty("role", "field")
        self.notes = TextEdit()
        self.notes.setPlaceholderText("Ghi chú")
        self.notes.setMinimumHeight(64)
        self.notes.setMaximumHeight(96)
        self.notes.setPlainText(data.notes)
        grid.addWidget(notes_label, 3, 0, 1, 2)
        grid.addWidget(self.notes, 4, 0, 1, 2)
        self.body.addStretch()

    # Layout helpers -----------------------------------------------------------------

    def _section(self, title, right, columns):
        head = QHBoxLayout()
        head.setSpacing(10)
        bar = QFrame()
        bar.setProperty("role", "sectionBar")
        bar.setFixedSize(4, 16)
        label = QLabel(title)
        label.setProperty("role", "section")
        head.addWidget(bar)
        head.addWidget(label)
        head.addStretch()
        if right is not None:
            head.addWidget(right)
        rule = QFrame()
        rule.setProperty("role", "rule")
        rule.setFixedHeight(1)
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(6)
        for column in range(columns):
            grid.setColumnStretch(column, 1)
        self.body.addSpacing(4)
        self.body.addLayout(head)
        self.body.addWidget(rule)
        self.body.addLayout(grid)
        return grid

    def _edit(self, placeholder):
        edit = LineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setToolTip(placeholder)
        edit.setMinimumHeight(36)
        return edit

    def _place(self, grid, row, column, label, widget, required=False):
        caption = QLabel(
            label
            + (f" <span style='color:{COLORS['error']}'>*</span>" if required else "")
        )
        caption.setProperty("role", "field")
        grid.addWidget(caption, row * 2, column)
        grid.addWidget(widget, row * 2 + 1, column)
        grid.setRowMinimumHeight(row * 2 + 1, 40)

    def _text(self, grid, row, column, field, label, placeholder, required=False):
        edit = self._edit(placeholder)
        self.inputs[field] = edit
        self._place(grid, row, column, label, edit, required)

    @staticmethod
    def _lead_icon(edit, icon):
        # Fluent's LineEdit overrides addAction; use Qt's leading-icon overload.
        QLineEdit.addAction(
            edit,
            colored_icon(icon, COLORS["muted"]),
            QLineEdit.ActionPosition.LeadingPosition,
        )

    # Value -------------------------------------------------------------------------

    def value(self):
        values = {
            field: widget.isChecked()
            if isinstance(widget, ChoiceCard)
            else widget.text()
            for field, widget in self.inputs.items()
        }
        for field, label in TIMED_FIELDS:
            text = values[field].strip()
            # Older free-text values are kept as-is unless the user changes them.
            if text and text != getattr(self.original_data, field).strip():
                values[field] = parse_time(text, label).strftime(TIME_FORMAT)
            else:
                values[field] = text
        deadline_text = self.deadline.text().strip()
        if not deadline_text:
            deadline_at = ""
        elif deadline_text == self.original_deadline:
            deadline_at = self.original_data.deadline_at  # Keep stored seconds.
        else:
            deadline_at = (
                parse_time(deadline_text, "Hạn xử lý").astimezone(UTC).isoformat()
            )
        return RecordData(
            **values,
            processing_duration=self.original_data.processing_duration,
            reminder_tracking_time=self.original_data.reminder_tracking_time,
            deadline_at=deadline_at,
            reminder_lead_seconds=None,
            status=self.status.currentText(),
            notes=self.notes.toPlainText(),
        )
