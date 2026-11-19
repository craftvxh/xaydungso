"""Create / edit reminder dialog laid out like the Stitch "Tạo lịch nhắc" design."""

from datetime import UTC, datetime, timedelta

from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import CheckBox, ComboBox, PlainTextEdit

from xaydungso.domain.records import ValidationError, format_duration
from xaydungso.domain.reminders import LOCAL_ZONE, make_deadline_reminder
from xaydungso.domain.templates import Template, render
from xaydungso.presentation.card_dialog import CardDialog
from xaydungso.presentation.forms import DurationInput, deadline_input
from xaydungso.presentation.icons import Icon
from xaydungso.presentation.record_widgets import compact_checkbox, icon_label
from xaydungso.presentation.theme import COLORS

# Used when no saved templates are passed in (e.g. tests, missing store).
FALLBACK = (Template(None, "Mặc định", "Hồ sơ {{ma_ho_so}} — {{ho_ten}}", True),)
CUSTOM_LABEL = "Tự nhập nội dung"


class MessageEdit(PlainTextEdit):
    """Multi-line reminder text with the LineEdit-style text()/setText() API."""

    def text(self):
        return self.toPlainText()

    def setText(self, text):
        self.setPlainText(text)


SHEET = """
QLabel[role="letter"] { background: @surface_container; color: @primary;
    border-radius: 11px; font-size: @fs_tiny; font-weight: 700; }
QLabel[role="section"] { font-size: @fs_tiny; font-weight: 700; }
QFrame[role="rule"] { background: @outline_soft; border: none; }
QLabel[role="field"] { font-size: @fs_body; font-weight: 600; }
QLabel[role="hint"] { color: @muted; font-size: @fs_small; }
QFrame#notifyBox { background: #e6e9ff; border: 1px solid #d3d8fb; border-radius: 8px; }
QLabel#notifyIcon { background: @primary_container; border-radius: 18px; }
QLabel#notifyCaption { font-size: @fs_tiny; font-weight: 700; color: @primary; }
QLabel#notifyTime { background: @surface; border-radius: 6px; padding: 3px 10px;
    font-size: @fs_heading; font-weight: 700; }
QLabel#notifyChip { border-radius: 4px; padding: 2px 8px; font-size: @fs_tiny;
    font-weight: 600; background: #dbeafe; color: #1d4ed8; }
QLabel#notifyChip[valid="false"] { background: #fee2e2; color: #b91c1c; }
QLabel#notifyExplain { color: @muted; font-size: @fs_small; }
QFrame#messageBox { background: @surface_low; border: 1px solid @outline_soft;
    border-radius: 8px; }
QFrame#messageCard { background: @surface; border: 1px solid @outline_soft;
    border-radius: 6px; }
QLabel#messageHeading { font-size: @fs_body; font-weight: 700; }
QLabel#messageDue { color: @error; font-family: @mono; font-size: @fs_mono;
    font-weight: 700; }
QLabel[role="channel"] { background: #dbeafe; color: #1d4ed8; border-radius: 8px;
    padding: 3px 10px; font-size: @fs_tiny; font-weight: 600; }
QDateTimeEdit { background: @surface_low; border: 1px solid @outline_soft;
    border-radius: 6px; padding: 6px 10px; font-size: @fs_mono; color: @text; }
QDateTimeEdit:focus { border-color: @primary; }
QDateTimeEdit::drop-down { border: none; background: transparent; width: 24px; }
"""


