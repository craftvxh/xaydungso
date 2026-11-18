"""Display-only widgets for the records page: status filter, badge and detail pane."""

from datetime import datetime

from PyQt6.QtCore import QEvent, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPen
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    ScrollArea,
    TableItemDelegate,
    setCustomStyleSheet,
)
from qfluentwidgets.components.widgets.check_box import CheckBoxIcon

from xaydungso.domain.records import RecordStatus
from xaydungso.domain.reminders import LOCAL_ZONE
from xaydungso.presentation.icons import Icon, colored_icon
from xaydungso.presentation.theme import COLORS, qss, styled

DETAIL_WIDTH = 360
CHECK_SIZE = 16  # Design spec: 16px boxes, 4px radius, slate when checked.


class CompactCheckDelegate(TableItemDelegate):
    """Fluent table delegate drawing smaller checkboxes 16px into the cell."""

    def _drawCheckBox(self, painter, option, index):
        painter.save()
        state = Qt.CheckState(index.data(Qt.ItemDataRole.CheckStateRole))
        rect = QRectF(
            option.rect.x() + 16,
            option.rect.center().y() - CHECK_SIZE / 2 + 0.5,
            CHECK_SIZE,
            CHECK_SIZE,
        )
        if state == Qt.CheckState.Unchecked:
            painter.setPen(QPen(QColor("#94a3b8"), 1.5))
            painter.setBrush(QColor("#ffffff"))
            painter.drawRoundedRect(rect, 4, 4)
        else:
            painter.setPen(QColor(COLORS["primary_container"]))
            painter.setBrush(QColor(COLORS["primary_container"]))
            painter.drawRoundedRect(rect, 4, 4)
            icon = (
                CheckBoxIcon.ACCEPT
                if state == Qt.CheckState.Checked
                else CheckBoxIcon.PARTIAL_ACCEPT
            )
            icon.render(painter, rect.adjusted(1, 1, -1, -1))
        painter.restore()


def compact_checks(table):
    table.setItemDelegate(CompactCheckDelegate(table))


def compact_checkbox(checkbox):
    """Shrink a Fluent CheckBox indicator to the 16px design size."""
    # One sheet: Fluent replaces (not merges) custom sheets on each call.
    sheet = (
        "CheckBox { background: transparent; }"
        " CheckBox::indicator { width: 14px; height: 14px; }"
    )
    setCustomStyleSheet(checkbox, sheet, sheet)
    checkbox.setCheckedColor(
        QColor(COLORS["primary_container"]), QColor(COLORS["primary_container"])
    )
    return checkbox


def check_click(table, event, toggle):
    """Handle presses in the checkbox column; True means the event was used."""
    if event.type() not in (
        QEvent.Type.MouseButtonPress,
        QEvent.Type.MouseButtonDblClick,
    ):
        return False
    index = table.indexAt(event.position().toPoint())
    if not index.isValid() or index.column() != 0:
        return False
    if event.type() == QEvent.Type.MouseButtonPress:
        toggle(index.row(), 0)
    return True


def deadline_info(data, now=None):
    """Deadline text, a short remaining-time hint and whether it is overdue."""
    if not data.deadline_at:
        return "", "", False
    deadline = datetime.fromisoformat(data.deadline_at).astimezone(LOCAL_ZONE)
    text = deadline.strftime("%d/%m/%Y %H:%M")
    if data.status is RecordStatus.COMPLETE:
        return text, "", False
    now = now or datetime.now(LOCAL_ZONE)
    days = (deadline.date() - now.date()).days
    if deadline < now:
        return text, f"Quá hạn {-days:02d} ngày" if days < 0 else "Quá hạn", True
    return text, "Hôm nay" if days == 0 else f"Còn {days:02d} ngày", False


def icon_label(icon, size=16, parent=None, color=None):
    """A QLabel showing a Fluent icon pixmap (optionally recoloured)."""
    label = QLabel(parent)
    qicon = colored_icon(icon, color) if color else icon.icon()
    label.setPixmap(qicon.pixmap(QSize(size, size)))
    label.setFixedSize(size, size)
    return label


def badge_qss(status):
    done = status is RecordStatus.COMPLETE
    return qss(
        "QLabel { background: %s; color: %s; border-radius: 4px;"
        " padding: 2px 8px; font-size: 11px; font-weight: 500; }"
        % (("@done_bg", "@done_fg") if done else ("@pending_bg", "@pending_fg"))
    )


