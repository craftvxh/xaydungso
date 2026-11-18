"""Frameless rounded dialog frame shared by the Stitch-style editors."""

from PyQt6.QtCore import QPoint, QSize, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    TransparentToolButton,
    setCustomStyleSheet,
)

from xaydungso.presentation.forms import SavingDialog
from xaydungso.presentation.icons import Icon
from xaydungso.presentation.motion import fade_in_window
from xaydungso.presentation.record_widgets import icon_label
from xaydungso.presentation.theme import COLORS, accent_button, qss, styled

FRAME_SHEET = """
QFrame#dialogCard { background: @surface; border: 1px solid @outline_soft;
    border-radius: 12px; }
QFrame#dialogHeader { background: @surface_low; border: none;
    border-bottom: 1px solid @outline_soft; border-top-left-radius: 12px;
    border-top-right-radius: 12px; }
QFrame#dialogFooter { background: @surface; border: none;
    border-top: 1px solid @outline_soft; border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px; }
QWidget#dialogBody, QScrollArea { background: transparent; border: none; }
QLabel { background: transparent; color: @text; font-size: 12px; }
QLabel#dialogTitle { font-size: 17px; font-weight: 600; }
QLabel#dialogSubtitle { color: @muted; font-size: 11px; }
QLabel#dialogIcon { background: @primary_container; border-radius: 6px; }
QLabel#formError { color: @error; font-size: 12px; }
"""
MARGIN = 16  # Transparent margin around the card for its shadow.


class CardDialog(SavingDialog):
    """Header (icon, title, subtitle, close), scrolling body, footer buttons."""

    def __init__(
        self,
        title,
        icon,
        *,
        subtitle="",
        save_text="Lưu",
        cancel_text="Hủy",
        size=(900, 780),
        sheet="",
        parent=None,
    ):
        super().__init__(parent)
        self.saving = False
        self._drag = None
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        styled(self, FRAME_SHEET + sheet)
        self.resize(*size)

        shell = QVBoxLayout(self)
        shell.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        card = QFrame(self)
        card.setObjectName("dialogCard")
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(15, 23, 42, 60))
        card.setGraphicsEffect(shadow)
        shell.addWidget(card)
        outer = QVBoxLayout(card)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.header = QFrame(card)
        self.header.setObjectName("dialogHeader")
        header = QHBoxLayout(self.header)
        header.setContentsMargins(20, 12, 14, 12)
        header.setSpacing(10)
        badge = icon_label(icon, 16, self.header, COLORS["on_primary"])
        badge.setObjectName("dialogIcon")
        badge.setFixedSize(32, 32)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        heading = QLabel(title, self.header)
        heading.setObjectName("dialogTitle")
        titles.addWidget(heading)
        if subtitle:
            caption = QLabel(subtitle, self.header)
            caption.setObjectName("dialogSubtitle")
            titles.addWidget(caption)
        self.close_button = TransparentToolButton(Icon.CLOSE, self.header)
        self.close_button.setIconSize(QSize(12, 12))
        self.close_button.setToolTip("Đóng")
        self.close_button.clicked.connect(self.reject)
        header.addWidget(badge)
        header.addLayout(titles)
        header.addStretch()
        header.addWidget(self.close_button)
        outer.addWidget(self.header)

        scroll = ScrollArea(card)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("dialogBody")
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(24, 18, 24, 18)
        self.body.setSpacing(12)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        footer = QFrame(card)
        footer.setObjectName("dialogFooter")
        self.footer = QHBoxLayout(footer)
        self.footer.setContentsMargins(20, 12, 20, 12)
        self.footer.setSpacing(10)
        self.footer_left = QVBoxLayout()
        self.footer_left.setSpacing(2)
        self.error = QLabel(footer)
        self.error.setObjectName("formError")
        self.error.setWordWrap(True)
        self.footer_left.addWidget(self.error)
        self.cancel_button = PushButton(cancel_text, footer)
        self.cancel_button.setMinimumHeight(36)
        soft = qss(
            "PushButton { background: @surface_container; border: none;"
            " border-radius: 6px; color: @text; padding: 0 18px; }"
            " PushButton:hover { background: @surface_highest; }"
            " PushButton:pressed { background: @outline_soft; }"
        )
        setCustomStyleSheet(self.cancel_button, soft, soft)
        self.save_button = PrimaryPushButton(save_text, footer)
        accent_button(self.save_button)
        self.save_button.setMinimumSize(110, 36)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self._submit)
        self.footer.addLayout(self.footer_left, 1)
        self.footer.addWidget(self.cancel_button)
        self.footer.addWidget(self.save_button)
        outer.addWidget(footer)

    # Frameless window behaviour ---------------------------------------------------

    def mousePressEvent(self, event):
        area = self.header.geometry().translated(MARGIN, MARGIN)
        if area.contains(event.position().toPoint()):
            self._drag = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag = None
        super().mouseReleaseEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        parent = self.parentWidget()
        if parent is not None:
            centre = parent.frameGeometry().center()
            self.move(centre - QPoint(self.width() // 2, self.height() // 2))
        fade_in_window(self)
