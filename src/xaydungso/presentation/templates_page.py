"""Nhắc nhở > Cấu hình: manage notification templates (Stitch "Cấu hình" export)."""

from datetime import UTC, datetime, timedelta

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CheckBox,
    LineEdit,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SearchLineEdit,
    TransparentPushButton,
    TransparentToolButton,
    setCustomStyleSheet,
)

from xaydungso.domain.records import ValidationError
from xaydungso.domain.reminders import LOCAL_ZONE
from xaydungso.domain.templates import VARIABLES, Template, render
from xaydungso.presentation.confirm import ConfirmBox
from xaydungso.presentation.icons import Icon
from xaydungso.presentation.record_widgets import compact_checkbox, icon_label
from xaydungso.presentation.theme import COLORS, accent_button, qss, styled

HEADING = "Xây Dựng Số — Nhắc nhở"  # Same title the worker sends.
EMOJI = ("🔔", "📁", "👤", "📅", "⚠️", "✅", "❗")
DIVIDER = "────────────"

SHEET = """
QWidget#templates { background: @page; }
QLabel { background: transparent; color: @text; font-size: @fs_body; }
QLabel#tplTitle { font-size: @fs_page; font-weight: 700; }
QLabel[role="muted"] { color: @muted; font-size: @fs_small; }
QLabel[role="small"] { color: @muted; font-size: @fs_small; }
QLabel[role="panelTitle"] { font-size: @fs_heading; font-weight: 600; }
QLabel[role="field"] { font-size: @fs_body; font-weight: 600; }
QLabel[role="chip"] { background: @surface_container; color: @primary;
    border-radius: 8px; padding: 1px 8px; font-size: @fs_tiny; font-weight: 600; }
QLabel#savedChip { color: @muted; font-size: @fs_small; }
QLabel#savedChip[dirty="true"] { color: #b45309; font-weight: 600; }
QFrame[role="panel"] { background: @surface; border: 1px solid @outline_soft;
    border-radius: 10px; }
QWidget#tplList, QScrollArea { background: transparent; border: none; }
QPushButton[role="tplCard"] { background: transparent; border: none;
    border-radius: 8px; text-align: left; }
QPushButton[role="tplCard"]:hover { background: @surface_low; }
QPushButton[role="tplCard"]:checked { background: @surface_container; }
QLabel[role="cardName"] { font-size: @fs_body; font-weight: 600; }
QLabel[role="defaultChip"] { background: @surface_highest; color: @primary;
    border-radius: 4px; padding: 0 6px; font-size: @fs_tiny; font-weight: 700; }
QFrame#toolbarBox { background: @surface_low; border: 1px solid @outline_soft;
    border-radius: 8px; }
QFrame#varBox { background: @surface_low; border: 1px solid @outline_soft;
    border-radius: 8px; }
QFrame#previewFrame { background: @surface_low; border: 1px solid @outline_soft;
    border-radius: 8px; }
QFrame#bubble { background: @surface; border: 1px solid @outline_soft;
    border-radius: 8px; }
QLabel#bubbleHead { font-size: @fs_body; font-weight: 700; }
QLabel#botChip { background: #dbeafe; color: #1d4ed8; border-radius: 4px;
    padding: 0 5px; font-size: @fs_tiny; font-weight: 700; }
QLabel#previewText { font-size: @fs_body; }
QFrame#tplFooter { background: @surface; border: none;
    border-top: 1px solid @outline_soft; border-bottom-left-radius: 10px;
    border-bottom-right-radius: 10px; }
QLabel#tplError { color: @error; font-size: @fs_small; }
QPushButton[role="segment"] { background: transparent; border: 1px solid transparent;
    border-radius: 6px; padding: 4px 10px; font-size: @fs_small; color: @muted; }
QPushButton[role="segment"]:checked { background: @surface; color: @text;
    border-color: @outline; font-weight: 600; }
QFrame#segmentBox { background: @surface_low; border: 1px solid @outline_soft;
    border-radius: 8px; }
"""


