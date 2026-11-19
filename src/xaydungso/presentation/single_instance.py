"""One GUI per data directory: a second launch brings the running window back.

Needed since closing the window only hides it to the tray. Uses a Qt local
server (a named pipe on Windows) named after the user and data directory, so a
separate data directory (e.g. tests) never talks to the user's open app.
"""

import ctypes
import getpass
import hashlib
from pathlib import Path

from PyQt6.QtNetwork import QLocalServer, QLocalSocket

ASFW_ANY = -1


def instance_name(directory: Path) -> str:
    key = str(directory.resolve()).casefold().encode("utf-8")
    return f"xaydungso-gui-{getpass.getuser()}-{hashlib.sha256(key).hexdigest()[:16]}"


def notify_running(name: str) -> bool:
    """True when another GUI is running; it is asked to show its window."""
    socket = QLocalSocket()
    socket.connectToServer(name)
    if not socket.waitForConnected(500):
        return False
    # Let the running instance take the foreground instead of only flashing.
    ctypes.windll.user32.AllowSetForegroundWindow(ASFW_ANY)
    socket.write(b"show")
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True


class InstanceServer(QLocalServer):
    def __init__(self, on_show, name: str, parent=None):
        super().__init__(parent)
        self.on_show = on_show
        QLocalServer.removeServer(name)  # A crashed run may leave a stale name.
        self.listen(name)
        self.newConnection.connect(self._connected)

    def _connected(self):
        while (socket := self.nextPendingConnection()) is not None:
            socket.disconnected.connect(socket.deleteLater)
            self.on_show()
