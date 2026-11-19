"""Fluent Dashboard consumes only the Application read model."""

import math

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    TableWidget,
    TransparentPushButton,
    setCustomStyleSheet,
)

from xaydungso.application.dashboard import Dashboard, DashboardSnapshot, is_overdue
from xaydungso.domain.reminders import LOCAL_ZONE
from xaydungso.presentation.icons import Icon, colored_icon
from xaydungso.presentation.record_widgets import icon_label
from xaydungso.presentation.theme import (
    COLORS,
    accent_button,
    mono_font,
    qss,
    styled,
)

SHEET = """
QWidget#dashboard { background: @page; }
QLabel { background: transparent; color: @text; font-size: @fs_body; }
QLabel#dashTitle { font-size: @fs_page; font-weight: 700; }
QLabel#dashSubtitle { color: @muted; font-size: @fs_small; }
QLabel#syncChip { background: @surface_container; color: @muted; border-radius: 8px;
    padding: 2px 8px; font-size: @fs_tiny; }
QFrame[role="metric"], QFrame[role="panel"] { background: @surface;
    border: 1px solid @outline_soft; border-radius: 10px; }
QFrame[role="metric"][tone="pending"] { background: #fffbeb; border-color: #fde68a; }
QFrame[role="metric"][tone="done"] { background: #f0fdf4; border-color: #bbf7d0; }
QFrame[role="metric"][tone="alert"] { background: #fdeeee; border-color: #f5c9c9; }
QLabel[role="metricTitle"][tone="pending"], QLabel[role="metricNote"][tone="pending"] {
    color: @pending_fg; }
QLabel[role="metricTitle"][tone="done"], QLabel[role="metricNote"][tone="done"] {
    color: @done_fg; }
QLabel[role="metricTitle"][tone="alert"], QLabel[role="metricNote"][tone="alert"] {
    color: @error; }
QLabel[role="metricTitle"] { color: @muted; font-size: @fs_small; }
QLabel[role="metricValue"] { font-size: @fs_stat; font-weight: 700; }
QLabel[role="metricNote"] { color: @muted; font-size: @fs_small; }
QLabel[role="iconTile"] { background: @surface_container; border-radius: 6px; }
QLabel[role="iconTile"][tone="pending"] { background: @pending_bg; }
QLabel[role="iconTile"][tone="done"] { background: @done_bg; }
QLabel[role="iconTile"][tone="alert"] { background: #fbd5d5; }
QLabel[role="chip"] { background: @surface_container; color: @primary;
    border-radius: 4px; padding: 1px 6px; font-size: @fs_tiny; font-weight: 600; }
QLabel[role="chip"][tone="alert"] { background: #fbd5d5; color: @error; }
QLabel[role="panelTitle"] { font-size: @fs_heading; font-weight: 600; }
QLabel[role="countChip"] { background: #fbd5d5; color: @error; border-radius: 8px;
    padding: 1px 8px; font-size: @fs_tiny; font-weight: 600; }
QLabel[role="empty"] { color: @muted; font-size: @fs_small; }
QLabel[role="emptyTitle"] { font-size: @fs_body; font-weight: 600; }
QFrame[role="reminder"] { background: @surface_low; border: 1px solid @outline_soft;
    border-radius: 8px; }
QLabel[role="reminderTitle"] { font-size: @fs_body; font-weight: 600; }
QLabel[role="reminderText"] { color: @muted; font-size: @fs_small; }
QLabel[role="reminderTime"] { color: @muted; font-family: @mono; font-size: @fs_mono; }
QLabel[role="reminderTime"][today="true"] { color: @error; font-weight: 700; }
QLabel[role="codeChip"] { background: @surface_container; color: @primary;
    border-radius: 4px; padding: 0 5px; font-family: @mono; font-size: @fs_tiny;
    font-weight: 700; }
QWidget#reminderList, QScrollArea { background: transparent; border: none; }
"""

METRICS = (
    ("total_records", "Tổng hồ sơ", Icon.FOLDER, COLORS["text"]),
    ("incomplete_records", "Chưa hoàn thành", Icon.HISTORY, COLORS["pending_fg"]),
    ("completed_records", "Đã hoàn thành", Icon.ACCEPT, COLORS["done_fg"]),
    ("overdue_records", "Quá hạn", Icon.INFO, COLORS["error"]),
)

