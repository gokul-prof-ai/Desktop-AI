"""
DesktopAI v2.0 — Search View
File: src/gui/views/search_view.py

Three-tier search strategy:
  1. FAISS semantic search (via FileService -> search_engine)
  2. In-memory keyword + category search across cached scan results
  3. Graceful empty state with hints when nothing is indexed yet

The FAISS index is built lazily. If semantic search is unavailable or
returns no hits, the view falls back to keyword/category matching.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFrame,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QStackedWidget,
    QProgressBar,
)

from core.logger import get_logger
from services import FileService


logger = get_logger(__name__)


_FILTER_CATEGORIES = [
    "All",
    "Documents",
    "PDFs",
    "Images",
    "Code",
    "Spreadsheets",
    "Archives",
]


class _SearchWorker(QThread):
    """Run semantic search off the GUI thread."""

    results_ready = Signal(list)
    error = Signal(str)

    def __init__(
        self,
        service: FileService,
        query: str,
        top_k: int = 30,
    ) -> None:
        super().__init__()
        self._service = service
        self._query = query
        self._top_k = top_k

    def run(self) -> None:
        try:
            hits = self._service.search(
                self._query,
                top_k=self._top_k,
            )
            self.results_ready.emit(hits or [])
        except Exception as exc:
            logger.exception("SearchWorker error")
            self.error.emit(str(exc))


class SearchView(QWidget):
    """Search page for DesktopAI."""

    def __init__(self, service: FileService) -> None:
        super().__init__()

        self._service = service
        self._scan_results: list[dict] = []
        self._scan_path: str = ""
        self._active_filter = "All"
        self._worker: _SearchWorker | None = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        subtitle = QLabel(
            "Find files using natural language — DesktopAI understands "
            "context, not just keywords."
        )
        subtitle.setObjectName("Muted")
        layout.addWidget(subtitle)

        # Search bar
        bar_card = QFrame()
        bar_card.setObjectName("Card")
        bar_card.setFixedHeight(56)

        bar_layout = QHBoxLayout(bar_card)
        bar_layout.setContentsMargins(16, 0, 12, 0)
        bar_layout.setSpacing(8)

        icon_label = QLabel("⌕")
        icon_label.setObjectName("Muted")
        icon_label.setFixedWidth(22)
        bar_layout.addWidget(icon_label)

        self._input = QLineEdit()
        self._input.setPlaceholderText(
            'e.g. "invoices from March" or "Python files about databases"'
        )
        self._input.setStyleSheet(
            "border: none; background: transparent; font-size: 14px;"
        )
        self._input.returnPressed.connect(self._do_search)
        bar_layout.addWidget(self._input, 1)

        self._search_btn = QPushButton("Search")
        self._search_btn.setObjectName("PrimaryButton")
        self._search_btn.setFixedWidth(80)
        self._search_btn.clicked.connect(self._do_search)
        bar_layout.addWidget(self._search_btn)

        layout.addWidget(bar_card)

        # Filter chips
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)

        self._filter_btns: dict[str, QPushButton] = {}

        for label in _FILTER_CATEGORIES:
            button = QPushButton(label)
            button.setObjectName("GhostButton")
            button.setFixedHeight(26)
            button.setCheckable(True)
            button.setChecked(label == "All")
            button.clicked.connect(
                lambda _checked=False, value=label: self._set_filter(value)
            )

            filter_row.addWidget(button)
            self._filter_btns[label] = button

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(3)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Results stack
        self._stack = QStackedWidget()
        layout.addWidget(self._stack, 1)

        # Page 0: empty state
        empty_frame = QFrame()
        empty_frame.setObjectName("Card")

        empty_layout = QVBoxLayout(empty_frame)
        empty_layout.setAlignment(Qt.AlignCenter)

        self._status_lbl = QLabel(
            "No scan loaded.\n"
            "Scan a folder on Home first, then search here."
        )
        self._status_lbl.setObjectName("Muted")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setWordWrap(True)

        empty_layout.addWidget(self._status_lbl)
        self._stack.addWidget(empty_frame)

        # Page 1: results table
        table_frame = QFrame()
        table_frame.setObjectName("Card")

        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["File", "Category", "Match", "Path"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.Stretch,
        )

        table_layout.addWidget(self._table)
        self._stack.addWidget(table_frame)

        self._stack.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_scan_context(
        self,
        scan_path: str,
        results: list,
    ) -> None:
        """Receive completed scan results from MainWindow/HomeView."""
        self._scan_path = str(scan_path or "")
        self._scan_results = [
            item
            for item in (results or [])
            if isinstance(item, dict)
        ]

        self._clear_results()

        count = len(self._scan_results)

        if count == 0:
            self._status_lbl.setText(
                "No supported files found in the latest scan."
            )
            self._stack.setCurrentIndex(0)
            return

        self._status_lbl.setText(
            f"{count} files available.\n"
            "Type a query and press Search.\n"
            "Semantic search is attempted first, with keyword fallback."
        )
        self._stack.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Filter handling
    # ------------------------------------------------------------------

    def _set_filter(self, label: str) -> None:
        """Set the active category filter and refresh the current search."""
        self._active_filter = label

        for current_label, button in self._filter_btns.items():
            button.setChecked(current_label == label)

        if self._input.text().strip():
            self._do_search()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _do_search(self) -> None:
        """Start semantic search in a background thread."""
        query = self._input.text().strip()

        if not query:
            self._status_lbl.setText(
                "Enter a search query first."
            )
            self._stack.setCurrentIndex(0)
            return

        if self._worker is not None and self._worker.isRunning():
            return

        self._search_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)

        self._clear_results()

        worker = _SearchWorker(
            self._service,
            query,
            top_k=30,
        )

        worker.results_ready.connect(
            self._on_semantic_results
        )
        worker.error.connect(
            self._on_semantic_error
        )
        worker.finished.connect(
            self._on_worker_finished
        )

        self._worker = worker
        worker.start()

    def _on_semantic_results(
        self,
        hits: list[dict],
    ) -> None:
        """Handle successful semantic-search results."""
        if hits:
            path_to_category = {
                str(item.get("path", "")): str(
                    item.get("category") or "—"
                )
                for item in self._scan_results
            }

            rows: list[dict] = []

            for hit in hits:
                if not isinstance(hit, dict):
                    continue

                raw_path = str(hit.get("path", "")).strip()
                if not raw_path:
                    continue

                category = path_to_category.get(
                    raw_path,
                    "—",
                )

                if (
                    self._active_filter != "All"
                    and category != self._active_filter
                ):
                    continue

                try:
                    score = float(hit.get("score", 0.0))
                except (TypeError, ValueError):
                    score = 0.0

                score = max(0.0, min(1.0, score))

                rows.append(
                    {
                        "filename": Path(raw_path).name,
                        "category": category,
                        "match": f"{int(score * 100)}%",
                        "parent": str(Path(raw_path).parent),
                    }
                )

            if rows:
                self._populate_table(
                    rows,
                    match_label="Semantic",
                )
                return

        # No usable semantic matches: fallback.
        self._keyword_fallback(
            self._input.text().strip()
        )

    def _on_semantic_error(
        self,
        error_message: str,
    ) -> None:
        """Fallback gracefully when semantic search is unavailable."""
        logger.warning(
            "Semantic search unavailable; using keyword fallback: %s",
            error_message,
        )

        self._keyword_fallback(
            self._input.text().strip()
        )

    def _on_worker_finished(self) -> None:
        """Restore UI state after the worker exits."""
        self._progress.setVisible(False)
        self._search_btn.setEnabled(True)

        worker = self._worker
        self._worker = None

        if worker is not None:
            worker.deleteLater()

    # ------------------------------------------------------------------
    # Keyword fallback
    # ------------------------------------------------------------------

    def _keyword_fallback(
        self,
        query: str,
    ) -> None:
        """Search the latest scan results using filename/category text."""
        normalized_query = query.casefold()
        matches: list[dict] = []

        for result in self._scan_results:
            if result.get("skipped"):
                continue

            category = str(
                result.get("category") or ""
            )
            filename = str(
                result.get("filename") or ""
            )
            path_value = str(
                result.get("path") or ""
            )

            if (
                self._active_filter != "All"
                and category != self._active_filter
            ):
                continue

            searchable_text = " ".join(
                (
                    filename,
                    category,
                    path_value,
                )
            ).casefold()

            if normalized_query in searchable_text:
                matches.append(
                    {
                        "filename": filename or Path(path_value).name,
                        "category": category or "—",
                        "match": "keyword",
                        "parent": (
                            str(Path(path_value).parent)
                            if path_value
                            else "—"
                        ),
                    }
                )

        if matches:
            self._populate_table(
                matches,
                match_label="Keyword",
            )
            return

        safe_query = query.replace("\n", " ").strip()

        self._status_lbl.setText(
            f'No results for "{safe_query}".'
        )
        self._stack.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Table rendering
    # ------------------------------------------------------------------

    def _populate_table(
        self,
        rows: list[dict],
        match_label: str = "",
    ) -> None:
        """Populate the result table and switch to the result page."""
        self._table.setRowCount(0)

        for row_index, row in enumerate(rows):
            self._table.insertRow(row_index)

            self._table.setItem(
                row_index,
                0,
                QTableWidgetItem(
                    str(row.get("filename") or "—")
                ),
            )
            self._table.setItem(
                row_index,
                1,
                QTableWidgetItem(
                    str(row.get("category") or "—")
                ),
            )
            self._table.setItem(
                row_index,
                2,
                QTableWidgetItem(
                    str(row.get("match") or "—")
                ),
            )
            self._table.setItem(
                row_index,
                3,
                QTableWidgetItem(
                    str(row.get("parent") or "—")
                ),
            )

            self._table.setRowHeight(
                row_index,
                36,
            )

        count = len(rows)

        logger.info(
            "SearchView: %d %s results",
            count,
            match_label.lower(),
        )

        self._stack.setCurrentIndex(
            1 if rows else 0
        )

        if not rows:
            query = self._input.text().strip()
            self._status_lbl.setText(
                f'No results for "{query}".'
            )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _clear_results(self) -> None:
        """Clear previous search results."""
        self._table.setRowCount(0)