class ReminderDialog(CardDialog):
    def __init__(self, records, reminder=None, record=None, parent=None, templates=()):
        super().__init__(
            "Sửa lịch nhắc" if reminder else "Tạo lịch nhắc",
            Icon.RINGER,
            subtitle="Nhắc trước hạn xử lý, gửi qua Telegram và thông báo Windows",
            save_text="Lưu lịch nhắc",
            size=(700, 800),
            sheet=SHEET,
            parent=parent,
        )
        self.records_by_id = {item.id: item for item in records}
        self.templates = list(templates) or list(FALLBACK)
        self.applied = None  # Text last filled from a template.

        # A. Reminder information.
        grid = self._section("A", "THÔNG TIN LỊCH NHẮC")
        self.link = ComboBox()
        self.link.addItem("Không liên kết hồ sơ (lịch độc lập)", userData=None)
        for item in records:
            self.link.addItem(
                f"{item.data.record_code}  —  {item.data.applicant_name}",
                userData=item.id,
            )
        record_id = (
            reminder["record_id"] if reminder else (record.id if record else None)
        )
        self.link.setCurrentIndex(max(0, self.link.findData(record_id)))
        self._place(grid, 0, 0, "Hồ sơ liên quan", self.link, span=2)
        initial = (
            reminder["deadline_at"]
            if reminder
            else (record.data.deadline_at if record else "")
        )
        self.deadline = deadline_input(None, initial)
        self.deadline.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.deadline.setMinimumHeight(34)
        self._place(
            grid,
            2,
            0,
            "Hạn xử lý *",
            self.deadline,
            hint="Gợi ý từ hạn xử lý của hồ sơ; có thể sửa",
        )
        seconds = reminder.get("lead_seconds") if reminder else None
        self.duration = DurationInput(seconds or 86400)
        self._place(
            grid,
            2,
            1,
            "Khoảng thời gian nhắc *",
            self.duration,
            hint="Thời điểm gửi = hạn xử lý trừ khoảng này",
        )
        self._notify_box()

        # B. Message content.
        grid = self._section("B", "NỘI DUNG THÔNG BÁO")
        self.template = ComboBox()
        self.template.addItems(
            [
                item.name + ("  (Mặc định)" if item.is_default else "")
                for item in self.templates
            ]
            + [CUSTOM_LABEL]
        )
        self._place(
            grid,
            0,
            0,
            "Chọn mẫu thông báo sẵn có",
            self.template,
            span=2,
            hint="Quản lý mẫu ở Nhắc nhở → Cấu hình",
        )
        self.title = MessageEdit()
        self.title.setMinimumHeight(96)
        self.title.setMaximumHeight(140)
        self.title.setPlaceholderText("Nội dung sẽ gửi trong thông báo (nhiều dòng)")
        self._place(grid, 3, 0, "Nội dung nhắc *", self.title, span=2)

        # C. Message preview.
        self._section("C", "XEM TRƯỚC THÔNG BÁO")
        self._message_box()
        self.enable_background = compact_checkbox(
            CheckBox("Bật nhắc nền sau khi lưu lịch")
        )
        self.enable_background.setChecked(True)
        self.body.addWidget(self.enable_background)
        self.body.addStretch()

        info = QHBoxLayout()
        info.setSpacing(6)
        info.addWidget(icon_label(Icon.INFO, 14, None, COLORS["muted"]))
        note = QLabel("Gửi theo mốc đã tính khi nhắc nền đang bật, trong 07:00–23:00")
        note.setProperty("role", "hint")
        info.addWidget(note, 1)
        self.footer_left.insertLayout(0, info)

        # Initial text: an existing reminder keeps its own content.
        if reminder:
            self.template.setCurrentIndex(len(self.templates))  # Custom text.
            self.title.setText(reminder["title"])
        else:
            default = next(
                (i for i, item in enumerate(self.templates) if item.is_default), 0
            )
            self.template.setCurrentIndex(default)
            self._apply_template()
            self.link.currentIndexChanged.connect(self.record_changed)
        self.template.currentIndexChanged.connect(lambda _: self._apply_template())
        self.deadline.dateTimeChanged.connect(self.update_preview)
        self.deadline.dateTimeChanged.connect(self._deadline_changed)
        self.duration.seconds.textChanged.connect(self.update_preview)
        self.title.textChanged.connect(self.update_preview)
        self.update_preview()

    # Layout helpers -----------------------------------------------------------------

    def _section(self, letter, title):
        if self.body.count():
            rule = QFrame()
            rule.setProperty("role", "rule")
            rule.setFixedHeight(1)
            self.body.addSpacing(4)
            self.body.addWidget(rule)
        head = QHBoxLayout()
        head.setSpacing(10)
        badge = QLabel(letter)
        badge.setProperty("role", "letter")
        badge.setFixedSize(22, 22)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel(title)
        label.setProperty("role", "section")
        head.addWidget(badge)
        head.addWidget(label)
        head.addStretch()
        self.body.addLayout(head)
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self.body.addLayout(grid)
        return grid

    @staticmethod
    def _place(grid, row, column, label, widget, *, span=1, hint=""):
        caption = QLabel(
            label.replace(" *", f" <span style='color:{COLORS['error']}'>*</span>")
        )
        caption.setProperty("role", "field")
        grid.addWidget(caption, row, column, 1, span)
        grid.addWidget(widget, row + 1, column, 1, span)
        if hint:
            note = QLabel(hint)
            note.setProperty("role", "hint")
            note.setWordWrap(True)
            grid.addWidget(note, row + 2, column, 1, span)

    def _notify_box(self):
        box = QFrame()
        box.setObjectName("notifyBox")
        row = QHBoxLayout(box)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(12)
        icon = icon_label(Icon.SEND, 16, box, COLORS["on_primary"])
        icon.setObjectName("notifyIcon")
        icon.setFixedSize(36, 36)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        texts = QVBoxLayout()
        texts.setSpacing(6)
        line = QHBoxLayout()
        line.setSpacing(10)
        caption = QLabel("THỜI ĐIỂM GỬI THÔNG BÁO DỰ KIẾN:", box)
        caption.setObjectName("notifyCaption")
        self.notify_time = QLabel("—", box)
        self.notify_time.setObjectName("notifyTime")
        self.notify_chip = QLabel(box)
        self.notify_chip.setObjectName("notifyChip")
        line.addWidget(caption)
        line.addWidget(self.notify_time)
        line.addWidget(self.notify_chip)
        line.addStretch()
        self.preview = QLabel(box)
        self.preview.setObjectName("notifyExplain")
        self.preview.setWordWrap(True)
        self.preview.setTextFormat(Qt.TextFormat.RichText)
        texts.addLayout(line)
        texts.addWidget(self.preview)
        row.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        row.addLayout(texts, 1)
        self.body.addSpacing(4)
        self.body.addWidget(box)

    def _message_box(self):
        box = QFrame()
        box.setObjectName("messageBox")
        outer = QVBoxLayout(box)
        outer.setContentsMargins(14, 10, 14, 12)
        outer.setSpacing(8)
        top = QHBoxLayout()
        top.setSpacing(6)
        top.addWidget(icon_label(Icon.VIEW, 14, box, COLORS["muted"]))
        caption = QLabel("Nội dung gửi qua Telegram và thông báo Windows", box)
        caption.setProperty("role", "hint")
        top.addWidget(caption, 1)
        outer.addLayout(top)
        card = QFrame(box)
        card.setObjectName("messageCard")
        lines = QVBoxLayout(card)
        lines.setContentsMargins(14, 10, 14, 10)
        lines.setSpacing(4)
        heading = QLabel("Xây Dựng Số — Nhắc nhở", card)
        heading.setObjectName("messageHeading")
        self.message_text = QLabel(card)
        self.message_text.setWordWrap(True)
        self.message_due = QLabel(card)
        self.message_due.setObjectName("messageDue")
        code = QLabel("Mã nhắc: được tạo khi lưu lịch", card)
        code.setProperty("role", "hint")
        for widget in (heading, self.message_text, self.message_due, code):
            lines.addWidget(widget)
        outer.addWidget(card)
        channels = QHBoxLayout()
        channels.setSpacing(8)
        label = QLabel("Kênh gửi:", box)
        label.setProperty("role", "hint")
        channels.addWidget(label)
        channels.addStretch()
        for name in ("Telegram Bot", "Windows Toast"):
            chip = QLabel(name, box)
            chip.setProperty("role", "channel")
            channels.addWidget(chip)
        outer.addLayout(channels)
        self.body.addWidget(box)

    # Behaviour ---------------------------------------------------------------------

    def _apply_template(self):
        index = self.template.currentIndex()
        record = self.records_by_id.get(self.link.currentData())
        if index >= len(self.templates):
            return  # Custom text: keep whatever the user typed.
        if record is None:
            self.title.setText("")  # Templates need a linked record.
            self.applied = None
            return
        self.applied = render(
            self.templates[index].body,
            {
                "ma_ho_so": record.data.record_code,
                "ho_ten": record.data.applicant_name,
                "han_xu_ly": f"{self._deadline():%d/%m/%Y %H:%M}",
            },
        )
        self.title.setText(self.applied)

    def _deadline_changed(self, *_):
        # Keep {{han_xu_ly}} in step while the text is still the untouched template.
        if self.applied is not None and self.title.text() == self.applied:
            self._apply_template()

    def value(self):
        if not self.title.text().strip():
            raise ValidationError("Nội dung nhắc không được để trống.")
        return dict(
            title=self.title.text(),
            lead_seconds=self.duration.value(True),
            deadline_at=self._deadline(),
            record_id=self.link.currentData(),
        )

    def _deadline(self):
        return self.deadline.dateTime().toPyDateTime().replace(tzinfo=None)

    def record_changed(self, *_):
        record = self.records_by_id.get(self.link.currentData())
        if record is not None and record.data.deadline_at:
            initial = datetime.fromisoformat(record.data.deadline_at).astimezone(
                LOCAL_ZONE
            )
            self.deadline.setDateTime(
                QDateTime.fromString(
                    initial.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd HH:mm:ss"
                )
            )
        self._apply_template()

    def update_preview(self, *_):
        deadline = self._deadline().replace(tzinfo=LOCAL_ZONE)
        self.message_text.setText(self.title.text().strip() or "(Chưa có nội dung)")
        self.message_due.setText(f"Đến hạn: {deadline:%d/%m/%Y %H:%M:%S}")
        try:
            lead = self.duration.value(True)
            result = make_deadline_reminder(
                self.title.text().strip() or "Xem trước", self._deadline(), lead
            )
        except ValidationError as error:
            self.notify_time.setText("—")
            self._chip(False)
            self.preview.setText(str(error))
            return
        requested = (deadline.astimezone(UTC) - timedelta(seconds=lead)).astimezone(
            LOCAL_ZONE
        )
        notify = result.notify_at.astimezone(LOCAL_ZONE)
        self.notify_time.setText(f"{notify:%d/%m/%Y %H:%M}")
        self._chip(True)
        moved = notify != requested
        self.preview.setText(
            f"Giải thích: Hạn xử lý <b>{deadline:%d/%m/%Y %H:%M}</b> trừ đi "
            f"<b>{format_duration(lead)}</b> = {requested:%d/%m/%Y %H:%M}. "
            + (
                "Mốc này ngoài khung 07:00–23:00 hoặc đã qua nên được dời theo quy tắc. "
                if moved
                else "Nằm trong khung gửi 07:00–23:00. "
            )
            + "Cần bật nhắc nền để gửi."
        )

    def _chip(self, valid):
        self.notify_chip.setText("Hợp lệ" if valid else "Chưa hợp lệ")
        self.notify_chip.setProperty("valid", valid)
        self.notify_chip.style().unpolish(self.notify_chip)
        self.notify_chip.style().polish(self.notify_chip)
