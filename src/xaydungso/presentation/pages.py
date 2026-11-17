"""Record management and reminder pages; persistence remains in use cases."""

from datetime import datetime

from PyQt6.QtCore import QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    LineEdit,
    MessageBox,
    PrimaryPushButton,
    PushButton,
    SubtitleLabel,
    TableWidget,
)

from xaydungso.domain.records import RecordStatus, ValidationError
from xaydungso.domain.reminders import LOCAL_ZONE
from xaydungso.presentation.forms import RecordDialog, ReminderDialog


class Page(QWidget):
    def __init__(self, title, name, runner, parent=None):
        super().__init__(parent)
        self.setObjectName(name)
        self.runner = runner
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(28, 28, 28, 24)
        self.layout.setSpacing(16)
        self.layout.addWidget(SubtitleLabel(title, self))
        self.feedback = BodyLabel(self)
        self.feedback.setWordWrap(True)

    def show_error(self, error):
        self.feedback.setText(
            str(error)
            if isinstance(error, ValidationError)
            else "Không thể thực hiện. Vui lòng kiểm tra file/quyền truy cập và thử lại."
        )

    def table(self, headers):
        table = TableWidget(self)
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().hide()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setBorderVisible(True)
        self.layout.addWidget(table, 1)
        return table


class RecordsPage(Page):
    changed = pyqtSignal()
    remind = pyqtSignal(object)

    def __init__(self, service, runner, output_path, parent=None):
        super().__init__("Hồ sơ xây dựng", "records", runner, parent)
        self.service, self.output_path = service, output_path
        self.records = []
        self.editor = None
        toolbar = QHBoxLayout()
        self.search = LineEdit(self)
        self.search.setPlaceholderText("Tìm mã, tên, số điện thoại, địa chỉ, ghi chú…")
        self.status_filter = ComboBox(self)
        self.status_filter.addItems(
            ["Tất cả trạng thái", *[item.value for item in RecordStatus]]
        )
        self.add_button = PrimaryPushButton("Thêm hồ sơ", self)
        toolbar.addWidget(self.search, 1)
        toolbar.addWidget(self.status_filter)
        toolbar.addWidget(self.add_button)
        self.layout.addLayout(toolbar)
        actions = QHBoxLayout()
        self.edit_button = PushButton("Chi tiết / sửa", self)
        self.delete_button = PushButton("Xóa hồ sơ", self)
        self.remind_button = PushButton("Tạo nhắc cho hồ sơ", self)
        self.export_button = PushButton("Xuất lại Excel", self)
        self.open_button = PushButton("Mở sổ Excel", self)
        self.refresh_button = PushButton("Tải lại", self)
        for button in (
            self.edit_button,
            self.delete_button,
            self.remind_button,
            self.export_button,
            self.open_button,
            self.refresh_button,
        ):
            actions.addWidget(button)
        actions.addStretch()
        self.layout.addLayout(actions)
        self.count = BodyLabel(self)
        self.layout.addWidget(self.count)
        self.records_table = self.table(
            ["Mã hồ sơ", "Họ và tên", "Số điện thoại", "Thời gian nhận", "Trạng thái"]
        )
        self.layout.addWidget(self.feedback)
        self.debounce = QTimer(self)
        self.debounce.setSingleShot(True)
        self.debounce.setInterval(250)
        self.debounce.timeout.connect(self.refresh)
        self.search.textChanged.connect(lambda: self.debounce.start())
        self.status_filter.currentIndexChanged.connect(self.refresh)
        self.add_button.clicked.connect(lambda: self.edit(None))
        self.edit_button.clicked.connect(lambda: self.edit(self.selected()))
        self.records_table.cellDoubleClicked.connect(
            lambda *_: self.edit(self.selected())
        )
        self.delete_button.clicked.connect(self.delete_selected)
        self.remind_button.clicked.connect(
            lambda: self.remind.emit(self.selected()) if self.selected() else None
        )
        self.export_button.clicked.connect(self.export)
        self.open_button.clicked.connect(self.open_export)
        self.refresh_button.clicked.connect(self.refresh)
        self.records_table.itemSelectionChanged.connect(self._selection)
        self._selection()
        self.refresh()

    def selected(self):
        row = self.records_table.currentRow()
        return self.records[row] if 0 <= row < len(self.records) else None

    def _selection(self):
        for button in (self.edit_button, self.delete_button, self.remind_button):
            button.setEnabled(self.selected() is not None)

    def refresh(self, *_):
        search = self.search.text()
        index = self.status_filter.currentIndex()
        status = list(RecordStatus)[index - 1] if index > 0 else None
        self.runner.submit(
            lambda: self.service.list(search, status), self._render, self.show_error
        )

    def _render(self, records):
        self.records = records
        self.records_table.setRowCount(len(records))
        for index, record in enumerate(records):
            data = record.data
            for column, value in enumerate(
                (
                    data.record_code,
                    data.applicant_name,
                    data.phone,
                    data.received_at,
                    data.status.value,
                )
            ):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                self.records_table.setItem(index, column, item)
        self.records_table.resizeRowsToContents()
        self.count.setText(
            f"{len(records)} hồ sơ"
            if records
            else "Chưa có hồ sơ phù hợp. Chọn Thêm hồ sơ để bắt đầu."
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
            result.export_error or "SQLite đã lưu. Sổ Excel đã cập nhật."
        )
        self.refresh()
        self.changed.emit()

    def delete_selected(self):
        record = self.selected()
        if record is None:
            return
        confirmation = MessageBox(
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

    def export(self):
        self.export_button.setEnabled(False)

        def done(error):
            self.export_button.setEnabled(True)
            self.feedback.setText(error or f"Đã xuất toàn bộ hồ sơ: {self.output_path}")

        def failed(error):
            self.export_button.setEnabled(True)
            self.show_error(error)

        self.runner.submit(self.service.export, done, failed)

    def open_export(self):
        if not self.output_path.exists():
            self.feedback.setText("Chưa có sổ Excel. Chọn Xuất lại Excel trước.")
        elif not QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output_path))):
            self.feedback.setText(
                f"Không mở được ứng dụng Excel. File ở: {self.output_path}"
            )