def sample_values():
    deadline = datetime.now(LOCAL_ZONE) + timedelta(days=1)
    return {
        "ma_ho_so": "CPXD-2026-0089",
        "ho_ten": "Nguyễn Văn Hùng",
        "han_xu_ly": deadline.strftime("%d/%m/%Y %H:%M"),
    }


def ago(timestamp):
    """'10 phút trước' style label for the template list."""
    if not timestamp:
        return ""
    try:
        moment = datetime.fromisoformat(timestamp)
    except ValueError:
        return ""
    seconds = (datetime.now(UTC) - moment).total_seconds()
    if seconds < 60:
        return "Vừa xong"
    if seconds < 3600:
        return f"{int(seconds // 60)} phút trước"
    if seconds < 86400:
        return f"{int(seconds // 3600)} giờ trước"
    if seconds < 7 * 86400:
        return f"{int(seconds // 86400)} ngày trước"
    return moment.astimezone(LOCAL_ZONE).strftime("%d/%m/%Y")


class TemplatesPage(QWidget):
    back = pyqtSignal()
    changed = pyqtSignal()

    def __init__(self, service, runner, parent=None):
        super().__init__(parent)
        self.setObjectName("templates")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        styled(self, SHEET)
        self.service, self.runner = service, runner
        self.templates, self.cards = [], []
        self.current = None  # Template being edited (id None = new, unsaved).
        self.loading_editor = False
        self.dirty = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 12)
        layout.setSpacing(10)

        # Header.
        self.back_button = TransparentPushButton("←  Quay lại Nhắc nhở", self)
        self.back_button.setFixedHeight(26)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel("Cấu hình nội dung thông báo", self)
        title.setObjectName("tplTitle")
        subtitle = QLabel("Tạo và quản lý các mẫu nội dung dùng cho lịch nhắc", self)
        subtitle.setProperty("role", "muted")
        titles.addWidget(self.back_button, 0, Qt.AlignmentFlag.AlignLeft)
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles, 1)
        self.add_button = PrimaryPushButton(Icon.ADD, "Thêm mẫu", self)
        accent_button(self.add_button)
        header.addWidget(self.add_button, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self._list_panel())
        body.addWidget(self._editor_panel(), 1)
        layout.addLayout(body, 1)

        self.back_button.clicked.connect(self._back)
        self.add_button.clicked.connect(self._new)
        self.search.textChanged.connect(lambda _: self._show_list())
        self.reload_button.clicked.connect(
            lambda: self.refresh() if self._confirm_discard() else None
        )
        self.name.textChanged.connect(self._edited)
        self.body.textChanged.connect(self._edited)
        self.default_check.stateChanged.connect(self._edited)
        self.save_button.clicked.connect(self._save)
        self.revert_button.clicked.connect(self._revert)
        self.delete_button.clicked.connect(self._delete)
        self.refresh()

    # Layout -------------------------------------------------------------------------

    def _list_panel(self):
        panel = QFrame(self)
        panel.setProperty("role", "panel")
        panel.setFixedWidth(320)
        box = QVBoxLayout(panel)
        box.setContentsMargins(12, 12, 12, 12)
        box.setSpacing(8)
        head = QHBoxLayout()
        title = QLabel("Mẫu thông báo", panel)
        title.setProperty("role", "panelTitle")
        self.count = QLabel(panel)
        self.count.setProperty("role", "chip")
        self.reload_button = TransparentToolButton(Icon.SYNC, panel)
        self.reload_button.setToolTip("Tải lại")
        head.addWidget(title)
        head.addWidget(self.count)
        head.addStretch()
        head.addWidget(self.reload_button)
        box.addLayout(head)
        self.search = SearchLineEdit(panel)
        self.search.setPlaceholderText("Tìm mẫu thông báo...")
        box.addWidget(self.search)
        scroll = ScrollArea(panel)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        holder = QWidget()
        holder.setObjectName("tplList")
        self.list_layout = QVBoxLayout(holder)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.addStretch()
        scroll.setWidget(holder)
        box.addWidget(scroll, 1)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        return panel

    def _editor_panel(self):
        panel = QFrame(self)
        panel.setProperty("role", "panel")
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        scroll = ScrollArea(panel)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        holder = QWidget()
        holder.setObjectName("tplList")
        box = QVBoxLayout(holder)
        box.setContentsMargins(20, 14, 20, 14)
        box.setSpacing(8)
        scroll.setWidget(holder)
        outer.addWidget(scroll, 1)

        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(icon_label(Icon.EDIT, 16, panel, COLORS["primary"]))
        title = QLabel("Chỉnh sửa mẫu thông báo", panel)
        title.setProperty("role", "panelTitle")
        self.saved = QLabel(panel)
        self.saved.setObjectName("savedChip")
        head.addWidget(title)
        head.addStretch()
        head.addWidget(self.saved)
        box.addLayout(head)

        box.addWidget(self._field("Tên mẫu thông báo *"))
        self.name = LineEdit(panel)
        self.name.setMinimumHeight(34)
        self.name.setPlaceholderText("VD: Nhắc hồ sơ sắp đến hạn")
        box.addWidget(self.name)

        label_row = QHBoxLayout()
        label_row.addWidget(self._field("Nội dung thông báo *"))
        label_row.addStretch()
        plain = QLabel(
            "Văn bản thường, nhiều dòng; hiển thị giống nhau trên Telegram và Windows"
        )
        plain.setProperty("role", "small")
        label_row.addWidget(plain)
        box.addLayout(label_row)
        toolbar = QFrame(panel)
        toolbar.setObjectName("toolbarBox")
        tools = QHBoxLayout(toolbar)
        tools.setContentsMargins(6, 4, 6, 4)
        tools.setSpacing(2)
        bullet = TransparentPushButton("•  Gạch đầu dòng", toolbar)
        bullet.setToolTip("Thêm dấu • ở đầu dòng đang chọn")
        bullet.clicked.connect(self._bullet)
        divider = TransparentPushButton("—  Đường kẻ", toolbar)
        divider.setToolTip("Chèn một dòng kẻ ngang")
        divider.clicked.connect(lambda: self._insert_line(DIVIDER))
        tools.addWidget(bullet)
        tools.addWidget(divider)
        tools.addSpacing(8)
        for emoji in EMOJI:
            button = TransparentPushButton(emoji, toolbar)
            button.setFixedWidth(34)
            button.setToolTip("Chèn biểu tượng")
            button.clicked.connect(lambda _, e=emoji: self._insert(e))
            tools.addWidget(button)
        tools.addStretch()
        box.addWidget(toolbar)
        self.body = PlainTextEdit(panel)
        self.body.setMinimumHeight(150)
        self.body.setPlaceholderText(
            "VD:\n🔔 THÔNG BÁO HỒ SƠ SẮP ĐẾN HẠN\n📁 Mã hồ sơ: {{ma_ho_so}}"
        )
        box.addWidget(self.body)

        variables = QFrame(panel)
        variables.setObjectName("varBox")
        var_box = QVBoxLayout(variables)
        var_box.setContentsMargins(10, 8, 10, 10)
        var_box.setSpacing(6)
        var_head = QHBoxLayout()
        var_title = QLabel("Chèn thông tin hồ sơ", variables)
        var_title.setProperty("role", "field")
        hint = QLabel("(Nhấp để chèn biến vào vị trí con trỏ)", variables)
        hint.setProperty("role", "small")
        var_count = QLabel(f"{len(VARIABLES)} biến khả dụng", variables)
        var_count.setProperty("role", "chip")
        var_head.addWidget(var_title)
        var_head.addWidget(hint)
        var_head.addStretch()
        var_head.addWidget(var_count)
        var_box.addLayout(var_head)
        buttons = QHBoxLayout()
        buttons.setSpacing(6)
        self.variable_buttons = {}
        for key, label in VARIABLES:
            button = PushButton(f"+  {label}   {{{{{key}}}}}", variables)
            button.clicked.connect(lambda _, k=key: self._insert(f"{{{{{k}}}}}"))
            buttons.addWidget(button)
            self.variable_buttons[key] = button
        buttons.addStretch()
        var_box.addLayout(buttons)
        box.addWidget(variables)

        self.default_check = compact_checkbox(CheckBox("Đặt làm mẫu mặc định", panel))
        default_hint = QLabel(
            "Mẫu này sẽ được tự động chọn khi tạo lịch nhắc mới.", panel
        )
        default_hint.setProperty("role", "small")
        box.addWidget(self.default_check)
        box.addWidget(default_hint)

        preview_head = QHBoxLayout()
        preview_head.setSpacing(8)
        preview_head.addWidget(icon_label(Icon.VIEW, 16, panel, COLORS["text"]))
        preview_title = QLabel("Xem trước thông báo", panel)
        preview_title.setProperty("role", "panelTitle")
        preview_head.addWidget(preview_title)
        preview_head.addStretch()
        mode = QLabel("Chế độ hiển thị:", panel)
        mode.setProperty("role", "small")
        preview_head.addWidget(mode)
        segments = QFrame(panel)
        segments.setObjectName("segmentBox")
        seg = QHBoxLayout(segments)
        seg.setContentsMargins(3, 3, 3, 3)
        seg.setSpacing(3)
        self.preview_group = QButtonGroup(self)
        self.telegram_mode = self._segment("Telegram", segments)
        self.windows_mode = self._segment("Windows Toast", segments)
        self.telegram_mode.setChecked(True)
        for button in (self.telegram_mode, self.windows_mode):
            self.preview_group.addButton(button)
            seg.addWidget(button)
            button.toggled.connect(lambda _: self._preview())
        preview_head.addWidget(segments)
        box.addLayout(preview_head)

        frame = QFrame(panel)
        frame.setObjectName("previewFrame")
        frame_box = QVBoxLayout(frame)
        frame_box.setContentsMargins(12, 10, 12, 12)
        bubble = QFrame(frame)
        bubble.setObjectName("bubble")
        bubble_box = QVBoxLayout(bubble)
        bubble_box.setContentsMargins(12, 10, 12, 12)
        bubble_box.setSpacing(6)
        top = QHBoxLayout()
        top.setSpacing(6)
        self.preview_icon = icon_label(Icon.SEND, 14, bubble, COLORS["primary"])
        self.preview_sender = QLabel(bubble)
        self.preview_sender.setObjectName("bubbleHead")
        self.bot_chip = QLabel("BOT", bubble)
        self.bot_chip.setObjectName("botChip")
        self.preview_time = QLabel(bubble)
        self.preview_time.setProperty("role", "small")
        top.addWidget(self.preview_icon)
        top.addWidget(self.preview_sender)
        top.addWidget(self.bot_chip)
        top.addStretch()
        top.addWidget(self.preview_time)
        self.preview_text = QLabel(bubble)
        self.preview_text.setObjectName("previewText")
        self.preview_text.setWordWrap(True)
        self.preview_text.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        sample = QLabel(
            "Dữ liệu minh họa; khi tạo lịch, biến được thay bằng hồ sơ thật.", bubble
        )
        sample.setProperty("role", "small")
        bubble_box.addLayout(top)
        bubble_box.addWidget(self.preview_text)
        frame_box.addWidget(bubble)
        frame_box.addWidget(sample)
        box.addWidget(frame)
        box.addStretch()

        footer = QFrame(panel)
        footer.setObjectName("tplFooter")
        foot = QHBoxLayout(footer)
        foot.setContentsMargins(16, 10, 16, 10)
        foot.setSpacing(10)
        self.delete_button = TransparentPushButton(Icon.DELETE, "Xóa mẫu", footer)
        danger = qss(
            "TransparentPushButton { color: @error; }"
            " TransparentPushButton:hover { background: #fee2e2; }"
        )
        setCustomStyleSheet(self.delete_button, danger, danger)
        self.error = QLabel(footer)
        self.error.setObjectName("tplError")
        self.error.setWordWrap(True)
        self.revert_button = PushButton("Hủy thay đổi", footer)
        self.save_button = PrimaryPushButton(Icon.ACCEPT, "Lưu mẫu", footer)
        accent_button(self.save_button)
        foot.addWidget(self.delete_button)
        foot.addWidget(self.error, 1)
        foot.addWidget(self.revert_button)
        foot.addWidget(self.save_button)
        outer.addWidget(footer)
        return panel

    @staticmethod
    def _field(text):
        label = QLabel(
            text.replace(" *", f" <span style='color:{COLORS['error']}'>*</span>")
        )
        label.setProperty("role", "field")
        return label

    @staticmethod
    def _segment(text, parent):
        button = QPushButton(text, parent)
        button.setProperty("role", "segment")
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    # Data -------------------------------------------------------------------------

    def refresh(self, select_id=None):
        keep = (
            select_id
            if select_id is not None
            else (self.current.id if self.current else None)
        )
        self.runner.submit(
            self.service.list, lambda items: self._loaded(items, keep), self._failed
        )

    def _loaded(self, items, keep):
        self.templates = items
        self._show_list()
        target = next((t for t in items if t.id == keep), None)
        if target is None and items:
            target = items[0]
        if self.current is None or self.current.id is not None or keep is not None:
            self._edit(target)

    def _failed(self, error):
        self.error.setText(
            str(error)
            if isinstance(error, ValidationError)
            else "Không thực hiện được. Hãy thử lại."
        )

    def _show_list(self):
        for card in self.cards:
            self.group.removeButton(card)
            card.deleteLater()
        self.cards = []
        needle = self.search.text().strip().casefold()
        shown = [
            t
            for t in self.templates
            if not needle or needle in t.name.casefold() or needle in t.body.casefold()
        ]
        self.count.setText(f"{len(self.templates)} mẫu")
        for index, template in enumerate(shown):
            card = self._card(template)
            self.list_layout.insertWidget(index, card)
            self.cards.append(card)
        self._mark_selected()

    def _card(self, template):
        card = QPushButton()
        card.setProperty("role", "tplCard")
        card.setCheckable(True)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.template_id = template.id
        box = QVBoxLayout(card)
        box.setContentsMargins(10, 8, 10, 8)
        box.setSpacing(3)
        top = QHBoxLayout()
        name = QLabel(template.name, card)
        name.setProperty("role", "cardName")
        top.addWidget(name, 1)
        if template.is_default:
            chip = QLabel("Mặc định", card)
            chip.setProperty("role", "defaultChip")
            top.addWidget(chip)
        first = next((line for line in template.body.splitlines() if line.strip()), "")
        preview = QLabel(first, card)
        preview.setProperty("role", "muted")
        preview.setMaximumWidth(276)
        when = QLabel(f"🕑  {ago(template.updated_at)}", card)
        when.setProperty("role", "small")
        box.addLayout(top)
        box.addWidget(preview)
        box.addWidget(when)
        for widget in (name, preview, when):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        card.setMinimumHeight(box.sizeHint().height())
        self.group.addButton(card)
        card.clicked.connect(lambda _, t=template: self._choose(t))
        return card

    def _mark_selected(self):
        current = self.current.id if self.current else None
        for card in self.cards:
            card.setChecked(card.template_id == current and current is not None)

    # Editing ------------------------------------------------------------------------

    def _choose(self, template):
        if self.current is not None and template.id == self.current.id:
            return
        if self._confirm_discard():
            self._edit(template)
        else:
            self._mark_selected()

    def _confirm_discard(self):
        if not self.dirty:
            return True
        box = ConfirmBox(
            "Bỏ thay đổi chưa lưu?",
            "Mẫu đang sửa có thay đổi chưa lưu. Chuyển sang mẫu khác sẽ bỏ các thay đổi này.",
            self.window(),
        )
        box.yesButton.setText("Bỏ thay đổi")
        box.cancelButton.setText("Tiếp tục sửa")
        return bool(box.exec())

    def _edit(self, template):
        self.current = template
        self.loading_editor = True
        self.name.setText(template.name if template else "")
        self.body.setPlainText(template.body if template else "")
        self.default_check.setChecked(bool(template and template.is_default))
        self.loading_editor = False
        self.error.setText("")
        self._set_dirty(False)
        self.delete_button.setEnabled(bool(template and template.id is not None))
        self._mark_selected()
        self._preview()

    def _new(self):
        if self._confirm_discard():
            self.current = None
            self._edit(None)
            self.name.setText("Mẫu mới")
            self.name.selectAll()
            self.name.setFocus()
            self._set_dirty(True)

    def _revert(self):
        if self.current is None or self.current.id is None:
            self._edit(self.templates[0] if self.templates else None)
        else:
            self._edit(self.current)

    def _edited(self, *_):
        if not self.loading_editor:
            self._set_dirty(True)
            self._preview()

    def _set_dirty(self, dirty):
        self.dirty = dirty
        self.saved.setText("●  Có thay đổi chưa lưu" if dirty else "●  Đã lưu")
        self.saved.setProperty("dirty", dirty)
        self.saved.style().unpolish(self.saved)
        self.saved.style().polish(self.saved)
        self.save_button.setEnabled(dirty)
        self.revert_button.setEnabled(dirty)

    def _insert(self, text):
        self.body.insertPlainText(text)
        self.body.setFocus()

    def _insert_line(self, text):
        cursor = self.body.textCursor()
        if cursor.positionInBlock():
            cursor.insertText("\n")
        cursor.insertText(text + "\n")
        self.body.setTextCursor(cursor)
        self.body.setFocus()

    def _bullet(self):
        cursor = self.body.textCursor()
        cursor.movePosition(cursor.MoveOperation.StartOfBlock)
        cursor.insertText("• ")
        self.body.setFocus()

    def _preview(self):
        text = render(
            self.body.toPlainText().strip() or "(Chưa có nội dung)", sample_values()
        )
        due = (datetime.now(LOCAL_ZONE) + timedelta(days=1)).strftime(
            "%d/%m/%Y %H:%M:%S"
        )
        lines = [text, f"Đến hạn: {due}", "Mã nhắc: (tạo khi lưu lịch)"]
        telegram = self.telegram_mode.isChecked()
        self.bot_chip.setVisible(telegram)
        self.preview_sender.setText("Xây Dựng Số Bot" if telegram else "Xây Dựng Số")
        self.preview_time.setText(
            f"Hôm nay {datetime.now(LOCAL_ZONE):%H:%M}" if telegram else "Bây giờ"
        )
        # Telegram shows the heading as the first line; a toast shows it in bold.
        heading = f"<b>{HEADING}</b>" if not telegram else HEADING
        body = "<br>".join(_escape(line) for line in "\n".join(lines).split("\n"))
        self.preview_text.setText(f"{heading}<br>{body}")

    def _save(self):
        try:
            template = Template(
                self.current.id if self.current else None,
                self.name.text(),
                self.body.toPlainText().rstrip(),
                self.default_check.isChecked(),
            )
        except ValidationError as error:
            self.error.setText(str(error))
            return
        self.save_button.setEnabled(False)

        def saved(result):
            self.current = result
            self._set_dirty(False)
            self.refresh(result.id)
            self.changed.emit()

        def failed(error):
            self.save_button.setEnabled(True)
            self._failed(error)

        self.runner.submit(lambda: self.service.save(template), saved, failed)

    def _delete(self):
        if self.current is None or self.current.id is None:
            return
        if self.current.is_default:
            self.error.setText(
                "Không xóa được mẫu mặc định. Hãy đặt mẫu khác làm mặc định trước."
            )
            return
        box = ConfirmBox(
            "Xóa mẫu thông báo?",
            f'Mẫu "{self.current.name}" sẽ bị xóa vĩnh viễn. Các lịch nhắc đã tạo '
            "không bị ảnh hưởng.",
            self.window(),
        )
        box.yesButton.setText("Xóa mẫu")
        box.cancelButton.setText("Giữ mẫu")
        if box.exec():
            template_id = self.current.id
            self.current = None
            self.runner.submit(
                lambda: self.service.delete(template_id),
                lambda _: (self.refresh(), self.changed.emit()),
                self._failed,
            )

    def _back(self):
        if self._confirm_discard():
            self._set_dirty(False)
            if self.current is not None and self.current.id is None:
                self.current = None
            self.back.emit()


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
