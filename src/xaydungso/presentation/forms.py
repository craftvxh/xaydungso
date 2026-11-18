"""Fluent input widgets with validation delegated to the domain."""

from datetime import datetime, timedelta

from PyQt6.QtCore import QDateTime, pyqtSignal
from PyQt6.QtWidgets import (
    QDateTimeEdit,
    QDialog,
    QHBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    ComboBox,
    LineEdit,
)

from xaydungso.domain.records import ValidationError
from xaydungso.domain.reminders import LOCAL_ZONE

TIME_FORMAT = "%d/%m/%Y %H:%M"
TIME_HINT = "dd/mm/yyyy hh:mm, VD: 18/11/2026 08:30"


def time_text(offset=timedelta()):
    """Current Vietnam time as dd/mm/yyyy hh:mm text for auto-filled inputs."""
    return (datetime.now(LOCAL_ZONE) + offset).strftime(TIME_FORMAT)


def parse_time(text, label):
    """Parse dd/mm/yyyy hh:mm (24-hour) as Vietnam time; raise a user message."""
    normalized = " ".join(text.split())
    try:
        parsed = datetime.strptime(normalized, TIME_FORMAT)
        if parsed.strftime(TIME_FORMAT) != normalized:  # Require zero-padded fields.
            raise ValueError
        return parsed.replace(tzinfo=LOCAL_ZONE)
    except ValueError:
        raise ValidationError(
            f"{label} phải đúng định dạng dd/mm/yyyy hh:mm, VD: 18/11/2026 08:30."
        ) from None


def deadline_input(parent, value=""):
    widget = QDateTimeEdit(parent)
    widget.setCalendarPopup(True)
    widget.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
    initial = (
        datetime.fromisoformat(value).astimezone(LOCAL_ZONE)
        if value
        else datetime.now(LOCAL_ZONE) + timedelta(days=1)
    )
    widget.setDateTime(
        QDateTime.fromString(
            initial.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd HH:mm:ss"
        )
    )
    return widget


class DurationInput(QWidget):
    """Lead time before the deadline: presets, or a custom number of seconds."""

    LABELS = (
        "Tự nhập (giây)",
        "Trước 10 giây (thử)",
        "Trước 1 giờ",
        "Trước 12 giờ",
        "Trước 24 giờ",
    )
    VALUES = (None, 10, 3600, 43200, 86400)

    def __init__(self, seconds=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.presets = ComboBox(self)
        self.presets.addItems(self.LABELS)
        self.seconds = LineEdit(self)
        self.seconds.setPlaceholderText("Số giây nguyên dương, VD: 3600 = 1 giờ")
        self.seconds.setText("" if seconds is None else str(seconds))
        self.presets.currentIndexChanged.connect(self._preset)
        layout.addWidget(self.presets, 1)
        layout.addWidget(self.seconds, 1)
        preset = self.VALUES.index(seconds) if seconds in self.VALUES else 0
        self.presets.setCurrentIndex(preset)
        self._preset(preset)

    def _preset(self, index):
        value = self.VALUES[index]
        if value is not None:
            self.seconds.setText(str(value))
        # The seconds box is only needed for a custom value.
        self.seconds.setVisible(value is None)

    def value(self, required=False):
        text = self.seconds.text().strip()
        if not text and not required:
            return None
        try:
            value = int(text)
        except ValueError:
            raise ValidationError("Thời lượng phải là số giây nguyên dương.") from None
        if value <= 0:
            raise ValidationError("Thời lượng phải lớn hơn 0.")
        return value


class SavingDialog(QDialog):
    """Validate via value(), emit submitted, and block closing while saving."""

    submitted = pyqtSignal(object)

    def _submit(self):
        try:
            value = self.value()
        except ValidationError as error:
            self.error.setText(str(error))
            return
        self.set_saving(True)
        self.submitted.emit(value)

    def set_saving(self, saving):
        self.saving = saving
        self.save_button.setEnabled(not saving)
        self.cancel_button.setEnabled(not saving)

    def reject(self):
        if not self.saving:
            super().reject()

    def closeEvent(self, event):
        if self.saving:
            event.ignore()
        else:
            super().closeEvent(event)
