"""
DesktopAI v2.0 — Search View (Semantic Discovery)
File: src/gui/views/search_view.py

Debounced semantic search on a worker thread, index-build empty
state, stale-index warning after new scans, rich result rows.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QScrollArea,
    QStackedWidget, QVBoxLayout, QWidget,
)

from core.logger import get_logger
from gui.components import icons as I
from gui.components.widgets import (
    ConfidenceBadge, EmptyState, GhostButton, PrimaryButton, SectionHeader,
    StatusIndicator,
)
from gui.theme.design_tokens import tokens_for
from services import FileService

logger = get_logger(__name__)

_EXT_ICON = {
    ".py": "code", ".js": "code", ".ts": "code", ".html": "code",
    ".pdf": "file", ".doc": "file", ".docx": "file", ".txt": "file", ".md": "file",
    ".jpg": "image", ".jpeg": "image", ".png": "image", ".gif": "image",
    ".mp4": "video", ".mkv": "video", ".mp3": "audio", ".wav": "audio",
    ".zip": "archive", ".rar": "archive", ".7z": "archive",
    ".xlsx": "sheet", ".csv": "sheet", ".pptx": "slides",
}


class _SearchWorker(QThread):
    results = Signal(list)
    failed = Signal(str)

    def __init__(self, service: FileService, query: str, parent=None):
        super().__init__(parent)
        self._service = service
        self._query = query

    def run(self):
        try:
            self.results.emit(self._service.search(self._query, top_k=20))
        except Exception as exc:
            self.failed.emit(str(exc))


class _IndexWorker(QThread):
    done = Signal(dict)

    def __init__(self, service: FileService, parent=None):
        super().__init__(parent)
        self._service = service

    def run(self):
        self.done.emit(self._service.build_index())


class SearchView(QWidget):
    """Semantic search over the user's library."""

    def __init__(self, file_service: FileService, parent=None):
        super().__init__(parent)
        self.service = file_service
        self._stale = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.header = SectionHeader(
            "Search your library",
            "Find files by name, type, content, or meaning.",
        )
        layout.addWidget(self.header)

        # Search box
        box = QFrame()
        box.setObjectName("daCard")
        box.setFixedHeight(52)
        bl = QHBoxLayout(box)
        bl.setContentsMargins(14, 0, 14, 0)
        bl.setSpacing(10)
        self._box_icon = QLabel()
        self._box_icon.setFixedSize(20, 20)
        bl.addWidget(self._box_icon)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Search your files…")
        self.input.setStyleSheet("border: none; background: transparent; font-size: 15px;")
        self.input.textChanged.connect(self._on_text_changed)
        bl.addWidget(self.input, 1)
        layout.addWidget(box)

        # Suggestions
        sug = QHBoxLayout()
        sug.setSpacing(8)
        for text in ("invoices", "reports", "python", "images", "documents"):
            b = GhostButton(text)
            b.clicked.connect(lambda _c, t=text: self.input.setText(t))
            sug.addWidget(b)
        sug.addStretch()
        layout.addLayout(sug)

        # Stale-index warning (hidden by default)
        self.stale_row = QWidget()
        sl = QHBoxLayout(self.stale_row)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(8)
        self.stale_indicator = StatusIndicator("Index may be outdated", "warn")
        sl.addWidget(self.stale_indicator)
        sl.addStretch()
        rebuild = GhostButton("Rebuild Index")
        rebuild.clicked.connect(self._build_index)
        sl.addWidget(rebuild)
        self.stale_row.hide()
        layout.addWidget(self.stale_row)

        # Stack: 0 = no index, 1 = results
        self.stack = QStackedWidget()

        no_index = QWidget()
        ni_lay = QVBoxLayout(no_index)
        ni_lay.setAlignment(Qt.AlignCenter)
        self.empty_index = EmptyState(
            "Your search index isn't ready",
            "Build an index to search your files intelligently.",
        )
        build_btn = PrimaryButton("Build Search Index")
        build_btn.clicked.connect(self._build_index)
        self.empty_index.add_action(build_btn)
        ni_lay.addWidget(self.empty_index)
        self.stack.addWidget(no_index)

        results_page = QWidget()
        rp_lay = QVBoxLayout(results_page)
        rp_lay.setSpacing(10)
        self.results_status = QLabel("")
        self.results_status.setObjectName("daSectionSub")
        rp_lay.addWidget(self.results_status)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.results_content = QWidget()
        self.results_content.setStyleSheet("background: transparent;")
        self.results_layout = QVBoxLayout(self.results_content)
        self.results_layout.setSpacing(8)
        self.results_layout.addStretch()
        scroll.setWidget(self.results_content)
        rp_lay.addWidget(scroll, 1)

        self.no_results = EmptyState(
            "No files found",
            "Try another search phrase or adjust your filters.",
        )
        self.no_results.hide()
        rp_lay.addWidget(self.no_results)

        self.stack.addWidget(results_page)
        self.stack.setCurrentIndex(1)
        layout.addWidget(self.stack, 1)

        # Debounce
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(300)
        self._timer.timeout.connect(self._run_search)

        self._refresh_icons()

    # ── Theme-aware icon for the box ──────────────────────────────
    def _refresh_icons(self):
        try:
            from infrastructure.config.settings import Settings
            theme = Settings.app.theme
        except Exception:
            theme = "dark"
        t = tokens_for(theme)
        self._box_icon.setPixmap(I.pixmap("search", 20, t["muted"]))

    def showEvent(self, event):
        self._refresh_icons()
        super().showEvent(event)

    # ── Context from scans ────────────────────────────────────────
    def set_scan_context(self, path: str, results: list) -> None:
        if results:
            self._stale = True
            self.stale_row.show()

    # ── Search flow ───────────────────────────────────────────────
    def _on_text_changed(self, text: str):
        if text.strip():
            self._timer.start()
        else:
            self._clear_results()

    def _run_search(self):
        query = self.input.text().strip()
        if not query:
            return
        self.results_status.setText(f"✦ AI search — finding files related to: “{query}”")
        self._worker = _SearchWorker(self.service, query)
        self._worker.results.connect(self._on_results)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_failed(self, message: str):
        if "index" in message.lower():
            self.stack.setCurrentIndex(0)
        else:
            self.results_status.setText("")
            toasts = getattr(self.window(), "toasts", None)
            if toasts:
                toasts.show_error("Search failed", message)

    def _on_results(self, results: list):
        self.stack.setCurrentIndex(1)
        self._clear_results()
        if not results:
            self.no_results.show()
            self.results_status.setText("No matches.")
            return
        self.no_results.hide()
        self.results_status.setText(f"{len(results)} results")
        for r in results:
            self.results_layout.insertWidget(0, self._result_row(r))
        # remove trailing stretch remains at bottom

    def _clear_results(self):
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.no_results.hide()

    def _result_row(self, r: dict) -> QFrame:
        path = Path(r.get("path", ""))
        ext = path.suffix.lower()
        row = QFrame()
        row.setObjectName("daCard")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)

        ic = QLabel()
        ic.setFixedSize(20, 20)
        ic.setPixmap(I.pixmap(_EXT_ICON.get(ext, "file"), 20, "#8B5CF6"))
        lay.addWidget(ic)

        col = QVBoxLayout()
        col.setSpacing(2)
        name = QLabel(path.name)
        name.setObjectName("daStatLabel")
        name.setStyleSheet("font-size: 13px; font-weight: 600;")
        col.addWidget(name)
        loc = QLabel(str(path.parent))
        loc.setObjectName("daProgressText")
        col.addWidget(loc)
        lay.addLayout(col, 1)

        lay.addWidget(ConfidenceBadge(r.get("score", 0.0)))
        return row

    # ── Index building ────────────────────────────────────────────
    def _build_index(self):
        self.stale_row.hide()
        self._index_worker = _IndexWorker(self.service)
        self._index_worker.done.connect(self._on_index_done)
        self._index_worker.start()

    def _on_index_done(self, result: dict):
        toasts = getattr(self.window(), "toasts", None)
        if result.get("error"):
            if toasts:
                toasts.show_error("Index failed", result["error"])
        else:
            self._stale = False
            self.stack.setCurrentIndex(1)
            if toasts:
                toasts.show_success("Search index ready", f"{result.get('indexed', 0)} file(s) indexed.")
            if self.input.text().strip():
                self._run_search()