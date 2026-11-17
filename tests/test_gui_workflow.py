"""Exercise real forms/buttons and async persistence without external delivery."""

from test_foundation import run_python


def test_visible_crud_reminder_and_export_workflow():
    run_python("""
        import time
        from pathlib import Path
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication
        from xaydungso.application.records import Records
        from xaydungso.application.dashboard import Dashboard
        from xaydungso.application.reminders import Reminders
        from xaydungso.core.config import AppSettings
        from xaydungso.core.paths import data_directory, template_path
        from xaydungso.infrastructure.database import Database
        from xaydungso.infrastructure.dashboard import SqliteDashboard
        from xaydungso.infrastructure.records import SqliteRecords
        from xaydungso.infrastructure.reminders import SqliteReminders
        from xaydungso.infrastructure.tracking_export import SqliteTrackingExporter
        from xaydungso.presentation.main_window import MainWindow
        import xaydungso.presentation.pages as pages

        class Background:
            def running(self): return False
            def start(self): raise AssertionError('No real worker in GUI tests')
            def stop(self): pass

        app = QApplication([])
        directory = data_directory()
        database = Database(directory / 'xaydungso.sqlite3')
        database.initialize()
        repository = SqliteRecords(database)
        store = SqliteReminders(database)
        output = directory / 'so_theo_doi.xlsx'
        service = Records(repository, SqliteTrackingExporter(repository, template_path(), output))
        window = MainWindow(AppSettings(), service, Reminders(store), Background(), output,
                            Dashboard(SqliteDashboard(database)))
        window.show()

        def idle():
            deadline = time.monotonic() + 5
            QTest.qWait(10)
            while window.runner.busy:
                assert time.monotonic() < deadline, 'Async UI operation timed out'
                QTest.qWait(10)

        idle()
        page = window.records_page
        assert window.stackedWidget.currentWidget() is window.dashboard_page
        assert window.dashboard_page.metric_values['total_records'].text() == '0'
        window.dashboard_page.records_button.click()
        assert window.stackedWidget.currentWidget() is page
        assert page.records_table.rowCount() == 0
        page.add_button.click()
        editor = page.editor
        assert editor.isVisible()
        editor.save_button.click()  # Required fields rejected without persistence.
        assert 'Mã hồ sơ' in editor.error.text()
        assert not repository.list()
        editor.inputs['record_code'].setText('0001')
        editor.inputs['applicant_name'].setText('Nguyễn Văn Mẫu')
        editor.inputs['phone'].setText('0123456789')
        editor.inputs['reminder_tracking_time'].setText('Nhập tay H')
        editor.duration.presets.setCurrentIndex(1)
        editor.save_button.click()
        idle()
        assert not editor.isVisible()
        assert page.records_table.rowCount() == 1
        assert output.is_file()
        record = repository.list()[0]
        assert record.data.phone == '0123456789'
        assert window.dashboard_page.metric_values['total_records'].text() == '1'

        page.add_button.click()
        duplicate = page.editor
        duplicate.inputs['record_code'].setText('0001')
        duplicate.inputs['applicant_name'].setText('Trùng mã')
        duplicate.save_button.click()
        idle()
        assert duplicate.isVisible()
        assert 'đã tồn tại' in duplicate.error.text()
        assert duplicate.inputs['applicant_name'].text() == 'Trùng mã'
        duplicate.reject()

        page.records_table.selectRow(0)
        page.edit_button.click()
        editor = page.editor
        assert editor.inputs['phone'].text() == '0123456789'
        editor.status.setCurrentText('Đã hoàn thành')
        editor.notes.setPlainText('Đã sửa từ giao diện')
        editor.save_button.click()
        idle()
        assert repository.get(record.id).data.status.value == 'Đã hoàn thành'

        page.search.setText('KHÔNG CÓ')
        QTest.qWait(300)
        idle()
        assert page.records_table.rowCount() == 0
        assert window.dashboard_page.metric_values['total_records'].text() == '1'
        page.search.setText('NGUYỄN')
        QTest.qWait(300)
        idle()
        assert page.records_table.rowCount() == 1
        page.status_filter.setCurrentIndex(1)
        idle()
        assert page.records_table.rowCount() == 0
        page.status_filter.setCurrentIndex(2)
        idle()
        assert page.records_table.rowCount() == 1

        page.records_table.selectRow(0)
        page.remind_button.click()
        idle()
        reminders = window.reminders_page
        editor = reminders.editor
        assert editor.isVisible()
        assert editor.value()['start_at'] is None
        editor.duration.presets.setCurrentIndex(1)
        editor.save_button.click()
        idle()
        assert len(store.list()) == 1
        assert store.list()[0]['start_at'] == store.list()[0]['created_at']
        assert reminders.reminders_table.rowCount() == 1
        assert repository.get(record.id).data.reminder_tracking_time == 'Nhập tay H'

        window.switchTo(page)
        page.records_table.selectRow(0)
        pages.MessageBox.exec = lambda self: 0
        page.delete_button.click()
        idle()
        assert len(repository.list()) == 1  # Cancellation must not delete.
        pages.MessageBox.exec = lambda self: 1
        page.delete_button.click()
        idle()
        assert not repository.list()
        assert window.dashboard_page.metric_values['total_records'].text() == '0'
        assert store.list()[0]['cancelled'] == 1
        assert page.records_table.rowCount() == 0
        page.export_button.click()
        idle()
        assert 'Đã xuất' in page.feedback.text()
        window.close()
        app.processEvents()
        assert not window.isVisible()
    """)
