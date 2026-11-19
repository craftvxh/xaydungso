"""Confirmation box: only the card is shown; the app behind is lightly dimmed."""

from PyQt6.QtGui import QColor
from qfluentwidgets import MessageBox, setCustomStyleSheet

from xaydungso.presentation.theme import qss, ui_font

# Same type scale as CardDialog titles and body text.
TITLE = qss("QLabel { font-family: @font; font-size: @fs_heading; font-weight: 600; }")
BODY = qss("QLabel { font-family: @font; font-size: @fs_body; }")

# DESIGN.md "Level 4" modal veil: #0F172A at ~30% instead of Fluent's light
# theme default (white 60%), which the app's white theme made fully opaque.
VEIL = QColor(15, 23, 42, 77)
DANGER = qss(
    "PrimaryPushButton { background-color: #b91c1c; color: #ffffff;"
    " border: 1px solid #b91c1c; border-radius: 6px; }"
    " PrimaryPushButton:hover { background-color: #991b1b; border-color: #991b1b; }"
    " PrimaryPushButton:pressed { background-color: #7f1d1d; }"
)


class ConfirmBox(MessageBox):
    def __init__(self, title, content, parent, *, yes="Đồng ý", no="Hủy", danger=True):
        super().__init__(title, content, parent)
        # Keep Fluent's own look: skip the app-wide forced white restyling.
        self.setProperty("xdsStyled", True)
        self.setMaskColor(VEIL)
        self.titleLabel.setStyleSheet(TITLE)
        self.contentLabel.setStyleSheet(BODY)
        for button in (self.yesButton, self.cancelButton):
            button.setFont(ui_font())
        self.yesButton.setText(yes)
        self.cancelButton.setText(no)
        if danger:
            self.yesButton.setProperty("xdsStyled", True)
            setCustomStyleSheet(self.yesButton, DANGER, DANGER)
        # The safe choice gets keyboard focus.
        self.cancelButton.setFocus()
