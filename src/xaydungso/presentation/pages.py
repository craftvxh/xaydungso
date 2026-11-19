"""Record management and reminder pages; persistence remains in use cases."""

from PyQt6.QtCore import QEvent, Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QDesktopServices, QFont
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
    BodyLabel,
    CheckBox,
    PrimaryPushButton,
    PushButton,
    SearchLineEdit,
    SubtitleLabel,
    TableWidget,
    ToolButton,
    TransparentPushButton,
    setCustomStyleSheet,
)

from xaydungso.application.ports import NotificationError
from xaydungso.domain.records import RecordStatus, ValidationError
from xaydungso.presentation.confirm import ConfirmBox
from xaydungso.presentation.icons import Icon
from xaydungso.presentation.motion import slide_in_width, unroll_height
from xaydungso.presentation.record_dialog import RecordDialog
from xaydungso.presentation.record_widgets import (
    DETAIL_WIDTH,
    Pager,
    RecordDetail,
    StatusFilter,
    check_click,
    compact_checkbox,
    compact_checks,
    deadline_info,
    icon_label,
    status_badge,
)
from xaydungso.presentation.reminders_page import RemindersPage  # noqa: F401
from xaydungso.presentation.theme import (
    COLORS,
    accent_button,
    mono_font,
    qss,
    styled,
)


class Page(QWidget):
    def __init__(self, title, name, runner, parent=None):
        super().__init__(parent)
        self.setObjectName(name)
        self.runner = runner
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(28, 28, 28, 24)
        self.layout.setSpacing(16)
        self.header = QHBoxLayout()
        self.header.setSpacing(8)
        self.title_label = SubtitleLabel(title, self)
        self.header.addWidget(self.title_label)
        self.header.addStretch()
        self.layout.addLayout(self.header)
        self.feedback = BodyLabel(self)
        self.feedback.setWordWrap(True)

    def show_error(self, error):
        self.feedback.setText(
            str(error)
            if isinstance(error, (ValidationError, NotificationError))
            else "Không thể thực hiện. Vui lòng kiểm tra file/quyền truy cập và thử lại."
        )

    def table(self, headers, add=True):
        table = TableWidget(self)
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().hide()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setBorderVisible(True)
        if add:
            self.layout.addWidget(table, 1)
        return table


