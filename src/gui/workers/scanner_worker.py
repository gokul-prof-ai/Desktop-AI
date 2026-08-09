"""
DesktopAI v2.0
Background scanner worker.

Responsibilities:
    1. Scan files.
    2. Classify files.
    3. Persist results to SQLite.
    4. Emit progress/results to the GUI.

The worker never blocks the GUI thread.
"""

from __future__ import annotations

import traceback

from PySide6.QtCore import QThread, Signal

from core.logger import get_logger
from infrastructure.storage.database import DB


logger = get_logger(__name__)


class ScannerWorker(QThread):
    progress = Signal(int, int)
    file_classified = Signal(str, str, float)
    finished_scan = Signal(list)
    error_occurred = Signal(str)

    def __init__(
        self,
        folder_path: str,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.folder_path = folder_path
        self._is_cancelled = False

    def cancel(self) -> None:
        """Request cancellation."""

        self._is_cancelled = True

    def _persist_result(self, result) -> None:
        """
        Persist a classification result.

        Database failures are isolated from scanning so a database
        problem cannot destroy an otherwise successful scan.
        """

        try:
            file_info = result.file_info

            modified_at = None

            if file_info.modified_at is not None:
                modified_at = file_info.modified_at.isoformat()

            DB.upsert_file(
                path=str(file_info.path),
                filename=file_info.filename,
                extension=file_info.extension,
                size_bytes=file_info.size_bytes,
                modified_at=modified_at,
                md5_hash=file_info.md5_hash,
                category=result.category,
                confidence=result.confidence,
                summary=file_info.summary,
                text_content=file_info.text_content,
            )

        except Exception as exc:
            logger.warning(
                "ScannerWorker: failed to persist %s: %s",
                getattr(
                    getattr(result, "file_info", None),
                    "filename",
                    "unknown",
                ),
                exc,
            )

    def run(self) -> None:
        """Execute scanning and classification."""

        try:
            from domain.scanner.scanner import FileScanner
            from domain.classifier.classifier import FileClassifier

            scanner = FileScanner()
            classifier = FileClassifier()

            logger.info(
                "ScannerWorker: starting scan on %s",
                self.folder_path,
            )

            files = scanner.scan(self.folder_path)

            total = len(files)

            if total == 0:
                self.finished_scan.emit([])
                return

            results = []

            for index, file_info in enumerate(files):

                if self._is_cancelled:
                    logger.info(
                        "ScannerWorker: scan cancelled"
                    )
                    return

                result = classifier.classify(file_info)

                results.append(result)

                # Persist scan result.
                self._persist_result(result)

                self.file_classified.emit(
                    result.file_info.filename,
                    result.category,
                    result.confidence,
                )

                self.progress.emit(
                    index + 1,
                    total,
                )

            if not self._is_cancelled:
                self.finished_scan.emit(results)

        except Exception as exc:
            logger.error(
                "ScannerWorker error: %s",
                exc,
            )

            logger.error(
                traceback.format_exc()
            )

            self.error_occurred.emit(
                str(exc)
            )