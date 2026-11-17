"""One reminder worker per data directory, using an OS-released process lock."""

import os
import subprocess
import sys
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


def start_worker(directory: Path) -> None:
    if is_running(directory):
        return
    (directory / "reminder-worker.stop").unlink(missing_ok=True)
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--reminder-worker"]
    else:
        command = [sys.executable, "-m", "xaydungso.worker"]
    options = (
        {"start_new_session": True}
        if sys.platform != "win32"
        else {
            "creationflags": subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
        }
    )
    subprocess.Popen(
        [*command, "--data-dir", str(directory.resolve())],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy(),
        **options,
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
