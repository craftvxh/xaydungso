"""Worker isolation and real process lock; empty databases prevent live sends."""

import subprocess
import sys
import time
from pathlib import Path

import pytest

from xaydungso.infrastructure.worker_process import (
    is_running,
    start_worker,
    stop_worker,
    worker_lock,
)


def test_worker_import_and_once_do_not_import_qt(tmp_path):
    source = """
import sys
from xaydungso import worker
assert not any(name.startswith('PyQt6') for name in sys.modules)
sys.argv = ['worker', '--once', '--data-dir', sys.argv[1]]
assert worker.main() == 0
assert not any(name.startswith('PyQt6') for name in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-c", source, str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "xaydungso.sqlite3").is_file()
    assert not is_running(tmp_path)


def test_os_lock_prevents_second_worker_and_releases(tmp_path):
    with worker_lock(tmp_path) as acquired:
        assert acquired
        assert is_running(tmp_path)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "xaydungso.worker",
                "--once",
                "--data-dir",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert not (tmp_path / "xaydungso.sqlite3").exists()
    assert not is_running(tmp_path)


def test_worker_can_run_without_gui_and_stop_cleanly(tmp_path):
    # A stale stop file must not prevent an explicit new launch.
    stop_worker(tmp_path)
    process = subprocess.Popen(
        [sys.executable, "-m", "xaydungso.worker", "--data-dir", str(tmp_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 5
        while not (tmp_path / "xaydungso.sqlite3").exists():
            assert time.monotonic() < deadline
            assert process.poll() is None
            time.sleep(0.02)
        assert is_running(tmp_path)
        stop_worker(tmp_path)
        assert process.wait(timeout=5) == 0
        assert not is_running(tmp_path)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def test_gui_worker_launcher_actually_starts_and_stops_empty_worker(tmp_path):
    start_worker(tmp_path)
    try:
        deadline = time.monotonic() + 8
        while not (tmp_path / "xaydungso.sqlite3").exists():
            assert time.monotonic() < deadline
            time.sleep(0.05)
        assert is_running(tmp_path)
    finally:
        stop_worker(tmp_path)
        deadline = time.monotonic() + 8
        while is_running(tmp_path) and time.monotonic() < deadline:
            time.sleep(0.05)
        assert not is_running(tmp_path)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows console behaviour")
def test_worker_starts_without_a_console_window(tmp_path, monkeypatch):
    from xaydungso.infrastructure import worker_process

    calls = []

    class FakeProcess:
        def poll(self):
            return 0  # Exit at once; we only inspect how it was launched.

    def fake_popen(command, **options):
        calls.append((command, options))
        return FakeProcess()

    monkeypatch.setattr(worker_process.subprocess, "Popen", fake_popen)
    with pytest.raises(RuntimeError):
        worker_process.start_worker(tmp_path)
    command, options = calls[0]
    assert Path(command[0]).name.lower() == "pythonw.exe"
    flags = options["creationflags"]
    assert flags & subprocess.CREATE_NO_WINDOW
    assert not flags & subprocess.DETACHED_PROCESS  # Would open a new terminal.
