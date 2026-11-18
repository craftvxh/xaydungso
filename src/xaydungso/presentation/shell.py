"""Window chrome from the approved design: tinted title bar/sidebar, badges."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget
from qfluentwidgets import (
    InfoBadge,
    InfoBadgePosition,
    setCustomStyleSheet,
)

from xaydungso.presentation.theme import COLORS

SUBTITLE = "Giải pháp chuyển đổi số"


def _tint(widget: QWidget, name: str):
    widget.setProperty("xdsStyled", True)
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    # An ID selector outranks Fluent's NavigationPanel[menu=...] rules; children
    # (e.g. scroll viewports) would otherwise take the app-wide white rule.
    widget.setObjectName(name)
    sheet = (
        "QWidget { background-color: transparent; }\n"
        f"#{name} {{ background-color: {COLORS['surface_low']}; border: none; }}"
    )
    widget.setStyleSheet(widget.styleSheet() + "\n" + sheet)
    # Fluent re-applies its own sheet to managed widgets; keep the tint appended.
    setCustomStyleSheet(widget, sheet, sheet)


def style_shell(window, name: str):
    """Apply the design's chrome to a FluentWindow (title bar, sidebar)."""
    title_bar = window.titleBar
    _tint(title_bar, "xdsTitleBar")
    title_bar.titleLabel.setText(f"{name} - {SUBTITLE}")
    title_bar.titleLabel.setStyleSheet(
        f"QLabel {{ background: transparent; color: {COLORS['text']};"
        ' font: 600 12px "Segoe UI"; padding: 0 0 0 4px; }'
    )
    title_bar.iconLabel.hide()
    for button in (title_bar.minBtn, title_bar.maxBtn, title_bar.closeBtn):
        button.setNormalColor(QColor(COLORS["muted"]))
        button.setHoverColor(QColor(COLORS["text"]))
        button.setPressedColor(QColor(COLORS["text"]))
        button.setNormalBackgroundColor(QColor(0, 0, 0, 0))
        button.setHoverBackgroundColor(QColor(COLORS["surface_container"]))
        button.setPressedBackgroundColor(QColor(COLORS["surface_highest"]))
    title_bar.closeBtn.setHoverColor(QColor("#ffffff"))
    title_bar.closeBtn.setHoverBackgroundColor(QColor("#ba1a1a"))
    title_bar.closeBtn.setPressedBackgroundColor(QColor("#93000a"))

    navigation = window.navigationInterface
    _tint(navigation, "xdsNavigation")
    _tint(navigation.panel, "xdsNavigationPanel")
    navigation.panel.setReturnButtonVisible(False)


def nav_badge(window, page, alert=False):
    """Count badge on a sidebar item; hidden while the count is zero."""
    target = window.navigationInterface.widget(page.objectName())
    if alert:
        badge = InfoBadge.attension(
            "0", window.navigationInterface, target, InfoBadgePosition.NAVIGATION_ITEM
        )
    else:
        badge = InfoBadge.custom(
            "0",
            QColor(COLORS["primary_container"]),
            QColor(COLORS["primary_container"]),
            window.navigationInterface,
            target,
            InfoBadgePosition.NAVIGATION_ITEM,
        )
    badge.hide()
    return badge


def set_badge(badge, count):
    badge.setText(str(count))
    badge.adjustSize()
    badge.setVisible(count > 0)
