"""Cài đặt: Dữ liệu (SQLite), Telegram Bot and Excel sections (Stitch design).

Persistence goes through the settings use case; status tiles are read-only
facts from ``SqliteDiagnostics``. No backup, repair or Excel import here.
"""

import time

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    LineEdit,
    PasswordLineEdit,
    PrimaryPushButton,
    PushButton,
)

from xaydungso.application.ports import NotificationError
from xaydungso.application.settings import Preferences
from xaydungso.domain.records import ValidationError
from xaydungso.presentation.icons import Icon
from xaydungso.presentation.record_widgets import icon_label
from xaydungso.presentation.theme import COLORS, accent_button, styled

SHEET = """
QWidget#settings { background: @page; }
QLabel { background: transparent; color: @text; font-size: 12px; }
QLabel#setTitle { font-size: 20px; font-weight: 700; }
QLabel#crumb { color: @muted; font-size: 13px; }
QFrame#subNav, QFrame[role="panel"] { background: @surface;
    border: 1px solid @outline_soft; border-radius: 10px; }
QLabel[role="overline"] { color: @muted; font-size: 10px; font-weight: 700; }
QPushButton[role="navItem"] { background: transparent; border: none;
    border-radius: 6px; text-align: left; }
QPushButton[role="navItem"]:hover { background: @surface_low; }
QPushButton[role="navItem"]:checked { background: @surface_container; }
QLabel[role="navTitle"] { font-size: 13px; font-weight: 600; }
QLabel[role="navHint"] { color: @muted; font-size: 11px; }
QLabel[role="sectionTitle"] { font-size: 18px; font-weight: 700; }
QLabel[role="muted"] { color: @muted; font-size: 12px; }
QLabel[role="small"] { color: @muted; font-size: 11px; }
QLabel[role="field"] { font-size: 12px; font-weight: 600; }
QLabel[role="chip"] { border-radius: 8px; padding: 2px 10px; font-size: 11px;
    font-weight: 600; background: @surface_container; color: @muted; }
QLabel[role="chip"][tone="ok"] { background: #dcfce7; color: #15803d; }
QLabel[role="chip"][tone="bad"] { background: #fee2e2; color: #b91c1c; }
QLabel[role="chip"][tone="busy"] { background: #dbeafe; color: #1d4ed8; }
QFrame[role="tile"] { background: @surface_low; border: 1px solid @outline_soft;
    border-radius: 8px; }
QLabel[role="tileLabel"] { color: @muted; font-size: 11px; }
QLabel[role="tileValue"] { font-size: 16px; font-weight: 700; }
QLabel[role="tileUnit"] { color: @muted; font-size: 11px; }
QFrame[role="info"] { background: @surface_low; border: 1px solid @outline_soft;
    border-radius: 8px; }
QLabel#settingsFeedback { color: @text; font-size: 12px; }
"""


def _chip(label, text, tone=""):
    label.setText(text)
    label.setProperty("tone", tone)
    label.style().unpolish(label)
    label.style().polish(label)


