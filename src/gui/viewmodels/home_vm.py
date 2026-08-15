"""
DesktopAI v2.0 — Home ViewModel (Service-Backed)
File: src/gui/viewmodels/home_vm.py

Accepts FileService and passes it to ScannerWorker.
"""
from __future__ import annotations
from PySide6.QtCore import QObject, Signal
from gui.workers.scanner_worker import ScannerWorker
from services import FileService
from core.logger import get_logger

logger = get_logger(__name__)


class HomeViewModel(QObject):
    """ViewModel for the Home screen."""
    
    scan_started = Signal()
    scan_progress = Signal(int, int)
    scan_completed = Signal(list)
    scan_failed = Signal(str)

    def __init__(self, file_service: FileService, parent=None):
        super().__init__(parent)
        self.file_service = file_service
        self._worker: ScannerWorker | None = None

    def start_scan(self, folder_path: str):
        """Start scanning the given folder."""
        if self._worker and self._worker.isRunning():
            logger.warning("Scan already in progress")
            return

        self.scan_started.emit()
        self._worker = ScannerWorker(folder_path, self.file_service)
        
        # Connect worker signals to ViewModel signals
        self._worker.progress.connect(self.scan_progress)
        self._worker.finished_scan.connect(self.scan_completed)
        self._worker.error_occurred.connect(self.scan_failed)
        
        self._worker.start()

    def cancel_scan(self):
        """Cancel the current scan."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()