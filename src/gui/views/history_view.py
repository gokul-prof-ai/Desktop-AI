"""
DesktopAI v2.0 — History View (Activity Timeline)
File: src/gui/views/history_view.py
Day-grouped audit timeline with status icons and batch undo.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from core.logger import get_logger
from gui.components import icons as I
from gui.components.widgets import (
    CategoryBadge, EmptyState, SecondaryButton, SectionHeader,
)
from services import FileService

logger = get_logger(__name__)

_STATUS_ICON = {
    "completed": ("success", "ok"),
    "undone": ("undo", "warn"),
    "failed": ("error", "err"),
}


class _HistoryWorker(QThread):
    loaded = Signal(list)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            from infrastructure.storage.database import DB
            self.loaded.emit([dict(r) for r in DB.get_history(limit=200)])
        except Exception as exc:
            self.failed.emit(str(exc))


class _UndoWorker(QThread):
    done = Signal(dict)
    failed = Signal(str)

    def __init__(self, service: FileService, parent=None):
        super().__init__(parent)
        self._service = service

    def run(self):
        try:
            self.done.emit(self._service.undo_last())
        except Exception as exc:
            self.failed.emit(str(exc))


class HistoryView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = FileService()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = SectionHeader(
            "History",
            "Everything DesktopAI has done, with undo.",
        )
        self.undo_btn = SecondaryButton("Undo Last Batch")
        self.undo_btn.clicked.connect(self._start_undo)
        header.add_action(self.undo_btn)
        layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.flow = QVBoxLayout(self.content)
        self.flow.setSpacing(8)
        self.flow.addStretch()
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll, 1)

        self.refresh()

    # ── Data ─────────────────────────────────────────────────────
    def refresh(self) -> None:
        self._worker = _HistoryWorker()
        self._worker.loaded.connect(self._render)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_failed(self, message: str):
        self._clear()
        empty = EmptyState("We couldn't load your history.", message)
        self.flow.insertWidget(0, empty)

    def _render(self, rows: list) -> None:
        self._clear()
        if not rows:
            empty = EmptyState(
                "No activity yet",
                "Scan and organize a folder — every action will be recorded here.",
            )
            self.flow.insertWidget(0, empty)
            return

        groups: dict = {}
        for r in rows:
            day = str(r.get("performed_at") or r.get("timestamp") or "")[:10] or "Unknown day"
            groups.setdefault(day, []).append(r)

        index = 0
        for day, items in groups.items():
            head = QLabel(day)
            head.setObjectName("daNavGroup")
            self.flow.insertWidget(index, head)
            index += 1
            for r in items:
                self.flow.insertWidget(index, self._row(r))
                index += 1

    def _row(self, r: dict) -> QFrame:
        frame = QFrame()
        frame.setObjectName("daCard")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)

        status = r.get("status", "completed")
        icon_name, _kind = _STATUS_ICON.get(status, ("history", "info"))
        ic = QLabel()
        ic.setFixedSize(20, 20)
        ic.setPixmap(I.pixmap(icon_name, 20, "#8B5CF6"))
        lay.addWidget(ic)

        col = QVBoxLayout()
        col.setSpacing(2)
        source = Path(str(r.get("source_path", "")))
        title = QLabel(f"{str(r.get('action_type', 'move')).title()} • {source.name}")
        title.setStyleSheet("font-size: 13px; font-weight: 600;")
        col.addWidget(title)
        when = QLabel(str(r.get("performed_at") or r.get("timestamp") or "")[:19])
        when.setObjectName("daProgressText")
        col.addWidget(when)
        lay.addLayout(col, 1)

        lay.addWidget(CategoryBadge(r.get("category", "Unknown")))
        st = QLabel(status)
        st.setObjectName("daProgressText")
        lay.addWidget(st)
        return frame

    def _clear(self) -> None:
        while self.flow.count() > 1:
            item = self.flow.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── Undo ─────────────────────────────────────────────────────
    def _start_undo(self):
        self._undo_worker = _UndoWorker(self.service)
        self._undo_worker.done.connect(self._on_undone)
        self._undo_worker.failed.connect(
            lambda m: self._toast("error", "Undo failed", m)
        )
        self._undo_worker.start()

    def _on_undone(self, result: dict):
        self._toast("success", "Undo complete", f"{result.get('reversed', 0)} files restored.")
        self.refresh()

    def _toast(self, kind: str, title: str, msg: str):
        toasts = getattr(self.window(), "toasts", None)
        if toasts:
            getattr(toasts, f"show_{kind}")(title, msg)