def status_text(status):
    return ("✓ " if status is RecordStatus.COMPLETE else "● ") + status.value


def status_badge(status, parent=None):
    """Coloured pill shown in the table and detail pane."""
    label = QLabel(status_text(status), parent)
    return styled(label, badge_qss(status))


class StatusFilter(QFrame):
    """Segmented Tất cả / Chưa hoàn thành / Đã hoàn thành control with counts."""

    currentIndexChanged = pyqtSignal(int)
    LABELS = ("Tất cả", *(item.value for item in RecordStatus))
    MARKS = ("", "●", "✓")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusFilter")
        styled(
            self,
            """
            QFrame#statusFilter { background: @surface_low; border: 1px solid @outline;
                border-radius: 8px; }
            QPushButton { background: transparent; border: 1px solid transparent;
                border-radius: 6px; }
            QPushButton:hover { background: @surface_container; }
            QPushButton:checked { background: @surface; border-color: @outline; }
            QLabel { background: transparent; color: @muted; font-size: 12px; }
            QLabel[checked="true"] { color: @text; font-weight: 600; }
            QLabel[role="mark"] { color: @secondary; font-size: 9px; }
            QLabel[role="mark"][done="true"] { color: @primary; font-size: 12px; }
            QLabel[role="count"] { background: @surface_container; border-radius: 8px;
                padding: 0 6px; font-size: 11px; }
            QLabel[role="count"][checked="true"] { background: @secondary_container;
                color: @text; }
            """,
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)
        self.group = QButtonGroup(self)
        self.buttons, self.labels, self.counts = [], [], []
        for index, text in enumerate(self.LABELS):
            button = QPushButton(self)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            inner = QHBoxLayout(button)
            inner.setContentsMargins(10, 3, 8, 3)
            inner.setSpacing(6)
            parts = []
            if self.MARKS[index]:
                mark = QLabel(self.MARKS[index], button)
                mark.setProperty("role", "mark")
                mark.setProperty("done", index == 2)
                parts.append(mark)
            label = QLabel(text, button)
            count = QLabel("0", button)
            count.setProperty("role", "count")
            parts += [label, count]
            for part in parts:
                part.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                inner.addWidget(part)
            self.group.addButton(button, index)
            layout.addWidget(button)
            self.buttons.append(button)
            self.labels.append((label, count))
        self.buttons[0].setChecked(True)
        self.group.idClicked.connect(self._clicked)
        self._restyle()

    def _clicked(self, index):
        self._restyle()
        self.currentIndexChanged.emit(index)

    def _restyle(self):
        for button, parts in zip(self.buttons, self.labels, strict=True):
            for part in parts:
                part.setProperty("checked", button.isChecked())
                part.style().unpolish(part)
                part.style().polish(part)
            button.setMinimumSize(button.layout().sizeHint())

    def currentIndex(self):
        return self.group.checkedId()

    def setCurrentIndex(self, index):
        if index != self.currentIndex():
            self.buttons[index].setChecked(True)
            self._clicked(index)

    def status(self):
        index = self.currentIndex()
        return list(RecordStatus)[index - 1] if index > 0 else None

    def text(self, index):
        label, count = self.labels[index]
        return f"{label.text()}  {count.text()}"

    def set_counts(self, counts):
        for (_, label), count in zip(self.labels, counts, strict=True):
            label.setText(str(count))
        self._restyle()


class Pager(QWidget):
    """'Trang x / n' with previous/next and up to five page-number buttons."""

    pageChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        styled(
            self,
            """
            QLabel { background: transparent; color: @muted; font-size: 11px; }
            QPushButton { background: @surface; color: @text; font-size: 11px;
                border: 1px solid @outline_soft; border-radius: 4px; }
            QPushButton:hover { background: @surface_container; }
            QPushButton:checked { background: @primary; color: @on_primary;
                border-color: @primary; font-weight: 700; }
            QPushButton:disabled { color: @outline; background: @surface; }
            """,
        )
        self.page, self.pages = 0, 1
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.label = QLabel(self)
        layout.addWidget(self.label)
        layout.addSpacing(4)
        self.previous = self._button("‹", lambda: self._go(self.page - 1))
        self.previous.setToolTip("Trang trước")
        layout.addWidget(self.previous)
        self.numbers = QHBoxLayout()
        self.numbers.setSpacing(4)
        layout.addLayout(self.numbers)
        self.next = self._button("›", lambda: self._go(self.page + 1))
        self.next.setToolTip("Trang sau")
        layout.addWidget(self.next)
        self.set(0, 1)

    def _button(self, text, action):
        button = QPushButton(text, self)
        button.setFixedSize(24, 24)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(action)
        return button

    def _go(self, page):
        if 0 <= page < self.pages and page != self.page:
            self.pageChanged.emit(page)

    def set(self, page, pages):
        self.page, self.pages = page, pages
        self.label.setText(f"Trang {page + 1} / {pages}")
        self.previous.setEnabled(page > 0)
        self.next.setEnabled(page < pages - 1)
        while self.numbers.count():
            self.numbers.takeAt(0).widget().deleteLater()
        first = max(0, min(page - 2, pages - 5))
        for number in range(first, min(pages, first + 5)):
            button = self._button(str(number + 1), lambda _, n=number: self._go(n))
            button.setCheckable(True)
            button.setChecked(number == page)
            self.numbers.addWidget(button)


