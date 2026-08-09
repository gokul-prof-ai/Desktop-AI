"""
DesktopAI v2.0 — History Loader Worker
File: src/gui/workers/history_worker.py
"""
from __future__ import annotations
from PySide6.QtCore import QThread, Signal
from core.logger import get_logger

logger = get_logger(__name__)


class HistoryLoader(QThread):
    loaded = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, status: str | None = None, parent=None):
        super().__init__(parent)
        self._status = status

    def run(self):
        try:
            from infrastructure.storage.database import DB
            rows = DB.get_history(limit=200, status=self._status)
            self.loaded.emit([dict(r) for r in rows])
        except Exception as exc:
            logger.error("HistoryLoader error: %s", exc)
            self.error_occurred.emit(str(exc))