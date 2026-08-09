"""
DesktopAI v2.0 — Organize ViewModel
File: src/gui/viewmodels/organize_vm.py
"""
from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import QObject, Signal
from gui.workers.apply_worker import ApplyWorker
from core.logger import get_logger

logger = get_logger(__name__)


class OrganizeViewModel(QObject):
    """
    ViewModel for the Organize screen.
    """
    apply_started = Signal()
    apply_progress = Signal(int, int)
    apply_completed = Signal(int, int, int)  # success, failed, skipped
    apply_failed = Signal(str)
    file_moved_signal = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: ApplyWorker | None = None
        self._results: list = []

    def set_results(self, results: list):
        self._results = results

    def start_apply(self, target_folder: Path):
        if not self._results:
            return
        if self._worker and self._worker.isRunning():
            return

        self.apply_started.emit()
        self._worker = ApplyWorker(self._results, target_folder)
        
        self._worker.progress.connect(self.apply_progress)
        self._worker.file_moved.connect(self.file_moved_signal)
        self._worker.finished_apply.connect(self.apply_completed)
        self._worker.error_occurred.connect(self.apply_failed)
        
        self._worker.start()

    def cancel_apply(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()