class RecordDetail(QFrame):
    """Read-only grouped view of the selected record."""

    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("recordDetail")
        self.setFixedWidth(DETAIL_WIDTH)
        styled(
            self,
            """
            QFrame#recordDetail { background: @surface; border: 1px solid @outline;
                border-radius: 8px; }
            QLabel { background: transparent; color: @text; font-size: 12px; }
            QLabel[role="title"] { font-size: 14px; font-weight: 600; }
            QLabel[role="code"] { background: @primary_container; color: @on_primary;
                border-radius: 4px; padding: 1px 6px; font-family: Consolas;
                font-weight: 700; font-size: 11px; }
            QLabel[role="group"] { color: @muted; font-size: 10px; font-weight: 700; }
            QLabel[role="key"] { color: @muted; font-size: 11px; }
            QLabel[role="value"] { font-weight: 600; font-size: 11px; }
            QLabel[role="hint"] { background: @surface_container; color: @primary;
                border-radius: 4px; padding: 0 6px; font-size: 10px; font-weight: 500; }
            QLabel[role="hint"][overdue="true"] { background: #fee2e2; color: @error; }
            QLabel[role="notes"] { background: @surface_low; border: 1px solid @outline;
                border-radius: 4px; padding: 8px; font-size: 11px; }
            QLabel[role="empty"] { color: @muted; }
            QFrame[role="card"] { background: @surface_faint; border: 1px solid @outline_soft;
                border-radius: 8px; }
            QFrame[role="rule"] { background: @outline_soft; max-height: 1px; border: none; }
            QWidget#detailBody, QScrollArea { background: transparent; border: none; }
            QPushButton#closeDetail { background: transparent; border: none;
                border-radius: 4px; }
            QPushButton#closeDetail:hover { background: @surface_container; }
            """,
        )
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(icon_label(Icon.DOCUMENT, 18, self, COLORS["primary"]))
        title = QLabel("Chi tiết hồ sơ", self)
        title.setProperty("role", "title")
        self.code = QLabel(self)
        self.code.setProperty("role", "code")
        self.close_button = QPushButton(self)
        self.close_button.setObjectName("closeDetail")
        self.close_button.setIcon(Icon.CLOSE.icon())
        self.close_button.setIconSize(QSize(12, 12))
        self.close_button.setFixedSize(24, 24)
        self.close_button.setToolTip("Đóng chi tiết")
        self.close_button.clicked.connect(self.closed.emit)
        header.addWidget(title)
        header.addWidget(self.code)
        header.addStretch()
        header.addWidget(self.close_button)
        outer.addLayout(header)
        rule = QFrame(self)
        rule.setProperty("role", "rule")
        outer.addWidget(rule)

        self.empty = QLabel(
            "Chọn một hồ sơ trong bảng để xem chi tiết.\nNhấp đúp để sửa nhanh.",
            self,
        )
        self.empty.setProperty("role", "empty")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setWordWrap(True)
        outer.addWidget(self.empty, 1)

        self.scroll = ScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("detailBody")
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(0, 0, 4, 0)
        self.body.setSpacing(6)
        self.values = {}
        self._group(
            "1. THÔNG TIN HỒ SƠ",
            [
                ("applicant_name", "Họ và tên"),
                ("phone", "Số điện thoại"),
                ("address", "Địa chỉ"),
            ],
        )
        self._group(
            "2. QUY TRÌNH & THỜI GIAN XỬ LÝ",
            [
                ("received_at", "Ngày tiếp nhận"),
                ("deadline", "Hạn xử lý"),
                ("return_appointment_date", "Ngày hẹn trả"),
                ("handover_at", "Thời gian giao nhận"),
            ],
        )
        results = self._group(
            "3. KẾT QUẢ & TÌNH TRẠNG",
            [
                ("status", "Trạng thái hồ sơ"),
                ("drawing_stamp_status", "Bản vẽ đóng dấu"),
                ("permit_stamp_status", "Giấy phép đóng dấu"),
                ("signature_status", "Chữ ký"),
                ("recipient_name", "Người ký nhận"),
            ],
        )
        notes_key = QLabel("Ghi chú", body)
        notes_key.setProperty("role", "key")
        self.notes = QLabel(body)
        self.notes.setProperty("role", "notes")
        self.notes.setWordWrap(True)
        self.notes.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        results.addWidget(notes_key, results.rowCount(), 0, 1, 2)
        results.addWidget(self.notes, results.rowCount(), 0, 1, 2)
        self.body.addStretch()
        self.scroll.setWidget(body)
        outer.addWidget(self.scroll, 1)

        footer_rule = QFrame(self)
        footer_rule.setProperty("role", "rule")
        outer.addWidget(footer_rule)
        self.actions = QHBoxLayout()
        self.actions.setSpacing(8)
        outer.addLayout(self.actions)
        self.show_record(None)

    def _group(self, title, rows):
        heading = QLabel(title)
        heading.setProperty("role", "group")
        card = QFrame()
        card.setProperty("role", "card")
        grid = QGridLayout(card)
        grid.setContentsMargins(10, 8, 10, 8)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(7)
        grid.setColumnStretch(1, 1)
        line = 0
        for name, label in rows:
            key = QLabel(label, card)
            key.setProperty("role", "key")
            value = QLabel(card)
            value.setProperty("role", "value")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            if name == "address":
                # Long addresses read as a block under their label (as in the design).
                value.setWordWrap(True)
                grid.addWidget(key, line, 0, 1, 2)
                grid.addWidget(value, line + 1, 0, 1, 2)
                line += 2
                self.values[name] = value
                continue
            value.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            value.setWordWrap(name not in ("deadline", "status"))
            holder = QHBoxLayout()
            holder.setSpacing(6)
            holder.addStretch()
            # The status badge hugs its text; other values take the free width.
            holder.addWidget(value, 0 if name == "status" else 1)
            if name == "deadline":
                self.deadline_hint = QLabel(card)
                self.deadline_hint.setProperty("role", "hint")
                holder.addWidget(self.deadline_hint)
            grid.addWidget(key, line, 0)
            grid.addLayout(holder, line, 1)
            line += 1
            self.values[name] = value
        self.body.addSpacing(4)
        self.body.addWidget(heading)
        self.body.addWidget(card)
        return grid

    def add_action(self, button, stretch=0):
        self.actions.addWidget(button, stretch)

    def show_record(self, record):
        self.empty.setVisible(record is None)
        self.scroll.setVisible(record is not None)
        self.code.setVisible(record is not None)
        self.close_button.setVisible(record is not None)
        if record is None:
            return
        data = record.data
        self.code.setText(data.record_code)
        deadline, hint, overdue = deadline_info(data)
        texts = {
            "applicant_name": data.applicant_name,
            "phone": data.phone,
            "address": data.address,
            "received_at": data.received_at,
            "deadline": deadline,
            "return_appointment_date": data.return_appointment_date,
            "handover_at": data.handover_at,
            "status": status_text(data.status),
            "drawing_stamp_status": "Có" if data.drawing_stamp_status else "Chưa",
            "permit_stamp_status": "Có" if data.permit_stamp_status else "Chưa",
            "signature_status": "Đã ký" if data.signature_status else "Chưa ký",
            "recipient_name": data.recipient_name,
        }
        for name, text in texts.items():
            self.values[name].setText(text or "—")
        styled(self.values["status"], badge_qss(data.status))
        self.values["deadline"].setStyleSheet(
            f"color: {COLORS['error']};" if overdue else ""
        )
        self.deadline_hint.setText(f"({hint})" if hint else "")
        self.deadline_hint.setVisible(bool(hint))
        self.deadline_hint.setProperty("overdue", overdue)
        self.deadline_hint.style().unpolish(self.deadline_hint)
        self.deadline_hint.style().polish(self.deadline_hint)
        self.notes.setText(data.notes or "Không có ghi chú.")
