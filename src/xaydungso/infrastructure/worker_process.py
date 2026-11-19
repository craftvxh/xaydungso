"""One reminder worker per data directory, using an OS-released process lock."""

import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def worker_lock(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    stream = (directory / "reminder-worker.lock").open("a+b")
    locked = False
    try:
        if sys.platform == "win32":
            import msvcrt

            if stream.seek(0, 2) == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                locked = True
            except OSError:
                pass
        else:
            import fcntl

            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except BlockingIOError:
                pass
        yield locked
    finally:
        stream.close()


def is_running(directory: Path) -> bool:
    with worker_lock(directory) as acquired:
        return not acquired


def _windowless_python() -> str:
    """pythonw.exe next to the running interpreter on Windows, if present."""
    if sys.platform == "win32":
        candidate = Path(sys.executable).with_name("pythonw.exe")
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def start_worker(directory: Path) -> None:
    if is_running(directory):
        return
    (directory / "reminder-worker.stop").unlink(missing_ok=True)
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--reminder-worker"]
    else:
        command = [_windowless_python(), "-m", "xaydungso.worker"]
    options = (
        {"start_new_session": True}
        if sys.platform != "win32"
        else {
            # CREATE_NO_WINDOW, not DETACHED_PROCESS: a detached console program
            # (e.g. the venv python.exe launcher's child) opens a new visible
            # terminal; with no window it gets a hidden console instead.
            "creationflags": subprocess.CREATE_NO_WINDOW
            | subprocess.CREATE_NEW_PROCESS_GROUP
        }
    )
    process = subprocess.Popen(
        [*command, "--data-dir", str(directory.resolve())],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy(),
        **options,
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if is_running(directory):
            return
        if process.poll() is not None:
            raise RuntimeError(
                "Tiến trình nhắc nền không khởi động được. Kiểm tra reminders.log."
            )
        time.sleep(0.05)
    if process.poll() is None:
        process.terminate()
        process.wait(timeout=5)
    raise RuntimeError(
        "Nhắc nền chưa khởi động sau 5 giây. Kiểm tra quyền truy cập thư mục dữ liệu."
    )


def stop_worker(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "reminder-worker.stop").touch()


class BackgroundReminders:
    def __init__(self, directory: Path):
        self.directory = directory

    def running(self):
        return is_running(self.directory)

    def start(self):
        start_worker(self.directory)

    def stop(self):
        stop_worker(self.directory)
