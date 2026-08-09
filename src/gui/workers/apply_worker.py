"""
DesktopAI v2.0 — Apply Worker
File: src/gui/workers/apply_worker.py

Executes the organization plan on a background QThread.
Wires the Domain layer (Planner + Organizer) to the GUI.
"""
from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from core.logger import get_logger

logger = get_logger(__name__)


class ApplyWorker(QThread):
    """
    Background worker for applying file organization.
    """
    # Signals
    progress = Signal(int, int)  # (done, total)
    file_moved = Signal(str, str)  # (source_name, target_name)
    finished_apply = Signal(int, int, int)  # (success, failed, skipped)
    error_occurred = Signal(str)

    def __init__(self, analysis_results: list, target_folder: Path, parent=None):
        super().__init__(parent)
        self._results = analysis_results
        self._target_folder = target_folder
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            # Import domain modules here to avoid circular imports
            from domain.organizer.planner import OrganizationPlanner
            from domain.organizer.organizer import AutoOrganizer
            from domain.scanner.file_info import FileInfo

            logger.info("ApplyWorker: Starting organization to %s", self._target_folder)
            
            # 1. Extract FileInfo objects from AnalysisResults
            files = [result.file_info for result in self._results]
            
            # 2. Plan the moves (resolves conflicts, checks memory)
            planner = OrganizationPlanner()
            actions = planner.create_plan(files, self._target_folder)
            
            if not actions:
                self.finished_apply.emit(0, 0, len(files))
                return

            # 3. Execute the moves
            organizer = AutoOrganizer()
            total = len(actions)
            
            # We hook into the organizer's internal loop by executing one by one 
            # to emit progress, or we just run the batch and emit at the end.
            # For real-time progress, we'll execute them sequentially here.
            
            success = 0
            failed = 0
            skipped = 0
            
            for i, action in enumerate(actions):
                if self._is_cancelled:
                    break
                
                try:
                    organizer._execute_action(action, batch_id="gui-batch")
                    if action.is_success:
                        success += 1
                        self.file_moved.emit(action.source_path.name, action.actual_target_path.name)
                    else:
                        skipped += 1
                except Exception as e:
                    failed += 1
                    logger.error("Failed to move %s: %s", action.source_path.name, e)
                
                self.progress.emit(i + 1, total)

            self.finished_apply.emit(success, failed, skipped)
            logger.info("ApplyWorker: Finished. Success=%d, Failed=%d", success, failed)

        except Exception as e:
            logger.error("ApplyWorker fatal error: %s", e)
            self.error_occurred.emit(str(e))