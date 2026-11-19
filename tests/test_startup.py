"""Windows startup shortcut for the reminder worker (first run, toggle, failures)."""

import base64
import subprocess

import pytest

from xaydungso.infrastructure import startup
from xaydungso.infrastructure.startup import MARKER, StartupShortcut


def decode(env, name):
    return base64.b64decode(env[name]).decode("utf-8")


class FakePowerShell:
    def __init__(self, returncode=0):
        self.returncode = returncode
        self.calls = []

    def __call__(self, command, **options):
        env = options["env"]
        self.calls.append(env)
        if self.returncode == 0:
            # PowerShell saves the ASCII staging name; Python renames it.
            with open(decode(env, "XDS_LINK"), "wb") as link:
                link.write(b"lnk")
        return subprocess.CompletedProcess(command, self.returncode, b"", b"")


def make(tmp_path, run):
    return StartupShortcut(tmp_path / "data", folder=tmp_path / "Startup", run=run)


def test_first_run_enables_once_then_keeps_user_choice(tmp_path):
    run = FakePowerShell()
    shortcut = make(tmp_path, run)
    assert shortcut.ensure_first_run() is True
    assert shortcut.enabled()
    assert shortcut.path.name == "Xây Dựng Số - Nhắc nền.lnk"
    assert (tmp_path / "data" / MARKER).exists()
    shortcut.set_enabled(False)
    assert not shortcut.enabled()
    assert shortcut.ensure_first_run() is False  # User turned it off: stays off.
    assert not shortcut.enabled()
    assert len(run.calls) == 1


def test_shortcut_runs_hidden_worker_for_this_data_directory(tmp_path):
    run = FakePowerShell()
    make(tmp_path, run).enable()
    env = run.calls[0]
    assert decode(env, "XDS_TARGET").lower().endswith("pythonw.exe")
    arguments = decode(env, "XDS_ARGUMENTS")
    assert "-m xaydungso.worker" in arguments
    assert str((tmp_path / "data").resolve()) in arguments
    assert decode(env, "XDS_ICON").endswith(",0")
    assert "XDS_LINK" in env and "$env" not in startup.SCRIPT  # Data, not code.


def test_failure_reports_error_and_leaves_nothing(tmp_path):
    shortcut = make(tmp_path, FakePowerShell(returncode=1))
    with pytest.raises(RuntimeError):
        shortcut.ensure_first_run()
    assert not shortcut.enabled()
    assert not (tmp_path / "data" / MARKER).exists()  # Retried on the next start.
    assert list((tmp_path / "Startup").iterdir()) == []


def test_real_shortcut_is_created_and_removed(tmp_path):
    shortcut = StartupShortcut(tmp_path / "data", folder=tmp_path / "Startup")
    shortcut.set_enabled(True)
    assert shortcut.enabled()
    assert [p.name for p in (tmp_path / "Startup").iterdir()] == [shortcut.path.name]
    shortcut.set_enabled(False)
    assert not shortcut.enabled()
