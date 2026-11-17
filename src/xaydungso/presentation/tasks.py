"""Run SQLite/export work serially off the Qt event loop."""

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot


class JobSignals(QObject):
    finished = pyqtSignal(object, object, object)


class Job(QRunnable):
    def __init__(self, function):
        super().__init__()
        self.function = function
        self.signals = JobSignals()

    def run(self):
        try:
            result = self.function()
        except Exception as error:
            self.signals.finished.emit(self, None, error)
        else:
            self.signals.finished.emit(self, result, None)


class TaskRunner(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.jobs = {}

    @property
    def busy(self):
        return bool(self.jobs)

    def submit(self, function, success, failure):
        job = Job(function)
        self.jobs[job] = success, failure
        job.signals.finished.connect(self._finish)
        self.pool.start(job)

    @pyqtSlot(object, object, object)
    def _finish(self, job, result, error):
        success, failure = self.jobs.pop(job)
        if error is None:
            success(result)
        else:
            failure(error)
