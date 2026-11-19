"""Tray icon: X hides to the tray, double-click reopens, Thoát quits."""

from test_foundation import run_python


def test_close_hides_to_tray_and_quit_exits():
    run_python("""
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
        from xaydungso.application.dashboard import Dashboard
        from xaydungso.application.records import Records
        from xaydungso.application.reminders import Reminders
        from xaydungso.core.config import AppSettings
        from xaydungso.core.paths import data_directory
        from xaydungso.infrastructure.dashboard import SqliteDashboard
        from xaydungso.infrastructure.database import Database
        from xaydungso.infrastructure.records import SqliteRecords
        from xaydungso.infrastructure.reminders import SqliteReminders
        from xaydungso.presentation.main_window import MainWindow

        class NoExport:
            def export(self): return None

        class Background:
            def running(self): return False
            def start(self): pass
            def stop(self): pass

        app = QApplication([])
        database = Database(data_directory() / 'xaydungso.sqlite3')
        database.initialize()
        window = MainWindow(AppSettings(), Records(SqliteRecords(database), NoExport()),
                            Reminders(SqliteReminders(database)), Background(), None,
                            Dashboard(SqliteDashboard(database)), tray=True)
        window.show()
        QTest.qWait(50)
        assert window.tray is not None and window.tray.isVisible()

        area = app.primaryScreen().availableGeometry()  # Opens centred on screen.
        frame = window.frameGeometry()
        if frame.width() <= area.width() and frame.height() <= area.height():
            assert abs(frame.center().x() - area.center().x()) <= 1
            assert abs(frame.center().y() - area.center().y()) <= 1
        else:
            assert frame.left() >= area.left() and frame.top() >= area.top()
        assert not app.quitOnLastWindowClosed()
        assert [a.text() for a in window.tray.menu.actions()] == ['Mở', 'Thoát']
        assert all(a.icon().isNull() for a in window.tray.menu.actions())

        window.close()  # X button: hide to the tray, keep running.
        assert not window.isVisible()
        assert not hasattr(window.tray, 'window_hidden')  # No notification on X.

        window.tray.activated.emit(QSystemTrayIcon.ActivationReason.Trigger)
        assert not window.isVisible()  # Single click does nothing.
        window.tray.activated.emit(QSystemTrayIcon.ActivationReason.DoubleClick)
        assert window.isVisible()

        window.quit_app()
        app.processEvents()
        assert window.quitting and not window.tray.isVisible()
        assert not window.isVisible()

        plain = MainWindow(AppSettings(), Records(SqliteRecords(database), NoExport()),
                           Reminders(SqliteReminders(database)), Background(), None,
                           Dashboard(SqliteDashboard(database)), tray=False)
        assert plain.tray is None  # Without a tray, X closes as before.
    """)


def test_second_launch_shows_the_running_window():
    run_python("""
        import uuid
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication
        from xaydungso.presentation.single_instance import InstanceServer, notify_running

        app = QApplication([])
        name = f'xaydungso-test-{uuid.uuid4().hex}'
        assert notify_running(name) is False  # Nothing running yet.
        shown = []
        server = InstanceServer(lambda: shown.append(True), name, app)
        assert server.isListening()
        assert notify_running(name) is True
        for _ in range(50):
            if shown:
                break
            QTest.qWait(20)
        assert shown == [True]
    """)
