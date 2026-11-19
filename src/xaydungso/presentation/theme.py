"""One fixed white surface / black text theme for native and Fluent widgets."""

import re
import weakref

from PyQt6 import sip
from PyQt6.QtCore import QEvent, QObject, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication, QWidget
from qfluentwidgets import Theme, qconfig, setCustomStyleSheet, setTheme, setThemeColor


def white_palette() -> QPalette:
    palette = QPalette()
    for group in (
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Inactive,
        QPalette.ColorGroup.Disabled,
    ):
        for role in (
            QPalette.ColorRole.Window,
            QPalette.ColorRole.Base,
            QPalette.ColorRole.AlternateBase,
            QPalette.ColorRole.Button,
            QPalette.ColorRole.ToolTipBase,
            QPalette.ColorRole.Highlight,
        ):
            palette.setColor(group, role, QColor("#ffffff"))
        for role in (
            QPalette.ColorRole.WindowText,
            QPalette.ColorRole.Text,
            QPalette.ColorRole.ButtonText,
            QPalette.ColorRole.ToolTipText,
            QPalette.ColorRole.PlaceholderText,
            QPalette.ColorRole.HighlightedText,
            QPalette.ColorRole.Link,
            QPalette.ColorRole.LinkVisited,
        ):
            palette.setColor(group, role, QColor("#000000"))
    return palette


# Light accent tokens from the approved records-page mockup. The base surface
# stays white with near-black text; tints only mark headers, panes and badges.
COLORS = {
    "primary": "#1d2b3e",
    "primary_container": "#334155",
    "on_primary": "#ffffff",
    "surface": "#ffffff",
    "surface_low": "#f2f3ff",
    "surface_container": "#eaedff",
    "surface_highest": "#dae2fd",
    "outline": "#c5c6cd",
    "outline_soft": "#e4e5eb",
    "page": "#faf8ff",
    "surface_faint": "#f7f8ff",
    "secondary": "#505f76",
    "secondary_container": "#d0e1fb",
    "text": "#131b2e",
    "muted": "#44474c",
    "error": "#b91c1c",
    "pending_bg": "#fef3c7",
    "pending_fg": "#b45309",
    "done_bg": "#dcfce7",
    "done_fg": "#15803d",
}

# Typography: change the families here to restyle the whole app. One type
# scale (px) for every page and dialog; QSS uses the @fs_* / @font / @mono
# tokens, Python code uses ui_font() / mono_font().
FONT_FAMILIES = ["Segoe UI", "Microsoft YaHei"]
MONO_FAMILIES = ["Consolas", "Courier New"]
TYPE = {
    "fs_page": "22px",  # Page titles.
    "fs_heading": "16px",  # Dialog, panel and section titles.
    "fs_stat": "24px",  # Big numbers on metric cards.
    "fs_body": "13px",  # Labels, table cells, buttons, inputs.
    "fs_small": "12px",  # Muted notes, captions, footers.
    "fs_tiny": "11px",  # Chips, badges, uppercase group labels.
    "fs_mono": "12px",  # Record codes and date-times.
    "font": ", ".join(f'"{name}"' for name in FONT_FAMILIES),
    "mono": ", ".join(f'"{name}"' for name in MONO_FAMILIES),
}
TOKENS = {**COLORS, **TYPE}


def _px(token: str) -> int:
    return int(TYPE[token].removesuffix("px"))


def ui_font(token="fs_body", weight=QFont.Weight.Normal) -> QFont:
    font = QFont()
    font.setFamilies(FONT_FAMILIES)
    font.setPixelSize(_px(token))
    font.setWeight(weight)
    return font


def mono_font(token="fs_mono", weight=QFont.Weight.Normal) -> QFont:
    font = ui_font(token, weight)
    font.setFamilies(MONO_FAMILIES)
    return font


def _in_styled(widget) -> bool:
    """Widgets inside a styled container keep that container's accent QSS."""
    while widget is not None:
        if widget.property("xdsStyled"):
            return True
        widget = widget.parentWidget()
    return False