class RecordsPage(Page):
    changed = pyqtSignal()
    remind = pyqtSignal(object)
    # (key, header, width). Wider than the pane on purpose: the table scrolls
    # sideways, as in the design, and every column can be resized by dragging.
    COLUMNS = (
        ("check", "", 40),
        ("record_code", "MÃ HỒ SƠ", 92),
        ("applicant_name", "HỌ VÀ TÊN", 150),
        ("phone", "SỐ ĐIỆN THOẠI", 112),
        ("address", "ĐỊA CHỈ", 170),
        # Time columns side by side, status last (user's choice).
        ("received_at", "NGÀY TIẾP NHẬN", 150),
        ("deadline", "HẠN XỬ LÝ", 150),
        ("return_appointment_date", "NGÀY HẸN TRẢ", 150),
        ("handover_at", "GIAO NHẬN", 150),
        ("status", "TRẠNG THÁI", 150),
    )
    COLUMN = {key: index for index, (key, _, _) in enumerate(COLUMNS)}
    # Date-time columns use the monospace family, like record codes.
    DATE_KEYS = (
        "received_at",
        "deadline",
        "return_appointment_date",
        "handover_at",
    )
    PAGE_SIZE = 14

    def __init__(self, service, runner, output_path, parent=None):
        super().__init__("Quản lý hồ sơ", "records", runner, parent)
        self.service, self.output_path = service, output_path
        self.all_records, self.records = [], []
        self.selected_id = None
        self.checked = set()
        self.page = 0
        self.focus_id = None
        self.editor = None
        styled(
            self,
            """
            QWidget#records { background: @page; }
            QLabel { background: transparent; color: @text; font-size: @fs_body; }
            QLabel#pageTitle { font-size: @fs_page; font-weight: 700; }
            QLabel#pageIcon { background: @primary_container; border-radius: 4px; }
            QFrame#recordsToolbar, QFrame#tableCard { background: @surface;
                border: 1px solid @outline_soft; border-radius: 8px; }
            QFrame#recordsCount { background: @surface_container;
                border: 1px solid @outline_soft; border-radius: 8px; }
            QLabel#countNumber { font-size: @fs_small; font-weight: 700; }
            QLabel#countUnit, QLabel#tableFooterText { color: @muted; font-size: @fs_small; }
            QFrame#tableFooter { background: @surface_low; border: none;
                border-top: 1px solid @outline_soft; border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px; }
            QFrame#bulkBar { background: @surface_container; border: none;
                border-bottom: 1px solid @outline_soft; border-top-left-radius: 8px;
                border-top-right-radius: 8px; }
            QLabel#bulkText { font-size: @fs_body; font-weight: 600; }
            """,
        )
        self.layout.setContentsMargins(16, 12, 16, 12)
        self.layout.setSpacing(10)
        self.title_label.hide()
        page_icon = icon_label(Icon.FOLDER, 16, self, COLORS["on_primary"])
        page_icon.setObjectName("pageIcon")
        page_icon.setFixedSize(28, 28)
        page_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_title = QLabel("Quản lý hồ sơ", self)
        page_title.setObjectName("pageTitle")
        self.header.insertWidget(0, page_icon)
        self.header.insertWidget(1, page_title)
        self.header.insertSpacing(1, 4)
        self.open_button = TransparentPushButton(Icon.FOLDER, "Mở sổ Excel", self)
        self.refresh_button = TransparentPushButton(Icon.SYNC, "Tải lại", self)
        self.add_button = PrimaryPushButton(Icon.ADD, "Thêm hồ sơ", self)
        accent_button(self.add_button)
        for button in (self.open_button, self.refresh_button, self.add_button):
            self.header.addWidget(button)

        toolbar = QFrame(self)
        toolbar.setObjectName("recordsToolbar")
        bar = QHBoxLayout(toolbar)
        bar.setContentsMargins(12, 8, 12, 8)
        bar.setSpacing(12)
        self.search = SearchLineEdit(toolbar)
        self.search.setPlaceholderText("Tìm mã hồ sơ, họ tên, số điện thoại...")
        self.search.setMinimumWidth(280)
        self.search.setMaximumWidth(340)
        self.status_filter = StatusFilter(toolbar)
        count_box = QFrame(toolbar)
        count_box.setObjectName("recordsCount")
        count_layout = QHBoxLayout(count_box)
        count_layout.setContentsMargins(10, 4, 10, 4)
        count_layout.setSpacing(5)
        count_layout.addWidget(
            icon_label(Icon.LIBRARY, 14, count_box, COLORS["primary"])
        )
        self.count = QLabel("0", count_box)
        self.count.setObjectName("countNumber")
        unit = QLabel("hồ sơ", count_box)
        unit.setObjectName("countUnit")
        count_layout.addWidget(self.count)
        count_layout.addWidget(unit)
        bar.addWidget(self.search, 1)
        bar.addWidget(self.status_filter)
        bar.addStretch()
        bar.addWidget(count_box)
        self.layout.addWidget(toolbar)

        workspace = QHBoxLayout()
        workspace.setSpacing(10)
        card = QFrame(self)
        card.setObjectName("tableCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(1, 1, 1, 0)
        card_layout.setSpacing(0)
        self.bulk_bar = QFrame(card)
        self.bulk_bar.setObjectName("bulkBar")
        bulk = QHBoxLayout(self.bulk_bar)
        bulk.setContentsMargins(12, 5, 8, 5)
        bulk.setSpacing(6)
        self.bulk_text = QLabel(self.bulk_bar)
        self.bulk_text.setObjectName("bulkText")
        self.bulk_done_button = TransparentPushButton(
            Icon.ACCEPT, "Hoàn thành", self.bulk_bar
        )
        self.bulk_done_button.setToolTip("Đánh dấu Đã hoàn thành các hồ sơ đã chọn")
        self.bulk_open_button = TransparentPushButton(
            Icon.HISTORY, "Chưa hoàn thành", self.bulk_bar
        )
        self.bulk_open_button.setToolTip("Đánh dấu Chưa hoàn thành các hồ sơ đã chọn")
        self.bulk_delete_button = TransparentPushButton(
            Icon.DELETE, "Xóa", self.bulk_bar
        )
        self.bulk_delete_button.setToolTip("Xóa vĩnh viễn các hồ sơ đã chọn")
        self.bulk_clear_button = TransparentPushButton("Bỏ chọn", self.bulk_bar)
        bulk.addWidget(self.bulk_text)
        bulk.addStretch()
        for button in (
            self.bulk_done_button,
            self.bulk_open_button,
            self.bulk_delete_button,
            self.bulk_clear_button,
        ):
            bulk.addWidget(button)
        self.bulk_bar.hide()
        card_layout.addWidget(self.bulk_bar)
        self.records_table = self.table(
            [title for _, title, _ in self.COLUMNS], add=False
        )
        self.records_table.setParent(card)
        self.records_table.setBorderVisible(False)
        self.records_table.setAlternatingRowColors(False)
        compact_checks(self.records_table)
        self.records_table.setWordWrap(False)
        header = self.records_table.horizontalHeader()
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setStretchLastSection(False)
        for column, (_, _, width) in enumerate(self.COLUMNS):
            header.resizeSection(column, width)
        self.records_table.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        # Spread spare width over name/address so the table always fills its card.
        self.records_table.viewport().installEventFilter(self)
        # Select-all box for the visible page, drawn over header section 0.
        self.check_all = compact_checkbox(CheckBox(header))
        self.check_all.setTristate(True)
        self.check_all.setFixedSize(22, 22)
        self.check_all.setToolTip("Chọn / bỏ chọn tất cả hồ sơ trên trang")
        self.records_table.verticalHeader().setDefaultSectionSize(36)
        table_sheet = qss(
            # Soft column borders in the body and matching header dividers.
            "QTableView { gridline-color: @outline_soft; }"
            " QHeaderView::section { background-color: @surface_low; color: @muted;"
            " font-family: @font; font-size: @fs_tiny; font-weight: 600; border: none;"
            " border-right: 1px solid @outline_soft;"
            # Fluent's 16px item padding + Qt's ~3px text margin = TEXT_INSET.
            " border-bottom: 1px solid @outline_soft; padding-left: 19px;"
            " padding-right: 8px; }"
        )
        self.records_table.setShowGrid(True)
        self.records_table.setGridStyle(Qt.PenStyle.SolidLine)
        setCustomStyleSheet(self.records_table, table_sheet, table_sheet)
        card_layout.addWidget(self.records_table, 1)
        footer = QFrame(card)
        footer.setObjectName("tableFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 7, 12, 7)
        self.footer_text = QLabel(footer)
        self.footer_text.setObjectName("tableFooterText")
        footer_layout.addWidget(self.footer_text)
        footer_layout.addStretch()
        self.pager = Pager(footer)
        footer_layout.addWidget(self.pager)
        card_layout.addWidget(footer)
        workspace.addWidget(card, 1)
        self.detail = RecordDetail(self)
        self.edit_button = PrimaryPushButton(Icon.EDIT, "Sửa hồ sơ", self.detail)
        accent_button(self.edit_button)
        self.remind_button = ToolButton(Icon.RINGER, self.detail)
        self.remind_button.setToolTip("Tạo lịch nhắc cho hồ sơ này")
        self.delete_button = PushButton(Icon.DELETE, "Xóa hồ sơ", self.detail)
        self.detail.add_action(self.edit_button, 1)
        self.detail.add_action(self.remind_button)
        self.detail.add_action(self.delete_button)
        workspace.addWidget(self.detail)
        self.layout.addLayout(workspace, 1)
        self.layout.addWidget(self.feedback)

        self.debounce = QTimer(self)
        self.debounce.setSingleShot(True)
        self.debounce.setInterval(250)
        self.debounce.timeout.connect(self.refresh)
        self.search.textChanged.connect(self._search_changed)
        self.status_filter.currentIndexChanged.connect(lambda _: self._go(0))
        self.pager.pageChanged.connect(self._go)
        header.sectionClicked.connect(self._header_clicked)
        self.check_all.clicked.connect(lambda: self._header_clicked(0))
        self.records_table.horizontalScrollBar().valueChanged.connect(
            lambda _: self._place_check_all()
        )
        self.bulk_done_button.clicked.connect(
            lambda: self._bulk_status(RecordStatus.COMPLETE)
        )
        self.bulk_open_button.clicked.connect(
            lambda: self._bulk_status(RecordStatus.INCOMPLETE)
        )
        self.bulk_delete_button.clicked.connect(self._bulk_delete)
        self.bulk_clear_button.clicked.connect(self._clear_checked)
        self.add_button.clicked.connect(lambda: self.edit(None))
        self.edit_button.clicked.connect(lambda: self.edit(self.selected()))
        self.records_table.cellDoubleClicked.connect(
            lambda *_: self.edit(self.selected())
        )
        self.delete_button.clicked.connect(self.delete_selected)
        self.remind_button.clicked.connect(
            lambda: self.remind.emit(self.selected()) if self.selected() else None
        )
        self.open_button.clicked.connect(self.open_export)
        self.refresh_button.clicked.connect(self.refresh)
        self.records_table.itemSelectionChanged.connect(self._selection)
        self.detail.closed.connect(self.records_table.clearSelection)
        self._selection()
        self.refresh()

    def eventFilter(self, watched, event):
        if watched is self.records_table.viewport():
            if event.type() == QEvent.Type.Resize:
                self._fit_columns()
            elif check_click(self.records_table, event, self._cell_clicked):
                return True  # Ticking a box must not select the row.
        return super().eventFilter(watched, event)

    def _fit_columns(self):
        widths = {key: width for key, _, width in self.COLUMNS}
        spare = max(0, self.records_table.viewport().width() - sum(widths.values()))
        name_share = spare * 2 // 5
        widths["applicant_name"] += name_share
        widths["address"] += spare - name_share
        header = self.records_table.horizontalHeader()
        for column, (key, _, _) in enumerate(self.COLUMNS):
            header.resizeSection(column, widths[key])
        self._place_check_all()

    def focus_record(self, record_id):
        """Show one record (e.g. from the Dashboard): clear filters, select it."""
        self.focus_id = record_id
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.status_filter.setCurrentIndex(0)
        self.refresh()

    def _search_changed(self):
        self.page = 0
        self.debounce.start()

    def _go(self, page):
        self.page = page
        self._show()

    def _cell_clicked(self, row, column):
        if column == 0 and 0 <= row < len(self.records):
            self.checked ^= {self.records[row].id}
            self._update_checks()

    def _header_clicked(self, column):
        if column == 0 and self.records:
            ids = {record.id for record in self.records}
            if ids <= self.checked:
                self.checked -= ids
            else:
                self.checked |= ids
            self._update_checks()

    def _clear_checked(self):
        self.checked.clear()
        self._update_checks()

    def _place_check_all(self):
        # Fluent draws row boxes 15px into column 0; match that and centre it.
        header = self.records_table.horizontalHeader()
        x = header.sectionViewportPosition(0) + 15  # Row boxes start 16px in.
        self.check_all.move(x, (header.height() - self.check_all.height()) // 2)
        self.check_all.setVisible(x >= 0)  # Hidden once scrolled past column 0.

    def _update_checks(self):
        self._place_check_all()
        ids = {record.id for record in self.records}
        for row, record in enumerate(self.records):
            item = self.records_table.item(row, 0)
            if item is not None:
                item.setCheckState(
                    Qt.CheckState.Checked
                    if record.id in self.checked
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
        self.bulk_text.setText(f"Đã chọn {len(self.checked)} hồ sơ")
        if self.checked:
            unroll_height(self.bulk_bar)
        else:
            self.bulk_bar.hide()

    def _bulk_status(self, status):
        ids = sorted(self.checked)
        if ids:
            self.runner.submit(
                lambda: self.service.set_status(ids, status),
                self._bulk_done,
                self.show_error,
            )

    def _bulk_delete(self):
        ids = sorted(self.checked)
        if not ids:
            return
        confirmation = ConfirmBox(
            f"Xóa vĩnh viễn {len(ids)} hồ sơ?",
            f"{len(ids)} hồ sơ đã chọn sẽ bị xóa vĩnh viễn. Các lịch nhắc chưa gửi "
            "liên quan sẽ bị hủy. Không thể hoàn tác.",
            self.window(),
        )
        confirmation.yesButton.setText("Xóa vĩnh viễn")
        confirmation.cancelButton.setText("Giữ hồ sơ")
        confirmation.cancelButton.setFocus()
        if confirmation.exec():
            self.runner.submit(
                lambda: self.service.delete_many(ids), self._bulk_done, self.show_error
            )

    def _bulk_done(self, result):
        self.checked.clear()
        self._saved(result)

    def selected(self):
        rows = self.records_table.selectionModel().selectedRows()
        row = rows[0].row() if rows else -1
        return self.records[row] if 0 <= row < len(self.records) else None

    def _selection(self):
        record = self.selected()
        self.selected_id = record.id if record else None
        for button in (self.edit_button, self.delete_button, self.remind_button):
            button.setVisible(record is not None)
        self.detail.show_record(record)
        # The pane opens for a selected record and closes otherwise, so the
        # wide table gets the full width while browsing.
        if record is None:
            self.detail.hide()
        else:
            slide_in_width(self.detail, DETAIL_WIDTH)

    def refresh(self, *_):
        search = self.search.text()
        # One query; status counts and the status filter are derived locally.
        self.runner.submit(
            lambda: self.service.list(search, None), self._render, self.show_error
        )

    def _render(self, records):
        self.all_records = records
        self.checked &= {record.id for record in records}
        self.status_filter.set_counts(
            [len(records)]
            + [
                sum(record.data.status is status for record in records)
                for status in RecordStatus
            ]
        )
        self._show()
        self.focus_id = None  # Fresh data arrived: a missing record is not retried.

    def _show(self):
        status = self.status_filter.status()
        keep = self.selected_id
        matching = [
            record
            for record in self.all_records
            if status is None or record.data.status is status
        ]
        pages = max(1, -(-len(matching) // self.PAGE_SIZE))
        if self.focus_id is not None:
            ids = [record.id for record in matching]
            if self.focus_id in ids:
                self.page = ids.index(self.focus_id) // self.PAGE_SIZE
                self.selected_id = keep = self.focus_id
                self.focus_id = None
        self.page = min(self.page, pages - 1)
        start = self.page * self.PAGE_SIZE
        records = matching[start : start + self.PAGE_SIZE]
        self.records = records
        table = self.records_table
        table.blockSignals(True)
        table.clearSelection()
        table.setRowCount(len(records))
        mono = mono_font(weight=QFont.Weight.Bold)
        dates = mono_font()
        overdue_font = mono_font(weight=QFont.Weight.Bold)
        for index, record in enumerate(records):
            data = record.data
            deadline, hint, overdue = deadline_info(data)
            check = QTableWidgetItem()
            # Drawn by Fluent's delegate; toggled in _cell_clicked, not by Qt.
            check.setFlags(check.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            check.setCheckState(Qt.CheckState.Unchecked)
            table.setItem(index, 0, check)
            for key, _, _ in self.COLUMNS:
                if key in ("check", "status"):
                    continue
                value = deadline if key == "deadline" else getattr(data, key)
                item = QTableWidgetItem(value)
                item.setToolTip(
                    f"{value} · {hint}" if key == "deadline" and hint else value
                )
                if key == "record_code":
                    item.setFont(mono)
                    item.setForeground(QColor(COLORS["primary"]))
                elif key == "deadline" and overdue:
                    item.setFont(overdue_font)
                    item.setForeground(QColor(COLORS["error"]))
                elif key in self.DATE_KEYS:
                    item.setFont(dates)
                table.setItem(index, self.COLUMN[key], item)
            # The badge widget shows the status; an empty item avoids text drawn
            # underneath it by the table delegate.
            status_item = QTableWidgetItem()
            status_item.setToolTip(data.status.value)
            table.setItem(index, self.COLUMN["status"], status_item)
            cell = styled(QWidget(), "QWidget { background: transparent; }")
            box = QHBoxLayout(cell)
            box.setContentsMargins(19, 0, 8, 0)  # Same inset as the header text.
            box.addWidget(
                status_badge(data.status, cell), 0, Qt.AlignmentFlag.AlignVCenter
            )
            box.addStretch()
            table.setCellWidget(index, self.COLUMN["status"], cell)
            if record.id == keep:
                table.selectRow(index)
        table.blockSignals(False)
        total = len(self.all_records)
        bold_text = f"<b style='color:{COLORS['text']}'>%s</b>"
        span = f"{start + 1} - {start + len(records)}" if records else "0"
        self.count.setText(str(len(matching)))
        self.footer_text.setText(
            f"Hiển thị {bold_text % span} trên tổng số "
            f"{bold_text % len(matching)} hồ sơ"
        )
        self.pager.set(self.page, pages)
        self._update_checks()
        if not total:
            self.feedback.setText(
                "Chưa có hồ sơ phù hợp. Chọn Thêm hồ sơ để bắt đầu."
                if not self.search.text()
                else "Không tìm thấy hồ sơ phù hợp."
            )
        self._selection()

    def edit(self, record=None):
        dialog = RecordDialog(record, self.window())
        self.editor = dialog

        def failure(error):
            dialog.set_saving(False)
            dialog.error.setText(
                str(error)
                if isinstance(error, ValidationError)
                else "Lưu không thành công. Dữ liệu nhập vẫn được giữ; hãy thử lại."
            )

        def success(result):
            dialog.set_saving(False)
            dialog.accept()
            self._saved(result)

        dialog.submitted.connect(
            lambda data: self.runner.submit(
                lambda: self.service.save(data, record.id if record else None),
                success,
                failure,
            )
        )
        dialog.setModal(True)
        dialog.show()

    def _saved(self, result):
        self.feedback.setText(
            result.export_error or "Đã lưu thay đổi và tự động cập nhật Excel."
        )
        self.refresh()
        self.changed.emit()

    def delete_selected(self):
        record = self.selected()
        if record is None:
            return
        confirmation = ConfirmBox(
            "Xóa vĩnh viễn hồ sơ?",
            f"Hồ sơ {record.data.record_code} sẽ bị xóa vĩnh viễn. Các lịch nhắc chưa gửi liên quan sẽ bị hủy.",
            self.window(),
        )
        confirmation.yesButton.setText("Xóa vĩnh viễn")
        confirmation.cancelButton.setText("Giữ hồ sơ")
        confirmation.cancelButton.setFocus()
        if confirmation.exec():
            self.runner.submit(
                lambda: self.service.delete(record.id), self._saved, self.show_error
            )

    def open_export(self):
        if self.output_path is None:
            self.feedback.setText(
                "Chưa chọn file Excel. Vào Cài đặt để chọn file có sẵn."
            )
        elif not self.output_path.exists():
            self.feedback.setText(
                "Không tìm thấy file Excel đã chọn. Kiểm tra lại trong Cài đặt."
            )
        elif not QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output_path))):
            self.feedback.setText(
                f"Không mở được ứng dụng Excel. File ở: {self.output_path}"
            )