def display_time(value):
    return (
        datetime.fromisoformat(value)
        .astimezone(LOCAL_ZONE)
        .strftime("%d/%m/%Y\n%H:%M:%S")
    )


class RemindersPage(Page):
    changed = pyqtSignal()

    def __init__(self, service, records, background, runner, parent=None):
        super().__init__("Lịch nhắc nhở", "reminders", runner, parent)
        self.service, self.records_service, self.background = (
            service,
            records,
            background,
        )
        self.reminders = []
        self.editor = None
        toolbar = QHBoxLayout()
        self.add_button = PrimaryPushButton("Tạo lịch nhắc", self)
        self.edit_button = PushButton("Sửa lịch chưa gửi", self)
        self.cancel_button = PushButton("Hủy lịch", self)
        self.refresh_button = PushButton("Tải lại", self)
        for button in (
            self.add_button,
            self.edit_button,
            self.cancel_button,
            self.refresh_button,
        ):
            toolbar.addWidget(button)
        toolbar.addStretch()
        self.layout.addLayout(toolbar)
        self.worker_status = BodyLabel(self)
        self.worker_status.setWordWrap(True)
        self.layout.addWidget(self.worker_status)
        controls = QHBoxLayout()
        self.start_button = PushButton("Bật nhắc nền", self)
        self.stop_button = PushButton("Dừng nhắc nền", self)
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addStretch()
        self.layout.addLayout(controls)
        help_text = BodyLabel(
            "Giờ Việt Nam · Gửi trong 07:00–23:00 · Lịch bỏ lỡ sẽ gửi bù.\n"
            "Tiến trình nền tiếp tục khi đóng cửa sổ; máy phải đang bật. "
            "Cấu hình Telegram bằng XAYDUNGSO_TELEGRAM_BOT_TOKEN và XAYDUNGSO_TELEGRAM_CHAT_ID trước khi bật nhắc nền.",
            self,
        )
        help_text.setWordWrap(True)
        self.layout.addWidget(help_text)
        self.reminders_table = self.table(
            ["Nội dung", "Bắt đầu", "Đến hạn", "Giờ gửi", "Telegram", "Windows", "Lịch"]
        )
        header = self.reminders_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setMinimumSectionSize(140)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.feedback)
        self.add_button.clicked.connect(lambda: self.edit())
        self.edit_button.clicked.connect(self.edit_selected)
        self.cancel_button.clicked.connect(self.cancel_selected)
        self.refresh_button.clicked.connect(self.refresh)
        self.start_button.clicked.connect(
            lambda: self.worker_action(self.background.start)
        )
        self.stop_button.clicked.connect(
            lambda: self.worker_action(self.background.stop)
        )
        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(
            lambda: self.refresh() if not self.runner.busy else None
        )
        self.timer.start()
        self.refresh()

    def refresh(self, *_):
        self.runner.submit(self.service.list, self._render, self.show_error)

    def _render(self, reminders):
        self.reminders = reminders
        self.reminders_table.setRowCount(len(reminders))
        labels = {
            "pending": "Chờ gửi",
            "sending": "Đang gửi",
            "sent": "Đã gửi",
            "failed": "Lỗi / chờ thử lại",
        }
        for index, reminder in enumerate(reminders):
            values = [
                reminder["title"],
                display_time(reminder["start_at"]),
                display_time(reminder["deadline_at"]),
                display_time(reminder["notify_at"]),
            ]
            values += [
                labels[reminder["deliveries"][channel]["state"]]
                for channel in ("telegram", "windows")
            ]
            values += ["Đã hủy" if reminder["cancelled"] else "Hoạt động"]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                if column in (4, 5):
                    item.setToolTip(
                        reminder["deliveries"][("telegram", "windows")[column - 4]][
                            "last_error"
                        ]
                    )
                self.reminders_table.setItem(index, column, item)
        self.reminders_table.resizeRowsToContents()
        try:
            running = self.background.running()
            self.worker_status.setText(
                "Nhắc nền đang chạy."
                if running
                else "Nhắc nền đang dừng. Bật nhắc nền để xử lý các lịch đến hạn."
            )
        except OSError:
            self.worker_status.setText(
                "Không kiểm tra được tiến trình nền. Kiểm tra quyền truy cập thư mục dữ liệu."
            )

    def selected(self):
        index = self.reminders_table.currentRow()
        return self.reminders[index] if 0 <= index < len(self.reminders) else None

    def edit_selected(self):
        reminder = self.selected()
        if reminder:
            self.edit(reminder=reminder)

    def edit(self, record=None, reminder=None):
        self.runner.submit(
            lambda: self.records_service.list(),
            lambda records: self._open_editor(records, record, reminder),
            self.show_error,
        )

    def _open_editor(self, records, record, reminder):
        dialog = ReminderDialog(
            records, reminder=reminder, record=record, parent=self.window()
        )
        self.editor = dialog

        def success(result):
            dialog.set_saving(False)
            dialog.accept()
            self.feedback.setText(
                f"Đã lưu lịch. Giờ gửi: {result.notify_at:%d/%m/%Y %H:%M:%S}. Bật nhắc nền để gửi."
            )
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

    def cancel_selected(self):
        reminder = self.selected()
        if reminder:
            confirmation = MessageBox(
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

    def _changed(self, _=None):
        self.refresh()
        self.changed.emit()

    def worker_action(self, action):
        self.runner.submit(action, lambda _: self.refresh(), self.show_error)
