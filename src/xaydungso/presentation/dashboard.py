"""Fluent Dashboard consumes only the Application read model."""

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    PrimaryPushButton,
    PushButton,
    SimpleCardWidget,
    SubtitleLabel,
    TableWidget,
    TitleLabel,
)

from xaydungso.application.dashboard import Dashboard, DashboardSnapshot
from xaydungso.domain.reminders import LOCAL_ZONE


class DashboardPage(QWidget):
    open_records = pyqtSignal()
    open_reminders = pyqtSignal()

    def __init__(self, service: Dashboard, runner, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboard")
        self.service, self.runner = service, runner
        self.loading = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        layout.setSpacing(16)
        header = QHBoxLayout()
        header.addWidget(SubtitleLabel("Tổng quan", self))
        header.addStretch()
        self.refresh_button = PushButton("Tải lại", self)
        header.addWidget(self.refresh_button)
        layout.addLayout(header)
        self.feedback = BodyLabel(self)
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)
        metrics = QGridLayout()
        self.metric_values = {}
        for index, (key, title) in enumerate(
            (
                ("total_records", "Tổng hồ sơ"),
                ("incomplete_records", "Chưa hoàn thành"),
                ("completed_records", "Đã hoàn thành"),
                ("todays_reminders", "Nhắc hôm nay"),
            )
        ):
            card = SimpleCardWidget(self)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 16, 18, 16)
            label = BodyLabel(title, card)
            label.setWordWrap(True)
            value = TitleLabel("—", card)
            card_layout.addWidget(label)
            card_layout.addWidget(value)
            self.metric_values[key] = value
            metrics.addWidget(card, index // 2, index % 2)
        layout.addLayout(metrics)
        actions = QHBoxLayout()
        self.records_button = PrimaryPushButton("Quản lý hồ sơ", self)
        self.reminders_button = PushButton("Xem lịch nhắc", self)
        actions.addWidget(self.records_button)
        actions.addWidget(self.reminders_button)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addWidget(SubtitleLabel("Lịch nhắc sắp tới", self))
        self.upcoming_message = BodyLabel(self)
        self.upcoming_message.setWordWrap(True)
        layout.addWidget(self.upcoming_message)
        self.upcoming_table = TableWidget(self)
        self.upcoming_table.setColumnCount(3)
        self.upcoming_table.setHorizontalHeaderLabels(
            ["Nội dung", "Hồ sơ", "Giờ gửi (Việt Nam)"]
        )
        self.upcoming_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.upcoming_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.upcoming_table.verticalHeader().hide()
        self.upcoming_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.upcoming_table.setBorderVisible(True)
        layout.addWidget(self.upcoming_table, 1)
        self.refresh_button.clicked.connect(self.refresh)
        self.records_button.clicked.connect(self.open_records.emit)
        self.reminders_button.clicked.connect(self.open_reminders.emit)
        self.timer = QTimer(self)
        self.timer.setInterval(30_000)
        self.timer.timeout.connect(self._automatic_refresh)
        self.timer.start()
        self.refresh()

    def _automatic_refresh(self):
        if self.isVisible() and not self.runner.busy:
            self.refresh()

    def refresh(self):
        if self.loading:
            return
        self.loading = True
        self.refresh_button.setEnabled(False)
        self.feedback.setText("Đang tải dữ liệu…")
        for value in self.metric_values.values():
            value.setText("—")
        self.upcoming_table.setRowCount(0)
        self.upcoming_message.setText("")
        self.runner.submit(self.service.load, self._render, self._failed)

    def _render(self, snapshot: DashboardSnapshot):
        self.loading = False
        self.refresh_button.setEnabled(True)
        for key, label in self.metric_values.items():
            label.setText(str(getattr(snapshot, key)))
        self.feedback.setText(
            f"Ngày {snapshot.as_of:%d/%m/%Y} · Giờ Việt Nam · "
            f"Cập nhật lúc {snapshot.as_of:%H:%M:%S}"
        )
        self.upcoming_message.setText(
            "Tối đa 10 lịch chưa gửi đủ các kênh, từ thời điểm cập nhật trở đi."
            if snapshot.upcoming
            else "Không có lịch nhắc sắp tới."
        )
        self.upcoming_table.setRowCount(len(snapshot.upcoming))
        for row, reminder in enumerate(snapshot.upcoming):
            values = (
                reminder.title,
                reminder.record_code or "Không liên kết",
                reminder.notify_at.astimezone(LOCAL_ZONE).strftime("%d/%m/%Y %H:%M:%S"),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                self.upcoming_table.setItem(row, column, item)
        self.upcoming_table.resizeRowsToContents()

    def _failed(self, _error):
        self.loading = False
        self.refresh_button.setEnabled(True)
        self.feedback.setText(
            "Không tải được tổng quan. Chọn Tải lại để thử lại; bạn vẫn có thể mở Hồ sơ hoặc Nhắc nhở."
        )
        self.upcoming_message.setText("Dữ liệu chưa tải được.")
