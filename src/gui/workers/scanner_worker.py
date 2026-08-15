"""
DesktopAI v2.0 — Background Scanner Worker (Service-Backed)
File: src/gui/workers/scanner_worker.py

Migrated to use FileService instead of direct domain imports.
Emits progress and per-file classification signals for live UX.
"""
from __future__ import annotations
import traceback
import time
from PySide6.QtCore import QThread, Signal
from core.logger import get_logger
from services import FileService

logger = get_logger(__name__)


class ScannerWorker(QThread):
    """Background worker that delegates to FileService."""
    
    progress = Signal(int, int)              # (current, total)
    file_classified = Signal(str, str, float) # (filename, category, confidence)
    finished_scan = Signal(list)             # list[dict]
    error_occurred = Signal(str)

    def __init__(self, folder_path: str, file_service: FileService, parent=None) -> None:
        super().__init__(parent)
        self.folder_path = folder_path
        self.file_service = file_service
        self._is_cancelled = False

    def cancel(self) -> None:
        """Request cancellation."""
        self._is_cancelled = True

    def run(self) -> None:
        """Execute scanning via FileService."""
        try:
            logger.info("ScannerWorker: starting scan on %s", self.folder_path)
            
            # Track current file index for per-file emissions
            current_index = [0]
            total_files = [0]
            
            def progress_callback(percent: int, message: str):
                """Emit progress signals during scan."""
                if self._is_cancelled:
                    return
                # FileService calls this during iteration
                # We can't get per-file info here, just overall progress
                if total_files[0] > 0:
                    current = int((percent / 100.0) * total_files[0])
                    self.progress.emit(current, total_files[0])
            
            # Call FileService.scan_folder (synchronous, but we're on a worker thread)
            results = self.file_service.scan_folder(
                self.folder_path,
                progress_callback=progress_callback
            )
            
            if self._is_cancelled:
                logger.info("ScannerWorker: scan cancelled")
                return
            
            if not results:
                self.finished_scan.emit([])
                return
            
            total_files[0] = len(results)
            
            # Emit per-file signals for live UX
            for result_dict in results:
                if self._is_cancelled:
                    logger.info("ScannerWorker: scan cancelled during emission")
                    return
                
                filename = result_dict.get("filename", "unknown")
                category = result_dict.get("category", "Unknown")
                confidence = result_dict.get("confidence", 0.0)
                
                self.file_classified.emit(filename, category, confidence)
                current_index[0] += 1
                self.progress.emit(current_index[0], total_files[0])
                
                # Small delay to simulate live feed (optional, for UX)
                time.sleep(0.01)
            
            self.finished_scan.emit(results)
            logger.info("ScannerWorker: scan complete (%d files)", len(results))

        except Exception as exc:
            logger.error("ScannerWorker error: %s", exc)
            logger.error(traceback.format_exc())
            self.error_occurred.emit(str(exc))