def qss(text: str) -> str:
    """Replace @token names with COLORS/TYPE values (longest names first)."""
    for name in sorted(TOKENS, key=len, reverse=True):
        text = text.replace(f"@{name}", TOKENS[name])
    return text


def styled(widget, sheet: str):
    """Opt a container (and its children) out of the forced white sheet."""
    widget.setProperty("xdsStyled", True)
    # One family for everything inside and the body size for Fluent controls
    # (their own default is 14px). Labels get sizes from each page's QLabel
    # rules: a nested container's sheet beats its parent's, so no catch-all
    # label size here. [mono="true"] marks record codes and date-times.
    widget.setStyleSheet(
        qss(
            "* { font-family: @font; }\n"
            "QAbstractButton, QLineEdit, QTextEdit, QPlainTextEdit,"
            " QAbstractSpinBox, QComboBox { font-size: @fs_body; }\n"
            '*[mono="true"] { font-family: @mono; }\n' + sheet
        )
    )
    return widget


def set_mono(widget):
    """Render a widget's text in the monospace family (codes, date-times)."""
    widget.setProperty("mono", True)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    return widget


def accent_button(button):
    """Dark slate primary action (mockup primary) instead of forced white."""
    sheet = qss(
        "PrimaryPushButton { background-color: @primary_container; color: @on_primary;"
        " border: 1px solid @primary_container; border-radius: 6px; }"
        " PrimaryPushButton:hover { background-color: @primary;"
        " border-color: @primary; }"
        " PrimaryPushButton:pressed { background-color: @primary; }"
        " PrimaryPushButton:disabled { background-color: @outline; }"
    )
    button.setProperty("xdsStyled", True)
    setCustomStyleSheet(button, sheet, sheet)
    return button


class WhiteTheme(QObject):
    def eventFilter(self, widget, event):
        if event.type() == QEvent.Type.Polish and isinstance(widget, QWidget):
            if not widget.property("xdsWhiteThemeQueued"):
                widget.setProperty("xdsWhiteThemeQueued", True)
                reference = weakref.ref(widget)
                QTimer.singleShot(0, lambda: self.apply(reference))
        return super().eventFilter(widget, event)

    def apply(self, reference):
        widget = reference()
        if widget is None or sip.isdeleted(widget) or _in_styled(widget):
            return
        widget.setPalette(white_palette())
        if not widget.property("xdsWhiteTheme"):
            widget.setProperty("xdsWhiteTheme", True)
            name = widget.objectName()
            selector = (
                f"QWidget#{name}"
                if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9-]*", name)
                else 'QWidget[xdsWhiteTheme="true"][xdsWhiteTheme="true"][xdsWhiteTheme="true"]'
            )
            states = ", ".join(
                selector + state
                for state in (
                    "",
                    ":hover",
                    ":pressed",
                    ":checked",
                    ":disabled",
                    ":focus",
                    ":selected",
                )
            )
            # Append after Fluent's own sheet so buttons/dialogs cannot restore
            # white text or tinted backgrounds over the application palette.
            widget.setStyleSheet(
                widget.styleSheet()
                + f"""
{states} {{
background-color: #ffffff;
color: #000000;
placeholder-text-color: #000000;
selection-background-color: #ffffff;
selection-color: #000000;
}}
{selector}::section, {selector}::item, {selector}::item:selected {{
background-color: #ffffff;
color: #000000;
}}
{selector}:focus {{ border-color: #000000; }}
"""
            )


def configure_theme(app: QApplication) -> None:
    app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
    app.setStyle("Fusion")
    app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    setTheme(Theme.LIGHT, save=False)
    # Navy primary from the design: nav indicator, focus and checked accents.
    setThemeColor(QColor(COLORS["primary"]), save=False)
    qconfig.set(qconfig.fontFamilies, FONT_FAMILIES, save=False)
    app.setPalette(white_palette())
    app.setStyleSheet(
        "QWidget { background-color: #ffffff; color: #000000; } QToolTip { background-color: #ffffff; color: #000000; border: 1px solid #000000; }"
    )
    app.white_theme = WhiteTheme(app)
    app.installEventFilter(app.white_theme)
