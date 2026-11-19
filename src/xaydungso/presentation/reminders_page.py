"""Reminders page laid out like the Stitch "Nhắc nhở" export."""

from datetime import datetime

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CheckBox,
    ComboBox,
    PrimaryPushButton,
    PushButton,
    SearchLineEdit,
    TableWidget,
    ToolButton,
    TransparentPushButton,
    TransparentToolButton,
    setCustomStyleSheet,
)

from xaydungso.application.ports import NotificationError
from xaydungso.domain.records import ValidationError, format_duration
from xaydungso.domain.reminders import LOCAL_ZONE
from xaydungso.presentation.confirm import ConfirmBox
from xaydungso.presentation.icons import Icon
from xaydungso.presentation.motion import unroll_height
from xaydungso.presentation.record_widgets import (
    Pager,
    check_click,
    compact_checkbox,
    compact_checks,
    icon_label,
)
from xaydungso.presentation.reminder_dialog import ReminderDialog
from xaydungso.presentation.theme import (
    COLORS,
    accent_button,
    qss,
    set_mono,
    styled,
)

# Overall status of one reminder, derived from its two delivery channels.
PENDING, SENT, FAILED, CANCELLED = "Chờ gửi", "Đã gửi", "Gửi lỗi", "Đã hủy"
BADGES = {
    PENDING: ("#fef3c7", "#b45309"),
    SENT: ("#dcfce7", "#15803d"),
    FAILED: ("#fee2e2", "#b91c1c"),
    CANCELLED: ("#eceef3", "#5b616e"),
}
CHANNELS = (("telegram", "Telegram"), ("windows", "Windows"))
STATE_LABELS = {
    "pending": "Chờ gửi",
    "sending": "Đang gửi",
    "sent": "Đã gửi",
    "failed": "Lỗi / chờ thử lại",
}
STATE_COLOURS = {
    "pending": "#b45309",
    "sending": "#1d4ed8",
    "sent": "#15803d",
    "failed": "#b91c1c",
}

SHEET = """
QWidget#reminders { background: @page; }
QLabel { background: transparent; color: @text; font-size: @fs_body; }
QLabel#remTitle { font-size: @fs_page; font-weight: 700; }
QLabel#remSubtitle, QLabel#remHelp { color: @muted; font-size: @fs_small; }
QLabel#workerChip { border-radius: 8px; padding: 3px 10px; font-size: @fs_tiny;
    font-weight: 600; background: #eceef3; color: #5b616e; }
QLabel#workerChip[running="true"] { background: #dcfce7; color: #15803d; }
QFrame[role="stat"], QFrame#remToolbar, QFrame#remCard { background: @surface;
    border: 1px solid @outline_soft; border-radius: 8px; }
QLabel[role="statTitle"] { color: @muted; font-size: @fs_small; }
QLabel[role="statValue"] { font-size: @fs_stat; font-weight: 700; }
QLabel[role="statIcon"] { border-radius: 20px; }
QLabel#remCount { color: @muted; font-size: @fs_small; }
QLabel[role="main"] { font-size: @fs_body; font-weight: 600; }
QLabel[role="sub"] { color: @muted; font-size: @fs_small; }
QLabel[role="main"][mono="true"], QLabel[role="sub"][mono="true"] {
    font-size: @fs_mono; }
QFrame#remFooter { background: @surface_low; border: none;
    border-top: 1px solid @outline_soft; border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px; }
QLabel#remFooterText { color: @muted; font-size: @fs_small; }
QFrame#remBulk { background: @surface_container; border: none;
    border-bottom: 1px solid @outline_soft; border-top-left-radius: 8px;
    border-top-right-radius: 8px; }
QLabel#remBulkText { font-size: @fs_body; font-weight: 600; }
"""


def first_line(text):
    """First non-empty line: multi-line template messages stay one table line."""
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