# Card colour by meaning: amber in progress, green done, red overdue.
TONES = {
    "incomplete_records": "pending",
    "completed_records": "done",
    "overdue_records": "alert",
}


def _set(widget, **properties):
    for name, value in properties.items():
        widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def warning_text(item, as_of):
    """'Quá hạn' or 'Sắp hạn (Còn N giờ/phút)' for the attention table."""
    if is_overdue(item, as_of):
        return "Quá hạn"
    minutes = math.ceil((item.deadline_at - as_of).total_seconds() / 60)
    if minutes < 60:
        return f"Sắp hạn (Còn {minutes} phút)"
    return f"Sắp hạn (Còn {math.ceil(minutes / 60)} giờ)"


def relative_day(moment, as_of):
    days = (moment.date() - as_of.date()).days
    return {0: "Hôm nay", 1: "Ngày mai"}.get(days, "")


class EmptyState(QWidget):
    """Centred icon + heading + muted line for a panel with nothing to list."""

    def __init__(self, parent=None):
        super().__init__(parent)
        box = QVBoxLayout(self)
        box.setContentsMargins(24, 16, 24, 24)
        box.setSpacing(6)
        box.addStretch()
        self.icon = QLabel(self)
        self.icon.setFixedSize(44, 44)
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title = QLabel(self)
        self.title.setProperty("role", "emptyTitle")
        self.message = QLabel(self)
        self.message.setProperty("role", "empty")
        self.message.setWordWrap(True)
        for label in (self.title, self.message):
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        box.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignHCenter)
        box.addSpacing(4)
        box.addWidget(self.title)
        box.addWidget(self.message)
        box.addStretch()
        self.hide()

    def show_state(self, icon, colour, background, title, message):
        self.icon.setPixmap(colored_icon(icon, colour).pixmap(QSize(20, 20)))
        self.icon.setStyleSheet(f"background: {background}; border-radius: 22px;")
        self.title.setText(title)
        self.message.setText(message)
        self.show()

    def clear(self):
        self.title.setText("")
        self.message.setText("")
        self.hide()


