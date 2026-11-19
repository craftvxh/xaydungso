"""Notification-area (tray) icon while the app is open.

Closing the window hides it to the tray instead of quitting; double-clicking
the icon or "Mở" brings it back, "Thoát" quits. No notification is shown
when hiding (user's choice). The reminder worker is a separate process and is not affected by either.
"""

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QSystemTrayIcon
from qfluentwidgets import Action, SystemTrayMenu

from xaydungso.presentation.icons import LOGO


class AppTray(QSystemTrayIcon):
    def __init__(self, window, on_quit):
        super().__init__(QIcon(str(LOGO)), window)
        self.window = window
        self.setToolTip("Xây Dựng Số")
        self.menu = SystemTrayMenu(parent=window)
        # Text only, no icons (user's choice).
        self.open_action = Action("Mở", self.menu, triggered=self.open_window)
        self.quit_action = Action("Thoát", self.menu, triggered=on_quit)
        self.menu.addActions([self.open_action, self.quit_action])
        self.setContextMenu(self.menu)
        self.activated.connect(self._activated)

    def _activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_window()

    def open_window(self):
        self.window.bring_to_front()