class ElidedLabel(QLabel):
    """Single-line label that shortens with "…" to whatever width it gets."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.full_text = text
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setText(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        elided = self.fontMetrics().elidedText(
            self.full_text, Qt.TextElideMode.ElideRight, max(0, self.width())
        )
        if elided != self.text():
            self.setText(elided)


def reminder_status(reminder):
    if reminder["cancelled"]:
        return CANCELLED
    states = [reminder["deliveries"][key]["state"] for key, _ in CHANNELS]
    if "failed" in states:
        return FAILED
    if all(state == "sent" for state in states):
        return SENT
    return PENDING


def local(value):
    return datetime.fromisoformat(value).astimezone(LOCAL_ZONE)


class RemindersPage(QWidget):
    changed = pyqtSignal()
    open_templates = pyqtSignal()
    PAGE_SIZE = 14
    COLUMNS = (
        ("", 40),
        ("MÃ HỒ SƠ", 120),
        ("CHỦ ĐẦU TƯ / CÔNG TRÌNH", 0),
        ("KÊNH GỬI", 150),
        ("NỘI DUNG THÔNG BÁO", 0),
        ("THỜI GIAN DỰ KIẾN", 140),
        ("TRẠNG THÁI", 110),
        ("THAO TÁC", 124),
    )
    STATUS_FILTERS = ("Tất cả trạng thái", PENDING, SENT, FAILED, CANCELLED)

    def __init__(
        self, service, records, background, runner, parent=None, templates=None
    ):
        super().__init__(parent)
        self.setObjectName("reminders")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        styled(self, SHEET)
        self.service, self.records_service, self.background = (
            service,
            records,
            background,
        )
        self.runner = runner
        self.templates_service = templates
        self.reminders, self.visible = [], []
        self.checked = set()
        self.records = {}
        self.page = 0
        self.newest_first = True
        self.editor = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Header: title, worker state and actions.
        header = QHBoxLayout()
        header.setSpacing(8)
        titles = QVBoxLayout()
        titles.setSpacing(2)
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(icon_label(Icon.RINGER, 22, self, COLORS["text"]))
        title = QLabel("Nhắc nhở", self)
        title.setObjectName("remTitle")
        self.worker_status = QLabel(self)
        self.worker_status.setObjectName("workerChip")
        row.addWidget(title)
        row.addWidget(self.worker_status)
        row.addStretch()
        subtitle = QLabel(
            "Lịch nhắc theo hạn xử lý, gửi qua Telegram và thông báo Windows", self
        )
        subtitle.setObjectName("remSubtitle")
        titles.addLayout(row)
        titles.addWidget(subtitle)
        header.addLayout(titles, 1)
        self.start_button = PushButton(Icon.PLAY, "Bật nhắc nền", self)
        self.stop_button = PushButton(Icon.PAUSE, "Dừng nhắc nền", self)
        self.settings_button = PushButton(Icon.SETTING, "Cấu hình", self)
        self.settings_button.setToolTip("Cấu hình nội dung thông báo (mẫu lịch nhắc)")
        self.add_button = PrimaryPushButton(Icon.ADD, "Tạo nhắc nhở", self)
        accent_button(self.add_button)
        for button in (
            self.start_button,
            self.stop_button,
            self.settings_button,
            self.add_button,
        ):
            header.addWidget(button, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        # Three status counters.
        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.stat_values = {}
        for status, icon in (
            (PENDING, Icon.HISTORY),
            (SENT, Icon.ACCEPT),
            (FAILED, Icon.INFO),
        ):
            background, colour = BADGES[status]
            card = QFrame(self)
            card.setProperty("role", "stat")
            box = QHBoxLayout(card)
            box.setContentsMargins(16, 12, 16, 12)
            texts = QVBoxLayout()
            texts.setSpacing(2)
            caption = QLabel(status, card)
            caption.setProperty("role", "statTitle")
            value = QLabel("—", card)
            value.setProperty("role", "statValue")
            texts.addWidget(caption)
            texts.addWidget(value)
            tile = icon_label(icon, 18, card, colour)
            tile.setProperty("role", "statIcon")
            tile.setFixedSize(40, 40)
            tile.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tile.setStyleSheet(f"background: {background}; border-radius: 20px;")
            box.addLayout(texts, 1)
            box.addWidget(tile)
            stats.addWidget(card, 1)
            self.stat_values[status] = value
        layout.addLayout(stats)

        # Toolbar: search, status filter, sort, count and refresh.
        toolbar = QFrame(self)
        toolbar.setObjectName("remToolbar")
        bar = QHBoxLayout(toolbar)
        bar.setContentsMargins(12, 8, 12, 8)
        bar.setSpacing(10)
        self.search = SearchLineEdit(toolbar)
        self.search.setPlaceholderText("Tìm kiếm lời nhắc, mã hồ sơ, họ tên...")
        self.search.setMinimumWidth(260)
        self.search.setMaximumWidth(340)
        self.status_filter = ComboBox(toolbar)
        self.status_filter.addItems(self.STATUS_FILTERS)
        self.sort_button = PushButton(Icon.SCROLL, "Mới nhất", toolbar)
        self.sort_button.setToolTip("Sắp xếp theo thời gian dự kiến gửi")
        self.count = QLabel(toolbar)
        self.count.setObjectName("remCount")
        self.refresh_button = ToolButton(Icon.SYNC, toolbar)
        self.refresh_button.setToolTip("Tải lại")
        bar.addWidget(self.search, 1)
        bar.addWidget(self.status_filter)
        bar.addWidget(self.sort_button)
        bar.addStretch()
        bar.addWidget(self.count)
        bar.addWidget(self.refresh_button)
        layout.addWidget(toolbar)

        # Table card with footer pager.
        card = QFrame(self)
        card.setObjectName("remCard")
        card_box = QVBoxLayout(card)
        card_box.setContentsMargins(1, 1, 1, 0)
        card_box.setSpacing(0)
        self.bulk_bar = QFrame(card)
        self.bulk_bar.setObjectName("remBulk")
        bulk = QHBoxLayout(self.bulk_bar)
        bulk.setContentsMargins(12, 5, 8, 5)
        bulk.setSpacing(6)
        self.bulk_text = QLabel(self.bulk_bar)
        self.bulk_text.setObjectName("remBulkText")
        self.bulk_delete_button = TransparentPushButton(
            Icon.DELETE, "Xóa", self.bulk_bar
        )
        self.bulk_delete_button.setToolTip("Xóa vĩnh viễn các lịch đã chọn")
        self.bulk_clear_button = TransparentPushButton("Bỏ chọn", self.bulk_bar)
        bulk.addWidget(self.bulk_text)
        bulk.addStretch()
        bulk.addWidget(self.bulk_delete_button)
        bulk.addWidget(self.bulk_clear_button)
        self.bulk_bar.hide()
        card_box.addWidget(self.bulk_bar)
        self.reminders_table = self._table(card)
        # Select-all box for the visible page, drawn over header section 0.
        self.check_all = compact_checkbox(
            CheckBox(self.reminders_table.horizontalHeader())
        )
        self.check_all.setTristate(True)
        self.check_all.setFixedSize(22, 22)
        self.check_all.setToolTip("Chọn / bỏ chọn tất cả lịch trên trang")
        card_box.addWidget(self.reminders_table, 1)
        footer = QFrame(card)
        footer.setObjectName("remFooter")
        foot = QHBoxLayout(footer)
        foot.setContentsMargins(12, 7, 12, 7)
        self.footer_text = QLabel(footer)
        self.footer_text.setObjectName("remFooterText")
        help_text = QLabel(
            "Giờ Việt Nam · Gửi trong 07:00–23:00 · Lịch bỏ lỡ sẽ gửi bù · "
            "Máy phải đang bật",
            footer,
        )
        help_text.setObjectName("remHelp")
        self.pager = Pager(footer)
        foot.addWidget(self.footer_text)
        foot.addSpacing(16)
        foot.addWidget(help_text)
        foot.addStretch()
        foot.addWidget(self.pager)
        card_box.addWidget(footer)
        layout.addWidget(card, 1)
        self.feedback = QLabel(self)
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)

        self.add_button.clicked.connect(lambda: self.edit())
        self.settings_button.clicked.connect(self.open_templates.emit)
        self.refresh_button.clicked.connect(self.refresh)
        self.start_button.clicked.connect(
            lambda: self.worker_action(self.background.start)
        )
        self.stop_button.clicked.connect(
            lambda: self.worker_action(self.background.stop)
        )
        self.search.textChanged.connect(lambda _: self._go(0))
        self.status_filter.currentIndexChanged.connect(lambda _: self._go(0))
        self.sort_button.clicked.connect(self._toggle_sort)
        self.pager.pageChanged.connect(self._go)
        self.reminders_table.cellDoubleClicked.connect(
            lambda row, column: self._edit_row(row) if column else None
        )
        self.reminders_table.viewport().installEventFilter(self)
        self.reminders_table.horizontalHeader().sectionClicked.connect(
            self._header_clicked
        )
        self.check_all.clicked.connect(lambda: self._header_clicked(0))
        self.bulk_delete_button.clicked.connect(self._delete_checked)
        self.bulk_clear_button.clicked.connect(self._clear_checked)
        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(
            lambda: self.refresh() if not self.runner.busy else None
        )
        self.timer.start()
        self.refresh()

    def _table(self, parent):
        table = TableWidget(parent)
        table.setColumnCount(len(self.COLUMNS))
        table.setHorizontalHeaderLabels([title for title, _ in self.COLUMNS])
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().hide()
        table.verticalHeader().setDefaultSectionSize(54)
        table.setBorderVisible(False)
        table.setAlternatingRowColors(False)
        compact_checks(table)
        table.setWordWrap(False)
        table.setShowGrid(True)
        header = table.horizontalHeader()
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        for column, (_, width) in enumerate(self.COLUMNS):
            if width:
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
                header.resizeSection(column, width)
            else:
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        sheet = qss(
            "QTableView { gridline-color: @outline_soft; }"
            " QHeaderView::section { background-color: @surface_low; color: @muted;"
            " font-family: @font; font-size: @fs_tiny; font-weight: 600; border: none;"
            " border-right: 1px solid @outline_soft;"
            " border-bottom: 1px solid @outline_soft; padding-left: 12px; }"
        )
        setCustomStyleSheet(table, sheet, sheet)
        return table

    # Data -------------------------------------------------------------------------

    def refresh(self, *_):
        def load():
            reminders = self.service.list()
            records = {record.id: record for record in self.records_service.list()}
            return reminders, records

        self.runner.submit(load, self._render, self.show_error)

    def _render(self, loaded):
        self.reminders, self.records = loaded
        self.checked &= {reminder["id"] for reminder in self.reminders}
        counts = {status: 0 for status in self.stat_values}
        for reminder in self.reminders:
            status = reminder_status(reminder)
            if status in counts:
                counts[status] += 1
        for status, value in self.stat_values.items():
            value.setText(str(counts[status]))
        self._show()
        try:
            running = self.background.running()
            self.worker_status.setText(
                "●  Nhắc nền đang chạy" if running else "●  Nhắc nền đang dừng"
            )
            self.worker_status.setProperty("running", running)
            self.worker_status.setToolTip(
                ""
                if running
                else "Bật nhắc nền để xử lý các lịch đến hạn; tiến trình chạy tiếp khi đóng cửa sổ."
            )
            self.start_button.setVisible(not running)
            self.stop_button.setVisible(running)
        except OSError:
            self.worker_status.setText("●  Không kiểm tra được nhắc nền")
            self.worker_status.setProperty("running", False)
        self.worker_status.style().unpolish(self.worker_status)
        self.worker_status.style().polish(self.worker_status)

    def _matches(self, reminder):
        index = self.status_filter.currentIndex()
        if index > 0 and reminder_status(reminder) != self.STATUS_FILTERS[index]:
            return False
        needle = self.search.text().strip().casefold()
        if not needle:
            return True
        record = self.records.get(reminder.get("record_id"))
        haystack = [reminder["title"]]
        if record is not None:
            haystack += [record.data.record_code, record.data.applicant_name]
        return any(needle in text.casefold() for text in haystack)

    def _toggle_sort(self):
        self.newest_first = not self.newest_first
        self.sort_button.setText("Mới nhất" if self.newest_first else "Cũ nhất")
        self._go(0)

    def _go(self, page):
        self.page = page
        self._show()

    def _show(self):
        matching = sorted(
            (item for item in self.reminders if self._matches(item)),
            key=lambda item: (item["notify_at"], item["id"]),
            reverse=self.newest_first,
        )
        pages = max(1, -(-len(matching) // self.PAGE_SIZE))
        self.page = min(self.page, pages - 1)
        start = self.page * self.PAGE_SIZE
        self.visible = matching[start : start + self.PAGE_SIZE]
        table = self.reminders_table
        table.clearSelection()
        table.setRowCount(len(self.visible))
        for row, reminder in enumerate(self.visible):
            self._fill(row, reminder)
        span = f"{start + 1} - {start + len(self.visible)}" if self.visible else "0"
        self.footer_text.setText(f"Hiển thị {span} trên tổng số {len(matching)} lịch")
        self.count.setText(f"{len(matching)} lời nhắc")
        self.pager.set(self.page, pages)
        self._update_checks()

    def _fill(self, row, reminder):
        table = self.reminders_table
        record = self.records.get(reminder.get("record_id"))
        code = QLabel(record.data.record_code if record else "—")
        code.setStyleSheet(
            qss("color: @primary; font-family: @mono; font-size: @fs_mono;")
            + " font-weight: 700;"
        )
        who = (
            (record.data.applicant_name, record.data.address or "Chưa có địa chỉ")
            if record
            else ("Không liên kết hồ sơ", "Lịch độc lập")
        )
        channels = [
            (
                f"<span style='color:{STATE_COLOURS[state]}'>●</span> {label} · "
                f"{STATE_LABELS[state]}"
            )
            for key, label in CHANNELS
            for state in [reminder["deliveries"][key]["state"]]
        ]
        errors = "\n".join(
            f"{label}: {reminder['deliveries'][key]['last_error']}"
            for key, label in CHANNELS
            if reminder["deliveries"][key]["last_error"]
        )
        lead = format_duration(reminder.get("lead_seconds")) or "Lịch cũ"
        deadline = local(reminder["deadline_at"])
        detail = f"Báo trước {lead} · Hạn {deadline:%d/%m/%Y %H:%M}"
        notify = local(reminder["notify_at"])
        status = reminder_status(reminder)
        cells = (
            self._stack([code]),
            self._stack(self._lines(*who)),
            self._stack([self._rich(line) for line in channels], errors),
            self._stack(
                self._lines(first_line(reminder["title"]), detail),
                reminder["title"] + "\n\n" + detail,  # Full message on hover.
            ),
            self._stack(
                [
                    set_mono(label)
                    for label in self._lines(f"{notify:%d/%m/%Y}", f"{notify:%H:%M}")
                ]
            ),
            self._stack([self._badge(status)]),
            self._actions(reminder, status),
        )
        check = QTableWidgetItem()
        # Drawn by Fluent's delegate; toggled in _cell_clicked, not by Qt.
        check.setFlags(check.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
        check.setCheckState(Qt.CheckState.Unchecked)
        table.setItem(row, 0, check)
        for column, cell in enumerate(cells, 1):
            table.setItem(row, column, QTableWidgetItem())
            table.setCellWidget(row, column, cell)

    # Cell builders ---------------------------------------------------------------

    @staticmethod
    def _lines(main, sub):
        # Exactly two single-line labels per cell keeps every row the same height.
        top = ElidedLabel(main)
        top.setProperty("role", "main")
        bottom = ElidedLabel(sub)
        bottom.setProperty("role", "sub")
        return [top, bottom]

    @staticmethod
    def _rich(text):
        label = QLabel(text)
        label.setProperty("role", "sub")
        label.setTextFormat(Qt.TextFormat.RichText)
        return label

    @staticmethod
    def _badge(status):
        background, colour = BADGES[status]
        label = QLabel(status)
        label.setStyleSheet(
            f"background: {background}; color: {colour}; border-radius: 4px;"
            + qss(" padding: 2px 8px; font-size: @fs_tiny; font-weight: 600;")
        )
        return label

    def _stack(self, widgets, tooltip=""):
        cell = styled(QWidget(), "QWidget { background: transparent; }")
        box = QVBoxLayout(cell)
        box.setContentsMargins(12, 4, 8, 4)
        box.setSpacing(1)
        box.addStretch()
        for widget in widgets:
            widget.setParent(cell)
            if isinstance(widget, ElidedLabel):
                box.addWidget(widget)  # Full cell width so it can elide.
            else:
                box.addWidget(widget, 0, Qt.AlignmentFlag.AlignLeft)
        box.addStretch()
        cell.setToolTip(tooltip)
        return cell

    def _actions(self, reminder, status):
        cell = styled(QWidget(), "QWidget { background: transparent; }")
        box = QHBoxLayout(cell)
        box.setContentsMargins(8, 0, 8, 0)
        box.setSpacing(2)
        editable = status in (PENDING, FAILED) and not any(
            reminder["deliveries"][key]["state"] in ("sent", "sending")
            for key, _ in CHANNELS
        )
        for icon, tip, enabled, action in (
            (Icon.EDIT, "Sửa lịch chưa gửi", editable, self.edit),
            (Icon.CLOSE, "Hủy lịch", status != CANCELLED, self.cancel),
            (Icon.DELETE, "Xóa lịch vĩnh viễn", True, self.delete),
        ):
            button = TransparentToolButton(icon, cell)
            button.setIconSize(QSize(14, 14))
            button.setToolTip(tip if enabled else f"{tip} (không khả dụng)")
            button.setEnabled(enabled)
            button.clicked.connect(lambda _, r=reminder, a=action: a(reminder=r))
            box.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
        box.addStretch()
        return cell

    # Actions ---------------------------------------------------------------------

    def show_error(self, error):
        self.feedback.setText(
            str(error)
            if isinstance(error, (ValidationError, NotificationError))
            else "Không thể thực hiện. Vui lòng kiểm tra file/quyền truy cập và thử lại."
        )

    def selected(self):
        rows = self.reminders_table.selectionModel().selectedRows()
        row = rows[0].row() if rows else -1
        return self.visible[row] if 0 <= row < len(self.visible) else None

    def _edit_row(self, row):
        if 0 <= row < len(self.visible):
            self.edit(reminder=self.visible[row])

    def edit_selected(self):
        reminder = self.selected()
        if reminder:
            self.edit(reminder=reminder)

    def edit(self, record=None, reminder=None):
        def load():
            templates = self.templates_service.list() if self.templates_service else []
            return self.records_service.list(), templates

        self.runner.submit(
            load,
            lambda loaded: self._open_editor(*loaded, record, reminder),
            self.show_error,
        )

    def _open_editor(self, records, templates, record, reminder):
        dialog = ReminderDialog(
            records,
            reminder=reminder,
            record=record,
            parent=self.window(),
            templates=templates,
        )
        self.editor = dialog

        def success(result):
            dialog.set_saving(False)
            dialog.accept()
            self.feedback.setText(
                f"Đã lưu lịch. Giờ gửi: {result.notify_at:%d/%m/%Y %H:%M:%S}. Bật nhắc nền để gửi."
            )
            if dialog.enable_background.isChecked():

                def started(_):
                    self.feedback.setText(
                        f"Đã lưu lịch, nhắc nền đã bật. Giờ gửi: {result.notify_at:%d/%m/%Y %H:%M:%S}."
                    )
                    self.refresh()

                def start_failed(error):
                    self.feedback.setText(
                        "Lịch đã lưu nhưng không bật được nhắc nền. Nhấn Bật nhắc nền để thử lại; kiểm tra reminders.log trong thư mục dữ liệu."
                    )
                    self.refresh()

                self.runner.submit(self.background.start, started, start_failed)
            self.refresh()
            self.changed.emit()

        def failure(error):
            dialog.set_saving(False)
            dialog.error.setText(
                str(error)
                if isinstance(error, ValidationError)
                else "Không lưu được lịch. Hãy thử lại."
            )

        dialog.submitted.connect(
            lambda values: self.runner.submit(
                lambda: self.service.save(
                    **values, reminder_id=reminder["id"] if reminder else None
                ),
                success,
                failure,
            )
        )
        dialog.setModal(True)
        dialog.show()

    def cancel(self, reminder=None):
        reminder = reminder or self.selected()
        if not reminder:
            return
        confirmation = ConfirmBox(
            "Hủy lịch nhắc?",
            "Các kênh chưa gửi sẽ không tiếp tục gửi. Kết quả đã gửi vẫn được giữ.",
            self.window(),
        )
        confirmation.yesButton.setText("Hủy lịch")
        confirmation.cancelButton.setText("Giữ lịch")
        if confirmation.exec():
            self.runner.submit(
                lambda: self.service.cancel(reminder["id"]),
                self._changed,
                self.show_error,
            )

    def cancel_selected(self):
        self.cancel()

    # Checkboxes and permanent deletion --------------------------------------------

    def eventFilter(self, watched, event):
        if watched is self.reminders_table.viewport() and check_click(
            self.reminders_table, event, self._cell_clicked
        ):
            return True  # Ticking a box must not select the row.
        return super().eventFilter(watched, event)

    def _cell_clicked(self, row, column):
        if column == 0 and 0 <= row < len(self.visible):
            self.checked ^= {self.visible[row]["id"]}
            self._update_checks()

    def _header_clicked(self, column):
        if column == 0 and self.visible:
            ids = {reminder["id"] for reminder in self.visible}
            if ids <= self.checked:
                self.checked -= ids
            else:
                self.checked |= ids
            self._update_checks()

    def _clear_checked(self):
        self.checked.clear()
        self._update_checks()

    def _update_checks(self):
        header = self.reminders_table.horizontalHeader()
        x = header.sectionViewportPosition(0) + 15  # Row boxes start 16px in.
        self.check_all.move(x, (header.height() - self.check_all.height()) // 2)
        ids = {reminder["id"] for reminder in self.visible}
        for row, reminder in enumerate(self.visible):
            item = self.reminders_table.item(row, 0)
            if item is not None:
                item.setCheckState(
                    Qt.CheckState.Checked
                    if reminder["id"] in self.checked
                    else Qt.CheckState.Unchecked
                )
        on_page = len(ids & self.checked)
        self.check_all.setCheckState(
            Qt.CheckState.Checked
            if ids and on_page == len(ids)
            else Qt.CheckState.PartiallyChecked
            if on_page
            else Qt.CheckState.Unchecked
        )
        self.bulk_text.setText(f"Đã chọn {len(self.checked)} lịch")
        if self.checked:
            unroll_height(self.bulk_bar)
        else:
            self.bulk_bar.hide()

    def delete(self, reminder=None):
        if reminder is not None:
            self._confirm_delete([reminder["id"]])

    def _delete_checked(self):
        self._confirm_delete(sorted(self.checked))

    def _confirm_delete(self, ids):
        if not ids:
            return
        confirmation = ConfirmBox(
            f"Xóa vĩnh viễn {len(ids)} lịch nhắc?",
            "Lịch và lịch sử gửi của chúng sẽ bị xóa khỏi ứng dụng, không thể hoàn "
            "tác. Lịch đang được gửi sẽ được giữ lại. Tin đã gửi không bị thu hồi.",
            self.window(),
        )
        confirmation.yesButton.setText("Xóa vĩnh viễn")
        confirmation.cancelButton.setText("Giữ lịch")
        confirmation.cancelButton.setFocus()
        if confirmation.exec():
            self.runner.submit(
                lambda: self.service.delete(ids),
                lambda deleted: self._deleted(len(ids), deleted),
                self.show_error,
            )

    def _deleted(self, requested, deleted):
        self.checked.clear()
        kept = requested - deleted
        self.feedback.setText(
            f"Đã xóa {deleted} lịch nhắc."
            + (f" {kept} lịch đang được gửi nên chưa xóa; thử lại sau." if kept else "")
        )
        self._changed()

    def _changed(self, _=None):
        self.refresh()
        self.changed.emit()

    def worker_action(self, action):
        self.runner.submit(action, lambda _: self.refresh(), self.show_error)