class DashboardPage(QWidget):
    open_records = pyqtSignal()
    open_reminders = pyqtSignal()
    open_record = pyqtSignal(int)
    add_record = pyqtSignal()
    loaded = pyqtSignal(object)

    def __init__(self, service: Dashboard, runner, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        styled(self, SHEET)
        self.service, self.runner = service, runner
        self.loading = False
        self.upcoming_items = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Header: title, sync time, subtitle and actions.
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title = QLabel("Tổng quan", self)
        title.setObjectName("dashTitle")
        self.sync = QLabel(self)
        self.sync.setObjectName("syncChip")
        title_row.addWidget(title)
        title_row.addWidget(self.sync)
        title_row.addStretch()
        subtitle = QLabel("Theo dõi tình trạng hồ sơ và công việc cần xử lý", self)
        subtitle.setObjectName("dashSubtitle")
        titles.addLayout(title_row)
        titles.addWidget(subtitle)
        header.addLayout(titles, 1)
        self.refresh_button = PushButton(Icon.SYNC, "Tải lại", self)
        self.add_button = PrimaryPushButton(Icon.ADD, "Thêm hồ sơ", self)
        accent_button(self.add_button)
        header.addWidget(self.refresh_button, 0, Qt.AlignmentFlag.AlignTop)
        header.addWidget(self.add_button, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)
        self.feedback = QLabel(self)
        self.feedback.setObjectName("dashSubtitle")
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)

        # Four metric cards.
        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.metric_values, self.metric_notes, self.metric_chips = {}, {}, {}
        for key, label, icon, colour in METRICS:
            tone = TONES.get(key, "")
            card = QFrame(self)
            card.setProperty("role", "metric")
            card.setProperty("tone", tone)
            box = QVBoxLayout(card)
            box.setContentsMargins(14, 12, 14, 12)
            box.setSpacing(4)
            top = QHBoxLayout()
            caption = QLabel(label, card)
            caption.setProperty("role", "metricTitle")
            caption.setProperty("tone", tone)
            tile = icon_label(icon, 16, card, colour)
            tile.setProperty("role", "iconTile")
            tile.setProperty("tone", tone)
            tile.setFixedSize(28, 28)
            tile.setAlignment(Qt.AlignmentFlag.AlignCenter)
            top.addWidget(caption, 0, Qt.AlignmentFlag.AlignTop)
            top.addStretch()
            top.addWidget(tile)
            value = QLabel("—", card)
            value.setProperty("role", "metricValue")
            value.setStyleSheet(f"color: {colour};")
            foot = QHBoxLayout()
            foot.setSpacing(8)
            chip = QLabel(card)
            chip.setProperty("role", "chip")
            chip.setProperty("tone", tone)
            chip.hide()
            note = QLabel(card)
            note.setProperty("role", "metricNote")
            note.setProperty("tone", tone)
            foot.addWidget(chip)
            foot.addWidget(note)
            foot.addStretch()
            box.addLayout(top)
            box.addWidget(value)
            box.addLayout(foot)
            cards.addWidget(card, 1)
            self.metric_values[key] = value
            self.metric_notes[key] = note
            self.metric_chips[key] = chip
        layout.addLayout(cards)

        # Attention table (left) and upcoming reminders (right).
        panels = QHBoxLayout()
        panels.setSpacing(12)
        attention = QFrame(self)
        attention.setProperty("role", "panel")
        attention_box = QVBoxLayout(attention)
        attention_box.setContentsMargins(14, 10, 14, 12)
        attention_box.setSpacing(8)
        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(icon_label(Icon.INFO, 16, attention, COLORS["error"]))
        attention_title = QLabel("Hồ sơ cần chú ý", attention)
        attention_title.setProperty("role", "panelTitle")
        self.attention_count = QLabel(attention)
        self.attention_count.setProperty("role", "countChip")
        self.attention_count.hide()
        self.records_button = TransparentPushButton("Xem tất cả  →", attention)
        head.addWidget(attention_title)
        head.addWidget(self.attention_count)
        head.addStretch()
        head.addWidget(self.records_button)
        attention_box.addLayout(head)
        self.attention_empty = EmptyState(attention)
        self.attention_message = self.attention_empty.message
        attention_box.addWidget(self.attention_empty, 1)
        self.attention_table = self._attention_table(attention)
        attention_box.addWidget(self.attention_table, 1)
        panels.addWidget(attention, 1)

        upcoming = QFrame(self)
        upcoming.setProperty("role", "panel")
        upcoming.setFixedWidth(300)
        upcoming_box = QVBoxLayout(upcoming)
        upcoming_box.setContentsMargins(12, 10, 12, 12)
        upcoming_box.setSpacing(8)
        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(icon_label(Icon.RINGER, 16, upcoming, COLORS["text"]))
        upcoming_title = QLabel("Lịch nhắc sắp tới", upcoming)
        upcoming_title.setProperty("role", "panelTitle")
        self.reminders_button = TransparentPushButton("Xem lịch nhắc  →", upcoming)
        head.addWidget(upcoming_title)
        head.addStretch()
        head.addWidget(self.reminders_button)
        upcoming_box.addLayout(head)
        self.upcoming_empty = EmptyState(upcoming)
        self.upcoming_message = self.upcoming_empty.message
        upcoming_box.addWidget(self.upcoming_empty, 1)
        scroll = ScrollArea(upcoming)
        self.upcoming_scroll = scroll
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        holder = QWidget()
        holder.setObjectName("reminderList")
        self.upcoming_list = QVBoxLayout(holder)
        self.upcoming_list.setContentsMargins(0, 0, 0, 0)
        self.upcoming_list.setSpacing(8)
        self.upcoming_list.addStretch()
        scroll.setWidget(holder)
        upcoming_box.addWidget(scroll, 1)
        panels.addWidget(upcoming)
        layout.addLayout(panels, 1)

        self.refresh_button.clicked.connect(self.refresh)
        self.add_button.clicked.connect(self.add_record.emit)
        self.records_button.clicked.connect(self.open_records.emit)
        self.reminders_button.clicked.connect(self.open_reminders.emit)
        self.timer = QTimer(self)
        self.timer.setInterval(30_000)
        self.timer.timeout.connect(self._automatic_refresh)
        self.timer.start()
        self.refresh()

    def _attention_table(self, parent):
        table = TableWidget(parent)
        headers = ("MÃ HỒ SƠ", "HỌ VÀ TÊN", "ĐỊA CHỈ", "HẠN XỬ LÝ", "CẢNH BÁO", "")
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.verticalHeader().hide()
        table.verticalHeader().setDefaultSectionSize(40)
        table.setWordWrap(False)
        table.setBorderVisible(False)
        table.setAlternatingRowColors(False)
        header = table.horizontalHeader()
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        for column, width in enumerate((112, 0, 0, 164, 146, 84)):
            if width:
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
                header.resizeSection(column, width)
            else:
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        sheet = qss(
            "QHeaderView::section { background-color: @surface_low; color: @muted;"
            " font-family: @font; font-size: @fs_tiny; font-weight: 600; border: none;"
            " border-bottom: 1px solid @outline_soft; padding-left: 19px; }"
        )
        setCustomStyleSheet(table, sheet, sheet)
        return table

    def _automatic_refresh(self):
        if self.isVisible() and not self.runner.busy:
            self.refresh()

    def refresh(self):
        if self.loading:
            return
        self.loading = True
        self.refresh_button.setEnabled(False)
        self.feedback.setText("Đang tải dữ liệu…")
        self.feedback.show()
        for key, value in self.metric_values.items():
            value.setText("—")
            self.metric_notes[key].setText("")
            self.metric_chips[key].hide()
        self.attention_table.setRowCount(0)
        self.attention_empty.clear()
        self.attention_count.hide()
        self._clear_upcoming()
        self.upcoming_empty.clear()
        self.runner.submit(self.service.load, self._render, self._failed)

    def _clear_upcoming(self):
        for card in self.upcoming_items:
            self.upcoming_list.removeWidget(card)
            card.deleteLater()
        self.upcoming_items = []

    def _render(self, snapshot: DashboardSnapshot):
        self.loaded.emit(snapshot)
        self.loading = False
        self.refresh_button.setEnabled(True)
        as_of = snapshot.as_of.astimezone(LOCAL_ZONE)
        self.feedback.setText("")
        self.feedback.hide()
        self.sync.setText(f"●  Đồng bộ: {as_of:%H:%M}")
        self.sync.setToolTip(f"Cập nhật lúc {as_of:%d/%m/%Y %H:%M:%S} (giờ Việt Nam)")
        for key, value in self.metric_values.items():
            value.setText(str(getattr(snapshot, key)))
        notes = {
            "total_records": (None, "Toàn bộ hồ sơ trên hệ thống"),
            "incomplete_records": (None, "Đang trong quy trình"),
            "completed_records": (None, "Đã hoàn thành"),
            "overdue_records": (
                ("●  Cần xử lý ngay", "Chậm tiến độ")
                if snapshot.overdue_records
                else (None, "Không có hồ sơ quá hạn")
            ),
        }
        for key, (chip, note) in notes.items():
            self.metric_chips[key].setText(chip or "")
            self.metric_chips[key].setVisible(bool(chip))
            self.metric_notes[key].setText(note)
        self._render_attention(snapshot, as_of)
        self._render_upcoming(snapshot, as_of)

    def _render_attention(self, snapshot, as_of):
        items = snapshot.attention
        self.attention_count.setText(f"{snapshot.attention_total} hồ sơ")
        self.attention_count.setVisible(snapshot.attention_total > 0)
        if items:
            self.attention_empty.clear()
        else:
            self.attention_empty.show_state(
                Icon.ACCEPT,
                COLORS["done_fg"],
                COLORS["done_bg"],
                "Không có hồ sơ cần chú ý",
                "Không có hồ sơ quá hạn hoặc đến hạn trong 24 giờ tới.",
            )
        table = self.attention_table
        table.setVisible(bool(items))
        table.setRowCount(len(items))
        for row, item in enumerate(items):
            overdue = is_overdue(item, as_of)
            deadline = item.deadline_at.astimezone(LOCAL_ZONE).strftime(
                "%d/%m/%Y %H:%M"
            )
            code = QTableWidgetItem(item.record_code)
            code.setIcon(
                colored_icon(
                    Icon.INFO if overdue else Icon.HISTORY,
                    COLORS["error"] if overdue else COLORS["muted"],
                )
            )
            for column, cell in enumerate(
                (
                    code,
                    QTableWidgetItem(item.applicant_name),
                    QTableWidgetItem(item.address),
                    QTableWidgetItem(deadline),
                )
            ):
                cell.setToolTip(cell.text())
                if column == 0:
                    cell.setFont(mono_font(weight=QFont.Weight.Bold))
                elif column == 3:
                    cell.setFont(mono_font())
                if column == 3 and overdue:
                    cell.setForeground(QColor(COLORS["error"]))
                table.setItem(row, column, cell)
            text = warning_text(item, as_of)
            badge = QLabel(("●  " if overdue else "") + text)
            styled(
                badge,
                "QLabel { background: %s; color: %s; border-radius: 4px;"
                " padding: 2px 8px; font-size: @fs_tiny; font-weight: 600; }"
                % (
                    ("#fbd5d5", "@error")
                    if overdue
                    else ("@surface_container", "@primary")
                ),
            )
            table.setItem(row, 4, QTableWidgetItem())
            table.setCellWidget(row, 4, self._cell(badge, 19))
            detail = PushButton("Chi tiết")
            detail.setFixedHeight(28)
            detail.clicked.connect(lambda _, i=item.id: self.open_record.emit(i))
            table.setItem(row, 5, QTableWidgetItem())
            table.setCellWidget(row, 5, self._cell(detail, 8))

    @staticmethod
    def _cell(widget, left):
        cell = styled(QWidget(), "QWidget { background: transparent; }")
        box = QHBoxLayout(cell)
        box.setContentsMargins(left, 0, 8, 0)
        box.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        box.addStretch()
        return cell

    def _render_upcoming(self, snapshot, as_of):
        self._clear_upcoming()
        self.upcoming_scroll.setVisible(bool(snapshot.upcoming))
        if snapshot.upcoming:
            self.upcoming_empty.clear()
        else:
            self.upcoming_empty.show_state(
                Icon.RINGER,
                COLORS["primary"],
                COLORS["surface_container"],
                "Không có lịch nhắc sắp tới",
                "Tạo lịch ở trang Nhắc nhở để nhận thông báo trước hạn.",
            )
        for index, reminder in enumerate(snapshot.upcoming):
            card = QFrame()
            card.setProperty("role", "reminder")
            box = QVBoxLayout(card)
            box.setContentsMargins(10, 8, 10, 8)
            box.setSpacing(4)
            top = QHBoxLayout()
            top.setSpacing(6)
            top.addWidget(icon_label(Icon.RINGER, 14, card, COLORS["text"]))
            title = QLabel(reminder.title, card)
            title.setProperty("role", "reminderTitle")
            title.setWordWrap(True)
            top.addWidget(title, 1)
            if reminder.record_code:
                chip = QLabel(reminder.record_code, card)
                chip.setProperty("role", "codeChip")
                top.addWidget(chip, 0, Qt.AlignmentFlag.AlignTop)
            text = QLabel(
                f"Hồ sơ {reminder.record_code} · {reminder.record_name}"
                if reminder.record_code
                else "Không liên kết hồ sơ",
                card,
            )
            text.setProperty("role", "reminderText")
            text.setWordWrap(True)
            moment = reminder.notify_at.astimezone(LOCAL_ZONE)
            day = relative_day(moment, as_of)
            when = QLabel(
                f"{moment:%d/%m/%Y %H:%M}" + (f"  ({day})" if day else ""), card
            )
            when.setProperty("role", "reminderTime")
            when.setProperty("today", day == "Hôm nay")
            line = QHBoxLayout()
            line.setSpacing(6)
            line.addWidget(icon_label(Icon.HISTORY, 12, card, COLORS["muted"]))
            line.addWidget(when, 1)
            box.addLayout(top)
            box.addWidget(text)
            box.addLayout(line)
            self.upcoming_list.insertWidget(index, card)
            self.upcoming_items.append(card)

    def _failed(self, _error):
        self.loading = False
        self.refresh_button.setEnabled(True)
        self.feedback.setText(
            "Không tải được tổng quan. Chọn Tải lại để thử lại; bạn vẫn có thể mở Hồ sơ hoặc Nhắc nhở."
        )
        self.feedback.show()
        self.attention_table.hide()
        self.upcoming_scroll.hide()
        for empty in (self.attention_empty, self.upcoming_empty):
            empty.show_state(
                Icon.INFO,
                COLORS["error"],
                "#fee2e2",
                "Chưa tải được dữ liệu",
                "Dữ liệu chưa tải được. Chọn Tải lại để thử lại.",
            )
