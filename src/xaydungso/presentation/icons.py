"""Windows 11 icons from Microsoft's Fluent UI System Icons (MIT, see icons/LICENSE).

Each member keeps the name of the qfluentwidgets ``FluentIcon`` it replaces, so
``.icon()``, ``.colored()`` and ``.render()`` work unchanged. Files are the 20px
"regular" SVGs from github.com/microsoft/fluentui-system-icons.
"""

from enum import Enum
from pathlib import Path

from PyQt6.QtGui import QColor, QIcon
from qfluentwidgets import FluentIconBase, Theme, isDarkTheme
from qfluentwidgets.common.icon import SvgIconEngine, writeSvg

ICON_DIR = Path(__file__).resolve().parent / "icons"
# Application logo (window, taskbar, Alt+Tab); the .exe uses packaging/xaydungso.ico.
LOGO = Path(__file__).resolve().parent / "logo.svg"
LIGHT_FILL, DARK_FILL = "#212121", "#ffffff"


def _fill(theme):
    dark = theme == Theme.DARK or (theme == Theme.AUTO and isDarkTheme())
    return DARK_FILL if dark else LIGHT_FILL


def colored_icon(icon, color):
    """A QIcon of any Fluent icon in one colour (``colored().icon()`` is not)."""
    return icon.icon(color=QColor(color))


class Icon(FluentIconBase, Enum):
    ACCEPT = "checkmark"
    ADD = "add"
    CALENDAR = "calendar"
    CLOSE = "dismiss"
    DELETE = "delete"
    DOCUMENT = "document"
    EDIT = "edit"
    FOLDER = "folder"
    HISTORY = "clock"
    HOME = "home"
    INFO = "info"
    LAYOUT = "building"
    LIBRARY = "library"
    PAUSE = "pause"
    PLAY = "play"
    RINGER = "alert"
    SCROLL = "arrow_sort"
    SEND = "send"
    SETTING = "settings"
    SYNC = "arrow_sync"
    VIEW = "eye"

    def path(self, theme=Theme.AUTO):
        return str(ICON_DIR / f"{self.value}.svg")

    # One SVG per icon: apply the theme's fill (Fluent ships black/white files;
    # primary buttons ask for the DARK theme to get white icons).
    def icon(self, theme=Theme.AUTO, color=None):
        fill = QColor(color).name() if color else _fill(theme)
        return QIcon(SvgIconEngine(writeSvg(self.path(theme), fill=fill)))

    def render(self, painter, rect, theme=Theme.AUTO, indexes=None, **attributes):
        attributes.setdefault("fill", _fill(theme))
        super().render(painter, rect, theme, indexes, **attributes)
