"""
DesktopAI v2.0 — Apply / Undo Workers
File: src/gui/workers/apply_worker.py

Background threads that execute the organization plan and undo batches
via FileService — never touching domain classes directly.
"""
from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.logger import get_logger
from services import FileService

logger = get_logger(__name__)


class ApplyWorker(QThread):
    """Executes the organization plan on a background thread."""

    progress      = Signal(int, int)            # (done, total)
    file_moved    = Signal(str, str)            # (source_name, target_path)
    finished_apply = Signal(int, int, int, str) # success, failed, skipped, batch_id
    error_occurred = Signal(str)

    def __init__(
        self,
        service: FileService,
        scan_results: list[dict],
        target_folder: Path,
        parent=None,
    ):
        super().__init__(parent)
        self._service       = service
        self._scan_results  = scan_results
        self._target_folder = Path(target_folder)
        self._is_cancelled  = False

    def cancel(self) -> None:
        self._is_cancelled = True

    def run(self) -> None:
        try:
            # Plan
            plan = self._service.plan_organisation(
                target_folder=self._target_folder,
                scan_results=self._scan_results,
            )
            if not plan:
                self.finished_apply.emit(0, 0, len(self._scan_results), "")
                return

            total = len(plan)

            # Apply with per-file progress
            def _progress(pct: int, msg: str) -> None:
                done = max(1, int(pct / 100 * total))
                self.progress.emit(done, total)

            stats = self._service.apply_plan(plan, progress_callback=_progress)

            # Emit per-file signals for the live log
            for p in plan:
                if p.get("success"):
                    self.file_moved.emit(
                        Path(p["source"]).name,
                        p["destination"],
                    )

            logger.info(
                "ApplyWorker done: %d ok, %d failed, %d skipped",
                stats["success"], stats["failed"], stats["skipped"],
            )
            self.finished_apply.emit(
                stats["success"], stats["failed"], stats["skipped"],
                stats.get("batch_id", ""),
            )

        except Exception as exc:
            logger.error("ApplyWorker error: %s", exc, exc_info=True)
            self.error_occurred.emit(str(exc))


class UndoWorker(QThread):
    """Reverses a batch on a background thread."""

    finished_undo  = Signal(int, str)  # reversed_count, batch_id
    error_occurred = Signal(str)

    def __init__(self, service: FileService, batch_id: str, parent=None):
        super().__init__(parent)
        self._service   = service
        self._batch_id  = batch_id

    def run(self) -> None:
        try:
            result = self._service.undo_last(self._batch_id)
            if result["error"]:
                self.error_occurred.emit(result["error"])
            else:
                self.finished_undo.emit(result["reversed"], self._batch_id)
        except Exception as exc:
            logger.error("UndoWorker error: %s", exc, exc_info=True)
            self.error_occurred.emit(str(exc))
