"""Start the reminder worker at Windows sign-in via a Startup-folder shortcut.

The shortcut lives in the user's Startup folder (no registry, no admin rights),
so it also appears in Task Manager → Startup apps. It only runs the hidden
reminder worker; the window is opened by the user as usual. On the first app
start the shortcut is created once; after that the user's choice is kept.
"""

import base64
import os
import subprocess
import sys
from pathlib import Path

from xaydungso.infrastructure.worker_process import worker_command

SHORTCUT_NAME = "Xây Dựng Số - Nhắc nền.lnk"
MARKER = "startup-configured"  # In the data directory: first-run choice was applied.
DEV_ICON = Path(__file__).resolve().parents[3] / "packaging" / "xaydungso.ico"

# Values arrive as base64 UTF-8 environment variables (never interpolated into
# the script, and Vietnamese text survives the console code page).
SCRIPT = """
$ErrorActionPreference = 'Stop'
function Get-Value($name) {
  [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(
    [Environment]::GetEnvironmentVariable($name)))
}
try {
  $link = (New-Object -ComObject WScript.Shell).CreateShortcut((Get-Value 'XDS_LINK'))
  $link.TargetPath = Get-Value 'XDS_TARGET'
  $link.Arguments = Get-Value 'XDS_ARGUMENTS'
  $link.WorkingDirectory = Get-Value 'XDS_DIRECTORY'
  $link.IconLocation = Get-Value 'XDS_ICON'
  $link.Description = Get-Value 'XDS_DESCRIPTION'
  $link.WindowStyle = 7
  $link.Save()
  exit 0
} catch { exit 1 }
"""


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def startup_folder() -> Path:
    return (
        Path(os.environ["APPDATA"])
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "Startup"
    )


class StartupShortcut:
    def __init__(self, directory: Path, folder: Path | None = None, run=None):
        self.directory = directory
        self.path = (folder or startup_folder()) / SHORTCUT_NAME
        self.run = run or subprocess.run

    def enabled(self) -> bool:
        return self.path.is_file()

    def enable(self) -> None:
        target, *arguments = worker_command(self.directory)
        if getattr(sys, "frozen", False):
            icon, working = f"{sys.executable},0", Path(sys.executable).parent
        else:
            icon = f"{DEV_ICON},0" if DEV_ICON.is_file() else f"{target},0"
            working = DEV_ICON.parents[1]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # WScript.Shell cannot save a .lnk with a Vietnamese file name: save an
        # ASCII name, then rename it in Python.
        staging = self.path.with_name("xaydungso-startup.tmp.lnk")
        encoded = base64.b64encode(SCRIPT.encode("utf-16-le")).decode("ascii")
        powershell = os.path.join(
            os.environ["SystemRoot"],
            "System32",
            "WindowsPowerShell",
            "v1.0",
            "powershell.exe",
        )
        try:
            result = self.run(
                [
                    powershell,
                    "-NoProfile",
                    "-NonInteractive",
                    "-EncodedCommand",
                    encoded,
                ],
                env={
                    **os.environ,
                    "XDS_LINK": _b64(str(staging)),
                    "XDS_TARGET": _b64(target),
                    "XDS_ARGUMENTS": _b64(subprocess.list2cmdline(arguments)),
                    "XDS_DIRECTORY": _b64(str(working)),
                    "XDS_ICON": _b64(icon),
                    "XDS_DESCRIPTION": _b64(
                        "Xay Dung So - nhac nen khi dang nhap Windows"  # .lnk: ANSI only
                    ),
                },
                capture_output=True,
                timeout=20,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode != 0 or not staging.is_file():
                raise OSError(f"PowerShell exit code {result.returncode}")
            os.replace(staging, self.path)
        except (OSError, subprocess.TimeoutExpired) as error:
            staging.unlink(missing_ok=True)
            raise RuntimeError(
                "Không tạo được lối tắt khởi động cùng Windows."
            ) from error

    def disable(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError as error:
            raise RuntimeError(
                "Không xóa được lối tắt khởi động cùng Windows."
            ) from error

    def set_enabled(self, value: bool) -> None:
        self.enable() if value else self.disable()
        self._mark()

    def ensure_first_run(self) -> bool:
        """Enable once on the first app start; later starts keep the user's choice."""
        if (self.directory / MARKER).exists():
            return False
        self.enable()
        self._mark()
        return True

    def _mark(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / MARKER).touch()
