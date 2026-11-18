"""Exercise real forms/buttons and async persistence without external delivery."""

from test_foundation import run_python


def test_visible_crud_reminder_and_export_workflow():
    run_python("""
        import time
        from pathlib import Path
        from zipfile import ZipFile
        from xml.etree import ElementTree
        from PyQt6.QtCore import QDateTime
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
            starts = 0
            def running(self): return self.starts > 0
            def start(self): self.starts += 1
            def stop(self): pass

        app = QApplication([])
        directory = data_directory()
        database = Database(directory / 'xaydungso.sqlite3')
        database.initialize()
        repository = SqliteRecords(database)
        store = SqliteReminders(database)
        output = directory / 'so_theo_doi.xlsx'
        output.write_bytes(template_path().read_bytes())
        service = Records(repository, SqliteTrackingExporter(repository, template_path(), output, "replace"))
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
        assert 'reminder_tracking_time' not in editor.inputs
        assert editor.inputs['received_at'].text()  # Auto-filled with current time.
        assert editor.inputs['handover_at'].text()
        editor.deadline.setText('18/11/2099 9:00')  # Invalid format rejected.
        editor.save_button.click()
        assert 'dd/mm/yyyy hh:mm' in editor.error.text()
        editor.deadline.setText('18/11/2099 09:00')
        editor.inputs['return_appointment_date'].setText('20/11/2099')
        editor.save_button.click()
        assert 'Ngày hẹn trả kết quả' in editor.error.text()
        editor.inputs['return_appointment_date'].setText('20/11/2099 16:30')
        editor.inputs['drawing_stamp_status'].click()
        assert editor.inputs['drawing_stamp_status'].mark.isChecked()
        editor.save_button.click()
        idle()
        assert not editor.isVisible()
        assert page.records_table.rowCount() == 1
        assert page.records_table.item(0, page.COLUMN['status']).text() == ''  # Badge only.
        assert [page.status_filter.text(i) for i in range(3)] == [
            'Tất cả  1', 'Chưa hoàn thành  1', 'Đã hoàn thành  0']
        assert not page.detail.isVisible() and not page.edit_button.isVisible()
        page.records_table.selectRow(0)
        assert page.detail.code.text() == '0001'
        assert page.detail.values['applicant_name'].text() == 'Nguyễn Văn Mẫu'
        assert page.detail.values['deadline'].text() == '18/11/2099 09:00'
        assert page.edit_button.isVisible()
        page.detail.close_button.click()
        assert page.selected() is None and not page.detail.isVisible()
        assert not page.bulk_bar.isVisible()
        page._cell_clicked(0, 0)  # Tick the row checkbox.
        assert page.bulk_bar.isVisible() and 'Đã chọn 1' in page.bulk_text.text()
        page.bulk_clear_button.click()
        assert not page.bulk_bar.isVisible()
        assert 'Trang 1 / 1' in page.pager.label.text()
        assert output.is_file()
        # Saving the dialog must write Excel before any manual retry is clicked.
        with ZipFile(output) as workbook:
            sheet = ElementTree.fromstring(workbook.read('xl/worksheets/sheet1.xml'))
        ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        assert ''.join(sheet.find(".//s:c[@r='A5']", ns).itertext()) == '0001'
        record = repository.list()[0]
        assert store.list() == []
        assert not hasattr(editor, 'reminder_enabled')
        assert record.data.phone == '0123456789'
        assert record.data.return_appointment_date == '20/11/2099 16:30'
        assert record.data.drawing_stamp_status is True
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
        assert editor.value()['deadline_at'] is not None
        editor.duration.presets.setCurrentIndex(1)
        editor.save_button.click()
        idle()
        assert len(store.list()) == 1
        assert store.list()[0]['lead_seconds'] == 10
        assert reminders.reminders_table.rowCount() == 1
        assert reminders.background.starts == 1
        assert 'nhắc nền đã bật' in reminders.feedback.text()
        assert repository.get(record.id).data.reminder_lead_seconds is None
        assert store.list()[0]['notify_at'].startswith('2099-11-18T01:59:50')

        window.switchTo(page)
        page.records_table.selectRow(0)
        pages.ConfirmBox.exec = lambda self: 0
        page.delete_button.click()
        idle()
        assert len(repository.list()) == 1  # Cancellation must not delete.
        pages.ConfirmBox.exec = lambda self: 1
        page.delete_button.click()
        idle()
        assert not repository.list()
        assert window.dashboard_page.metric_values['total_records'].text() == '0'
        assert store.list()[0]['cancelled'] == 1
        assert page.records_table.rowCount() == 0
        assert not hasattr(page, 'export_button')
        window.close()
        app.processEvents()
        assert not window.isVisible()
    """)


