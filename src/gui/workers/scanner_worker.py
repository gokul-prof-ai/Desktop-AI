"""
DesktopAI v2.0 — Scanner Worker
File: src/gui/workers/scanner_worker.py

Runs the FileScanner and FileClassifier on a background QThread.
Emits signals for progress and results so the UI can update in real-time.
"""
from __future__ import annotations
import traceback
from PySide6.QtCore import QThread, Signal
from core.logger import get_logger

logger = get_logger(__name__)


class ScannerWorker(QThread):
    """
    Background worker for scanning and classifying files.
    """
    # Signals
    progress = Signal(int, int)  # (done, total)
    file_classified = Signal(str, str, float)  # (filename, category, confidence)
    finished_scan = Signal(list)  # list of AnalysisResult objects
    error_occurred = Signal(str)  # error message

    def __init__(self, folder_path: str, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self._is_cancelled = False

    def cancel(self):
        """Request the worker to stop as soon as possible."""
        self._is_cancelled = True

    def run(self):
        """Main thread execution."""
        try:
            # Import here to avoid circular imports or heavy imports at module load
            from domain.scanner.scanner import FileScanner
            from domain.classifier.classifier import FileClassifier
            
            scanner = FileScanner()
            classifier = FileClassifier()
            
            logger.info("ScannerWorker: Starting scan on %s", self.folder_path)
            
            # 1. Scan files
            files = scanner.scan(self.folder_path)
            total = len(files)
            
            if total == 0:
                self.finished_scan.emit([])
                return
                
            # 2. Classify files
            results = []
            for i, file_info in enumerate(files):
                if self._is_cancelled:
                    break
                    
                result = classifier.classify(file_info)
                results.append(result)
                
                # Emit signals for UI updates
                self.file_classified.emit(
                    result.file_info.filename,
                    result.category,
                    result.confidence
                )
                self.progress.emit(i + 1, total)
                
            if not self._is_cancelled:
                self.finished_scan.emit(results)
            else:
                logger.info("ScannerWorker: Scan cancelled")
                
        except Exception as e:
            logger.error("ScannerWorker error: %s", e)
            logger.error(traceback.format_exc())
            self.error_occurred.emit(str(e))