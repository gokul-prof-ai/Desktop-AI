"""
DesktopAI v2.0 — Apply / Undo Workers
File: src/gui/workers/apply_worker.py

Background threads that execute the organization plan and undo batches.
Keeps the UI responsive during file operations.
"""
from __future__ import annotations
import uuid
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.logger import get_logger

logger = get_logger(__name__)


class ApplyWorker(QThread):
    """Executes the organization plan on a background thread."""

    progress = Signal(int, int)            # (done, total)
    file_moved = Signal(str, str)          # (source_name, target_path)
    finished_apply = Signal(int, int, int, str)  # success, failed, skipped, batch_id
    error_occurred = Signal(str)

    def __init__(self, analysis_results: list, target_folder: Path, parent=None):
        super().__init__(parent)
        self._results = analysis_results
        self._target_folder = Path(target_folder)
        self._is_cancelled = False

    def cancel(self) -> None:
        self._is_cancelled = True

    def run(self) -> None:
        try:
            from domain.organizer.organizer import AutoOrganizer
            from domain.organizer.planner import OrganizationPlanner

            files = [r.file_info for r in self._results if not r.skipped]
            if not files:
                self.finished_apply.emit(0, 0, 0, "")
                return

            planner = OrganizationPlanner()
            actions = planner.create_plan(files, self._target_folder)
            if not actions:
                self.finished_apply.emit(0, 0, len(files), "")
                return

            organizer = AutoOrganizer()
            batch_id = str(uuid.uuid4())
            total = len(actions)
            success = failed = skipped = 0

            for i, action in enumerate(actions, 1):
                if self._is_cancelled:
                    break
                stats = organizer.execute_plan([action], batch_id)
                success += stats["success"]
                failed += stats["failed"]
                skipped += stats["skipped"]
                if action.is_success:
                    self.file_moved.emit(
                        action.source_path.name,
                        str(action.actual_target_path),
                    )
                self.progress.emit(i, total)

            logger.info("ApplyWorker done: %d ok, %d failed, %d skipped",
                        success, failed, skipped)
            self.finished_apply.emit(success, failed, skipped, batch_id)

        except Exception as exc:
            logger.error("ApplyWorker error: %s", exc, exc_info=True)
            self.error_occurred.emit(str(exc))


class UndoWorker(QThread):
    """Reverses a batch on a background thread."""

    finished_undo = Signal(int, str)  # reversed_count, batch_id
    error_occurred = Signal(str)

    def __init__(self, batch_id: str, parent=None):
        super().__init__(parent)
        self._batch_id = batch_id

    def run(self) -> None:
        try:
            from domain.organizer.organizer import AutoOrganizer
            organizer = AutoOrganizer()
            count = organizer.undo_last_batch(self._batch_id)
            self.finished_undo.emit(count, self._batch_id)
        except Exception as exc:
            logger.error("UndoWorker error: %s", exc, exc_info=True)
            self.error_occurred.emit(str(exc))