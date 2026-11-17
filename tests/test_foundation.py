"""Foundation checks, with Qt isolated in child processes."""

import os
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import FrozenInstanceError

import pytest

from xaydungso.core.config import AppSettings


def run_python(source: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as data_directory:
        result = subprocess.run(
            [sys.executable, "-c", textwrap.dedent(source)],
            env={
                **os.environ,
                "QT_QPA_PLATFORM": "offscreen",
                "QT_QPA_PLATFORMTHEME": "",
                "XDG_DATA_HOME": data_directory,
                "LOCALAPPDATA": data_directory,
                "APPDATA": data_directory,
                "XAYDUNGSO_DATA_DIR": data_directory,
            },
            capture_output=True,
            text=True,
            timeout=30,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def test_settings_are_immutable_defaults() -> None:
    settings = AppSettings()
    assert settings.app_name == "xaydungso"
    assert settings.window_title == "Xây Dựng Số"
    assert settings.window_width > 0
    assert settings.window_height > 0
    with pytest.raises(FrozenInstanceError):
        settings.window_title = "Changed"


def test_imports_do_not_create_application() -> None:
    run_python("""
        import importlib
        import pkgutil
        import xaydungso
        from PyQt6.QtWidgets import QApplication

        for module in pkgutil.walk_packages(
            xaydungso.__path__, xaydungso.__name__ + "."
        ):
            importlib.import_module(module.name)
        assert QApplication.instance() is None
    """)


def test_console_logging_is_formatted_and_not_duplicated() -> None:
    result = run_python("""
        import logging
        from xaydungso.core.logging import configure_logging

        configure_logging()
        configure_logging()
        logging.getLogger("xaydungso.test").info("Foundation ready")
        logging.getLogger("xaydungso.test").debug("Hidden debug message")
    """)
    assert result.stderr.count("INFO xaydungso.test: Foundation ready") == 1
    assert "Hidden debug message" not in result.stderr


def test_main_opens_dashboard_and_closes_cleanly() -> None:
    run_python("""
        from pathlib import Path
        from PyQt6 import sip
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication
        from qfluentwidgets import FluentWindow
        from xaydungso import main
        from xaydungso.core.config import AppSettings
        from xaydungso.core.paths import data_directory
        from xaydungso.presentation.main_window import MainWindow

        original_show = MainWindow.show
        observed = []

        def show_and_close(window):
            assert QApplication.instance().applicationName() == "xaydungso"
            assert (data_directory() / "xaydungso.sqlite3").is_file()
            assert isinstance(window, FluentWindow)
            assert window.windowTitle() == AppSettings().window_title
            assert window.stackedWidget.count() == 3
            assert window.stackedWidget.currentWidget() is window.dashboard_page
            original_show(window)
            assert window.isVisible()
            observed.append(window)
            def close_when_idle():
                if window.runner.busy:
                    QTimer.singleShot(50, close_when_idle)
                else:
                    window.close()
            QTimer.singleShot(100, close_when_idle)

        MainWindow.show = show_and_close
        assert main() == 0
        assert len(observed) == 1
        assert sip.isdeleted(observed[0])
    """)


def test_database_startup_failure_is_reported_without_opening_window() -> None:
    run_python("""
        import sqlite3
        import xaydungso.app as application

        messages = []
        def fail_initialize(database):
            raise sqlite3.OperationalError("Synthetic initialization failure")

        def unexpected_show(window):
            raise AssertionError("Main window must not open after database failure")

        application.Database.initialize = fail_initialize
        application.MainWindow.show = unexpected_show
        application.QMessageBox.critical = lambda *args: messages.append(args)
        assert application.main() == 1
        assert len(messages) == 1
        assert "Không thể mở cơ sở dữ liệu" in messages[0][2]
    """)
