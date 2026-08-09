"""
DesktopAI v2.0 — Organize ViewModel
File: src/gui/viewmodels/organize_vm.py

Owns the Organize screen state and worker lifecycle.
The View never touches domain objects directly.
"""
from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from core.logger import get_logger
from gui.workers.apply_worker import ApplyWorker, UndoWorker

logger = get_logger(__name__)


class OrganizeViewModel(QObject):
    apply_started = Signal()
    apply_progress = Signal(int, int)
    file_moved_signal = Signal(str, str)
    apply_completed = Signal(int, int, int, str)
    apply_failed = Signal(str)
    undo_started = Signal()
    undo_completed = Signal(int, str)
    undo_failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: list = []
        self._last_batch_id: str | None = None
        self._worker: ApplyWorker | None = None
        self._undo_worker: UndoWorker | None = None

    # ── State ──────────────────────────────────────────────────────
    def set_results(self, results: list) -> None:
        self._results = results or []

    @property
    def has_results(self) -> bool:
        return len(self._results) > 0

    @property
    def can_undo(self) -> bool:
        return self._last_batch_id is not None

    @property
    def is_busy(self) -> bool:
        return (self._worker is not None and self._worker.isRunning()) or (
            self._undo_worker is not None and self._undo_worker.isRunning()
        )

    # ── Apply ──────────────────────────────────────────────────────
    def start_apply(self, target_folder: Path) -> None:
        if not self.has_results or self.is_busy:
            return
        self.apply_started.emit()
        self._worker = ApplyWorker(self._results, target_folder)
        self._worker.progress.connect(self.apply_progress)
        self._worker.file_moved.connect(self.file_moved_signal)
        self._worker.finished_apply.connect(self._on_apply_finished)
        self._worker.error_occurred.connect(self.apply_failed)
        self._worker.start()

    def _on_apply_finished(self, success: int, failed: int, skipped: int, batch_id: str) -> None:
        if batch_id:
            self._last_batch_id = batch_id
        self.apply_completed.emit(success, failed, skipped, batch_id)

    # ── Undo ───────────────────────────────────────────────────────
    def start_undo(self) -> None:
        if not self.can_undo or self.is_busy:
            return
        self.undo_started.emit()
        self._undo_worker = UndoWorker(self._last_batch_id)
        self._undo_worker.finished_undo.connect(self.undo_completed)
        self._undo_worker.error_occurred.connect(self.undo_failed)
        self._undo_worker.start()