def test_saved_reminder_survives_worker_start_failure_and_opt_out():
    run_python("""
        import time
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtTest import QTest
        from xaydungso.core.paths import data_directory
        from xaydungso.infrastructure.database import Database
        from xaydungso.infrastructure.records import SqliteRecords
        from xaydungso.infrastructure.reminders import SqliteReminders
        from xaydungso.application.reminders import Reminders
        from xaydungso.presentation.pages import RemindersPage
        from xaydungso.presentation.tasks import TaskRunner
        app=QApplication([])
        db=Database(data_directory()/'test.sqlite3')
        db.initialize()
        store=SqliteReminders(db)
        class Background:
            calls=0
            def running(self):return False
            def start(self):
                self.calls+=1
                raise RuntimeError('Synthetic startup failure')
        background=Background()
        runner=TaskRunner()
        page=RemindersPage(Reminders(store),SqliteRecords(db),background,runner)
        def idle():
            deadline=time.monotonic()+5
            while runner.busy:
                assert time.monotonic()<deadline
                QTest.qWait(10)
        idle()
        page.add_button.click()
        idle()
        page.editor.title.setText('First test schedule')
        page.editor.save_button.click()
        idle()
        assert len(store.list())==1
        assert background.calls==1
        assert 'Lịch đã lưu nhưng không bật được' in page.feedback.text()
        page.add_button.click()
        idle()
        page.editor.title.setText('Second test schedule')
        page.editor.enable_background.setChecked(False)
        page.editor.save_button.click()
        idle()
        assert len(store.list())==2
        assert background.calls==1
        page.timer.stop()
        page.close()
    """)


def test_records_page_pages_fourteen_rows_and_bulk_status():
    run_python("""
        import time
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication
        from xaydungso.application.records import Records
        from xaydungso.core.paths import data_directory
        from xaydungso.domain.records import RecordData, RecordStatus
        from xaydungso.infrastructure.database import Database
        from xaydungso.infrastructure.records import SqliteRecords
        from xaydungso.presentation.pages import RecordsPage
        from xaydungso.presentation.tasks import TaskRunner

        class NoExport:
            def export(self): pass

        app = QApplication([])
        database = Database(data_directory() / 'paging.sqlite3')
        database.initialize()
        repository = SqliteRecords(database)
        for number in range(20):
            repository.save(RecordData(f'HS-{number:03d}', f'Tên {number}'))
        runner = TaskRunner()
        page = RecordsPage(Records(repository, NoExport()), runner, None)
        page.show()

        def idle():
            deadline = time.monotonic() + 5
            QTest.qWait(10)
            while runner.busy:
                assert time.monotonic() < deadline
                QTest.qWait(10)

        idle()
        assert page.records_table.rowCount() == 14
        assert page.pager.label.text() == 'Trang 1 / 2'
        assert 'Hiển thị' in page.footer_text.text() and '1 - 14' in page.footer_text.text()
        page.pager.next.click()
        assert page.records_table.rowCount() == 6 and '15 - 20' in page.footer_text.text()
        from PyQt6.QtCore import Qt as _Qt
        box = page.records_table.visualItemRect(page.records_table.item(0, 0)).center()
        QTest.mouseClick(page.records_table.viewport(), _Qt.MouseButton.LeftButton, pos=box)
        assert 'Đã chọn 1' in page.bulk_text.text()
        assert page.selected() is None and not page.detail.isVisible()  # Tick only.
        QTest.mouseClick(page.records_table.viewport(), _Qt.MouseButton.LeftButton, pos=box)
        assert not page.checked
        page.records_table.selectRow(1)
        QTest.qWait(400)  # Let the slide-in finish.
        assert page.detail.isVisible() and page.detail.width() == 360
        page.detail.close_button.click()
        page._header_clicked(0)  # Tick every row on this page.
        assert 'Đã chọn 6' in page.bulk_text.text()
        page.bulk_done_button.click()
        idle()
        done = [r for r in repository.list() if r.data.status is RecordStatus.COMPLETE]
        assert len(done) == 6 and not page.bulk_bar.isVisible()
        assert page.status_filter.text(2) == 'Đã hoàn thành  6'
        page.status_filter.setCurrentIndex(1)
        assert page.pager.label.text() == 'Trang 1 / 1'
        assert page.records_table.rowCount() == 14
        target = next(r for r in repository.list() if r.data.record_code == 'HS-018')
        page.search.setText('HS-001')  # Focus must clear search and filter.
        page.focus_record(target.id)
        idle()
        assert page.status_filter.currentIndex() == 0 and page.search.text() == ''
        assert page.pager.label.text() == 'Trang 2 / 2'
        assert page.selected().id == target.id and page.detail.isVisible()
        page.close()
    """)