class SettingsPage(QWidget):
    SECTIONS = (
        ("data", Icon.LIBRARY, "Dữ liệu (SQLite)", "Tệp cục bộ trên máy"),
        ("telegram", Icon.SEND, "Telegram Bot", "Gửi lịch nhắc tự động"),
        ("excel", Icon.DOCUMENT, "Sổ theo dõi Excel", "Ghi một chiều vào .xlsx"),
    )

    def __init__(
        self, service, runner, output_path, parent=None, diagnostics=None, export=None
    ):
        super().__init__(parent)
        self.setObjectName("settings")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        styled(self, SHEET)
        self.service, self.runner = service, runner
        self.output_path = output_path
        self.diagnostics, self.export = diagnostics, export
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(10)
        header.addWidget(icon_label(Icon.SETTING, 20, self, COLORS["text"]))
        title = QLabel("Cài đặt hệ thống", self)
        title.setObjectName("setTitle")
        self.crumb = QLabel(self)
        self.crumb.setObjectName("crumb")
        header.addWidget(title)
        header.addWidget(self.crumb)
        header.addStretch()
        layout.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self._sub_nav(), 0, Qt.AlignmentFlag.AlignTop)
        self.stack = QStackedWidget(self)
        self.stack.addWidget(self._data_section())
        self.stack.addWidget(self._telegram_section())
        self.stack.addWidget(self._excel_section())
        body.addWidget(self.stack, 1)
        layout.addLayout(body, 1)
        self.feedback = QLabel(self)
        self.feedback.setObjectName("settingsFeedback")
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)
        self.show_section(0)
        self.load()

    # Layout -------------------------------------------------------------------------

    def _sub_nav(self):
        panel = QFrame(self)
        panel.setObjectName("subNav")
        panel.setFixedWidth(220)
        box = QVBoxLayout(panel)
        box.setContentsMargins(8, 12, 8, 12)
        box.setSpacing(4)
        overline = QLabel("NHÓM CẤU HÌNH", panel)
        overline.setProperty("role", "overline")
        box.addWidget(overline)
        box.addSpacing(4)
        self.nav_group = QButtonGroup(self)
        self.nav_buttons = []
        for index, (_, icon, title, hint) in enumerate(self.SECTIONS):
            button = QPushButton(panel)
            button.setProperty("role", "navItem")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            row = QHBoxLayout(button)
            row.setContentsMargins(10, 6, 10, 6)
            row.setSpacing(10)
            mark = icon_label(icon, 16, button, COLORS["primary"])
            texts = QVBoxLayout()
            texts.setSpacing(0)
            name = QLabel(title, button)
            name.setProperty("role", "navTitle")
            note = QLabel(hint, button)
            note.setProperty("role", "navHint")
            texts.addWidget(name)
            texts.addWidget(note)
            row.addWidget(mark)
            row.addLayout(texts, 1)
            for widget in (mark, name, note):
                widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            button.setMinimumHeight(row.sizeHint().height())
            self.nav_group.addButton(button, index)
            box.addWidget(button)
            self.nav_buttons.append(button)
        self.nav_group.idClicked.connect(self.show_section)
        return panel

    def _panel(self, title, subtitle):
        panel = QFrame()
        panel.setProperty("role", "panel")
        box = QVBoxLayout(panel)
        box.setContentsMargins(22, 18, 22, 18)
        box.setSpacing(12)
        head = QHBoxLayout()
        name = QLabel(title, panel)
        name.setProperty("role", "sectionTitle")
        chip = QLabel(panel)
        chip.setProperty("role", "chip")
        head.addWidget(name)
        head.addWidget(chip)
        head.addStretch()
        box.addLayout(head)
        note = QLabel(subtitle, panel)
        note.setProperty("role", "muted")
        note.setWordWrap(True)
        box.addWidget(note)
        return panel, box, chip

    @staticmethod
    def _tile(label, parent):
        tile = QFrame(parent)
        tile.setProperty("role", "tile")
        box = QVBoxLayout(tile)
        box.setContentsMargins(12, 10, 12, 10)
        box.setSpacing(2)
        caption = QLabel(label, tile)
        caption.setProperty("role", "tileLabel")
        line = QHBoxLayout()
        line.setSpacing(6)
        value = QLabel("—", tile)
        value.setProperty("role", "tileValue")
        unit = QLabel(tile)
        unit.setProperty("role", "tileUnit")
        line.addWidget(value)
        line.addWidget(unit, 0, Qt.AlignmentFlag.AlignBottom)
        line.addStretch()
        note = QLabel(tile)
        note.setProperty("role", "small")
        note.setWordWrap(True)
        box.addWidget(caption)
        box.addLayout(line)
        box.addWidget(note)
        tile.value, tile.unit, tile.note = value, unit, note
        return tile

    @staticmethod
    def _field(text, parent):
        label = QLabel(
            text.replace(" *", f" <span style='color:{COLORS['error']}'>*</span>"),
            parent,
        )
        label.setProperty("role", "field")
        return label

    @staticmethod
    def _info(text, parent):
        frame = QFrame(parent)
        frame.setProperty("role", "info")
        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(8)
        row.addWidget(
            icon_label(Icon.INFO, 14, frame, COLORS["muted"]),
            0,
            Qt.AlignmentFlag.AlignTop,
        )
        label = QLabel(text, frame)
        label.setProperty("role", "small")
        label.setWordWrap(True)
        row.addWidget(label, 1)
        return frame

    def _data_section(self):
        panel, box, self.data_chip = self._panel(
            "Cơ sở dữ liệu SQLite",
            "Nơi lưu chính thức hồ sơ, lịch nhắc và mẫu thông báo trên máy này.",
        )
        box.addWidget(self._field("Đường dẫn tệp cơ sở dữ liệu (chỉ đọc)", panel))
        row = QHBoxLayout()
        self.database_path = LineEdit(panel)
        self.database_path.setReadOnly(True)
        path = str(self.service.directory / "xaydungso.sqlite3")
        self.database_path.setText(path)
        self.database_path.setToolTip(path)
        self.open_folder_button = PushButton(Icon.FOLDER, "Mở thư mục", panel)
        self.open_folder_button.clicked.connect(self.open_directory)
        row.addWidget(self.database_path, 1)
        row.addWidget(self.open_folder_button)
        box.addLayout(row)
        overline = QLabel("THÔNG SỐ KỸ THUẬT", panel)
        overline.setProperty("role", "overline")
        box.addWidget(overline)
        grid = QGridLayout()
        grid.setSpacing(10)
        self.data_tiles = {}
        for index, (key, label) in enumerate(
            (
                ("connection", "Trạng thái kết nối"),
                ("version", "Phiên bản SQLite"),
                ("size", "Dung lượng tệp"),
                ("records", "Tổng số hồ sơ"),
                ("schema", "Phiên bản dữ liệu"),
                ("integrity", "Kiểm tra toàn vẹn"),
            )
        ):
            tile = self._tile(label, panel)
            grid.addWidget(tile, index // 2, index % 2)
            self.data_tiles[key] = tile
        box.addLayout(grid)
        box.addWidget(
            self._info(
                "Chỉ đọc thông tin, không sửa hoặc sao lưu dữ liệu. Kiểm tra toàn vẹn dùng "
                "PRAGMA quick_check của SQLite.",
                panel,
            )
        )
        box.addStretch()
        foot = QHBoxLayout()
        self.data_checked = QLabel(panel)
        self.data_checked.setProperty("role", "small")
        self.data_check_button = PushButton(Icon.SYNC, "Kiểm tra lại", panel)
        self.data_check_button.clicked.connect(self.refresh_status)
        foot.addWidget(self.data_checked)
        foot.addStretch()
        foot.addWidget(self.data_check_button)
        box.addLayout(foot)
        return panel

    def _telegram_section(self):
        panel, box, self.telegram_chip = self._panel(
            "Kết nối Telegram",
            "Bot gửi lịch nhắc tới cuộc trò chuyện đã chọn khi nhắc nền đang bật.",
        )
        tiles = QHBoxLayout()
        tiles.setSpacing(10)
        self.telegram_tiles = {}
        for key, label in (
            ("latency", "Thời gian phản hồi"),
            ("sent", "Tin nhắn gửi hôm nay"),
            ("chat", "Kênh nhận thông báo"),
        ):
            tile = self._tile(label, panel)
            tiles.addWidget(tile, 1)
            self.telegram_tiles[key] = tile
        box.addLayout(tiles)
        box.addWidget(self._field("Bot Token *", panel))
        self.token = PasswordLineEdit(panel)
        self.token.setPlaceholderText("Bot Token do @BotFather cấp")
        self.token.setMinimumHeight(34)
        box.addWidget(self.token)
        hint = QLabel("Được che khi nhập và lưu mã hóa theo tài khoản Windows.", panel)
        hint.setProperty("role", "small")
        box.addWidget(hint)
        box.addWidget(self._field("Chat ID *", panel))
        self.chat_id = LineEdit(panel)
        self.chat_id.setPlaceholderText("VD: 123456789 hoặc -1001234567890 (nhóm)")
        self.chat_id.setMinimumHeight(34)
        box.addWidget(self.chat_id)
        hint = QLabel(
            "ID cuộc trò chuyện nhận tin, không phải dãy số đầu Bot Token. Mở chat với "
            "bot và bấm Start trước khi kiểm tra.",
            panel,
        )
        hint.setProperty("role", "small")
        hint.setWordWrap(True)
        box.addWidget(hint)
        box.addWidget(
            self._info(
                "Kiểm tra kết nối không gửi tin; Gửi thử gửi một tin. Cả hai dùng ô đang "
                "nhập và không tự lưu — nhấn Lưu để lịch nhắc dùng cấu hình mới. Để trống "
                "cả hai ô để dùng cấu hình môi trường nếu có.",
                panel,
            )
        )
        box.addStretch()
        actions = QHBoxLayout()
        actions.addStretch()
        self.check_button = PushButton(Icon.SYNC, "Kiểm tra kết nối", panel)
        self.check_button.clicked.connect(self.check_telegram)
        self.test_button = PushButton(Icon.SEND, "Gửi thử", panel)
        self.test_button.clicked.connect(self.test_telegram)
        self.save_button = PrimaryPushButton(Icon.ACCEPT, "Lưu", panel)
        accent_button(self.save_button)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save)
        for button in (self.check_button, self.test_button, self.save_button):
            actions.addWidget(button)
        box.addLayout(actions)
        _chip(self.telegram_chip, "Chưa kiểm tra")
        return panel

    def _excel_section(self):
        panel, box, self.excel_chip = self._panel(
            "Sổ theo dõi Excel",
            "Ghi một chiều từ dữ liệu ứng dụng vào file .xlsx có sẵn theo mẫu 14 cột A–N.",
        )
        box.addWidget(self._field("Vị trí tệp Excel làm việc", panel))
        row = QHBoxLayout()
        self.excel_file = LineEdit(panel)
        self.excel_file.setPlaceholderText("Chọn file .xlsx có sẵn để ghi hồ sơ")
        self.excel_file.setMinimumHeight(34)
        browse = PushButton(Icon.FOLDER, "Duyệt vị trí…", panel)
        browse.setMinimumWidth(130)
        browse.clicked.connect(self.choose_file)
        row.addWidget(self.excel_file, 1)
        row.addWidget(browse)
        box.addLayout(row)
        box.addWidget(
            self._info(
                "File Excel tự cập nhật mỗi khi thêm, sửa hoặc xóa hồ sơ. Giữ các dòng có "
                "sẵn, thêm/sửa theo mã hồ sơ; chỉ xóa dòng do ứng dụng từng ghi. Đổi file "
                "áp dụng khi mở lại phần mềm.",
                panel,
            )
        )
        tiles = QHBoxLayout()
        tiles.setSpacing(10)
        self.excel_tiles = {}
        for key, label in (
            ("auto", "Tự động cập nhật"),
            ("modified", "Lần ghi file gần nhất"),
            ("written", "Số hồ sơ đã ghi"),
        ):
            tile = self._tile(label, panel)
            tiles.addWidget(tile, 1)
            self.excel_tiles[key] = tile
        box.addLayout(tiles)
        box.addStretch()
        actions = QHBoxLayout()
        actions.addStretch()
        self.open_excel_button = PushButton(Icon.DOCUMENT, "Mở file Excel", panel)
        self.open_excel_button.clicked.connect(self.open_excel)
        self.export_button = PushButton(Icon.SYNC, "Ghi lại ngay", panel)
        self.export_button.setToolTip("Ghi lại toàn bộ hồ sơ vào file Excel đang dùng")
        self.export_button.clicked.connect(self.export_now)
        self.export_button.setVisible(self.export is not None)
        self.excel_save_button = PrimaryPushButton(Icon.ACCEPT, "Lưu", panel)
        accent_button(self.excel_save_button)
        self.excel_save_button.clicked.connect(self.save)
        for button in (
            self.open_excel_button,
            self.export_button,
            self.excel_save_button,
        ):
            actions.addWidget(button)
        box.addLayout(actions)
        return panel

    # Navigation and status ----------------------------------------------------------

    def show_section(self, index):
        self.nav_buttons[index].setChecked(True)
        self.stack.setCurrentIndex(index)
        self.crumb.setText(f"/  {self.SECTIONS[index][2]}")
        self.feedback.setText("")  # Messages belong to the section that made them.

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_status()

    def refresh_status(self):
        if self.diagnostics is None:
            _chip(self.data_chip, "Không có thông tin")
            return
        _chip(self.data_chip, "Đang kiểm tra…", "busy")
        workbook = self.output_path

        def load():
            return (
                self.diagnostics.database_status(),
                self.diagnostics.telegram_sent_today(),
                self.diagnostics.excel_status(workbook),
            )

        self.runner.submit(load, self._status, self._status_failed)

    def _status(self, loaded):
        database, sent_today, excel = loaded
        ok = database.integrity == "ok"
        _chip(
            self.data_chip,
            "●  Hoạt động bình thường" if ok else "●  Có lỗi toàn vẹn",
            "ok" if ok else "bad",
        )
        values = {
            "connection": ("● Kết nối được", "", "Mở và đọc được tệp"),
            "version": (
                f"v{database.sqlite_version}",
                "",
                "Thư viện SQLite của Python",
            ),
            "size": (f"{database.size_bytes / 1_048_576:.2f}", "MB", ""),
            "records": (str(database.records), "bản ghi", ""),
            "schema": (f"v{database.schema_version}", "", "Tự nâng cấp khi mở app"),
            "integrity": (
                "OK" if ok else "Lỗi",
                "",
                "PRAGMA quick_check" if ok else database.integrity[:120],
            ),
        }
        for key, (value, unit, note) in values.items():
            tile = self.data_tiles[key]
            tile.value.setText(value)
            tile.unit.setText(unit)
            tile.note.setText(note)
        self.data_checked.setText(
            f"Kiểm tra gần nhất: hôm nay, {database.checked_at:%H:%M:%S}"
        )
        sent = self.telegram_tiles["sent"]
        sent.value.setText(str(sent_today))
        sent.unit.setText("thông báo")
        sent.note.setText("Đã gửi thành công qua Telegram")
        auto = self.excel_tiles["auto"]
        auto.value.setText("Bật")
        auto.note.setText("Ghi khi lưu hoặc xóa hồ sơ")
        modified = self.excel_tiles["modified"]
        written = self.excel_tiles["written"]
        if excel.exists:
            _chip(self.excel_chip, "●  Đang dùng", "ok")
            modified.value.setText(f"{excel.modified_at:%d/%m/%Y}")
            modified.unit.setText(f"{excel.modified_at:%H:%M}")
            modified.note.setText("Theo thời gian sửa file")
            written.value.setText(str(excel.written_records))
            written.unit.setText("hồ sơ")
            written.note.setText("Do ứng dụng ghi vào file này")
        else:
            _chip(self.excel_chip, "●  Không tìm thấy file", "bad")
            for tile in (modified, written):
                tile.value.setText("—")
                tile.unit.setText("")
            modified.note.setText("Chọn file .xlsx có sẵn rồi Lưu")
            written.note.setText("")

    def _status_failed(self, _error):
        _chip(self.data_chip, "●  Không đọc được", "bad")
        self.data_checked.setText(
            "Không đọc được cơ sở dữ liệu. Kiểm tra quyền truy cập thư mục dữ liệu."
        )

    # Actions (behaviour unchanged from the previous page) -------------------------

    def show_error(self, error):
        self.feedback.setText(
            str(error)
            if isinstance(error, (ValidationError, NotificationError))
            else "Không thể thực hiện. Vui lòng kiểm tra file/quyền truy cập và thử lại."
        )

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file Excel có sẵn", self.excel_file.text(), "Excel (*.xlsx)"
        )
        if path:
            self.excel_file.setText(path)

    def open_directory(self):
        if not QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(self.service.directory))
        ):
            self.feedback.setText("Không mở được thư mục dữ liệu.")

    def open_excel(self):
        path = self.excel_file.text().strip()
        if not path:
            self.feedback.setText("Chưa chọn file Excel.")
        elif not QDesktopServices.openUrl(QUrl.fromLocalFile(path)):
            self.feedback.setText(f"Không mở được file Excel. File ở: {path}")

    def export_now(self):
        self.export_button.setEnabled(False)
        self.feedback.setText("Đang ghi lại file Excel…")

        def done(error):
            self.export_button.setEnabled(True)
            self.feedback.setText(error or "Đã ghi lại toàn bộ hồ sơ vào file Excel.")
            self.refresh_status()

        def failed(error):
            self.export_button.setEnabled(True)
            self.show_error(error)

        self.runner.submit(self.export, done, failed)

    def load(self):
        self.save_button.setEnabled(False)
        self.runner.submit(self.service.load, self.loaded, self.show_error)

    def loaded(self, value):
        self.token.setText(value.telegram_token)
        self.chat_id.setText(value.telegram_chat_id)
        self.excel_file.setText(str(self.service.export_path(value)))
        self.feedback.setText("")
        self.save_button.setEnabled(True)

    def save(self):
        value = Preferences(
            self.excel_file.text(),
            self.token.text(),
            self.chat_id.text(),
            "merge",
        )
        self.save_button.setEnabled(False)
        self.excel_save_button.setEnabled(False)
        self.runner.submit(lambda: self.service.save(value), self.saved, self.failed)

    def saved(self, _):
        self.save_button.setEnabled(True)
        self.excel_save_button.setEnabled(True)
        self.feedback.setText(
            "Đã lưu cài đặt. Telegram áp dụng ở lần gửi tiếp theo khi nhắc nền đang bật. "
            "Mở lại phần mềm để dùng file Excel đã chọn."
        )

    def failed(self, error):
        self.save_button.setEnabled(True)
        self.excel_save_button.setEnabled(True)
        self.show_error(error)

    def check_telegram(self):
        self._telegram_action(False)

    def test_telegram(self):
        self._telegram_action(True)

    def _telegram_action(self, send):
        token, chat = self.token.text(), self.chat_id.text()
        self.check_button.setEnabled(False)
        self.test_button.setEnabled(False)
        _chip(self.telegram_chip, "●  Đang kết nối…", "busy")
        self.feedback.setText(
            "Đang gửi một tin kiểm tra Telegram…"
            if send
            else "Đang kiểm tra Telegram (không gửi tin nhắn)…"
        )
        started = time.perf_counter()

        def success(result):
            self.check_button.setEnabled(True)
            self.test_button.setEnabled(True)
            message, name = result if isinstance(result, tuple) else (result, None)
            elapsed = round((time.perf_counter() - started) * 1000)
            _chip(self.telegram_chip, "●  Đã kết nối", "ok")
            latency = self.telegram_tiles["latency"]
            latency.value.setText(str(elapsed))
            latency.unit.setText("ms")
            latency.note.setText(
                "Lần " + ("gửi thử" if send else "kiểm tra") + " vừa rồi"
            )
            if name:
                chat = self.telegram_tiles["chat"]
                chat.value.setText(name)
                chat.note.setText("Theo Chat ID đang nhập")
            self.feedback.setText(message)
            if send:
                self.refresh_status()

        def failure(error):
            self.check_button.setEnabled(True)
            self.test_button.setEnabled(True)
            _chip(self.telegram_chip, "●  Lỗi kết nối", "bad")
            self.show_error(error)

        action = self.service.test_telegram if send else self.service.check_telegram
        self.runner.submit(lambda: action(token, chat), success, failure)
