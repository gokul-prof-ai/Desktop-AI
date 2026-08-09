"""
DesktopAI v2.0 — Search View
File: src/gui/views/search_view.py
"""
from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QFrame, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QStackedWidget,
)

from core.logger import get_logger
from services import FileService

logger = get_logger(__name__)


class SearchView(QWidget):

    def __init__(self, service: FileService) -> None:
        super().__init__()
        self._service = service
        self._scan_results: list[dict] = []   # cached for keyword fallback
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        sub = QLabel(
            "Find files using natural language — DesktopAI understands "
            "context, not just keywords."
        )
        sub.setObjectName("Muted")
        layout.addWidget(sub)

        # Search bar
        bar_card = QFrame()
        bar_card.setObjectName("Card")
        bar_card.setFixedHeight(56)
        bar_layout = QHBoxLayout(bar_card)
        bar_layout.setContentsMargins(16, 0, 12, 0)
        bar_layout.setSpacing(8)

        lbl = QLabel("⊕")
        lbl.setStyleSheet("color: #6C6C70; font-size: 16px;")
        bar_layout.addWidget(lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            'e.g.  "invoices from March"  or  "Python files about databases"'
        )
        self.search_input.setStyleSheet(
            "border: none; background: transparent; font-size: 14px;"
        )
        self.search_input.returnPressed.connect(self._do_search)
        bar_layout.addWidget(self.search_input, 1)

        search_btn = QPushButton("Search")
        search_btn.setObjectName("PrimaryButton")
        search_btn.setFixedWidth(80)
        search_btn.clicked.connect(self._do_search)
        bar_layout.addWidget(search_btn)

        layout.addWidget(bar_card)

        # Filter chips
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        for label in ["All", "Documents", "PDFs", "Images", "Code", "Spreadsheets"]:
            btn = QPushButton(label)
            btn.setObjectName("GhostButton")
            btn.setFixedHeight(26)
            filter_row.addWidget(btn)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Results area
        self.result_stack = QStackedWidget()
        layout.addWidget(self.result_stack, 1)

        # Empty state
        empty = QFrame()
        empty.setObjectName("Card")
        empty_layout = QVBoxLayout(empty)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(8)
        self.status_label = QLabel(
            "No scan loaded. Scan a folder on Home first,\n"
            "then search your files here."
        )
        self.status_label.setObjectName("Muted")
        self.status_label.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.status_label)
        self.result_stack.addWidget(empty)

        # Results table
        table_card = QFrame()
        table_card.setObjectName("Card")
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File", "Category", "Score", "Path"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)

        tc_layout.addWidget(self.table)
        self.result_stack.addWidget(table_card)

    # ── Public API ────────────────────────────────────────────────

    def set_scan_context(self, scan_path: str, results: list) -> None:
        """Called by MainWindow after a scan. results = list of scan dicts."""
        self._scan_results = results
        count = len(results)
        self.status_label.setText(
            f"{count} files indexed from scan.\nEnter a search query above."
        )

    # ── Search ───────────────────────────────────────────────────

    def _do_search(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            return

        # Try semantic search via FileService (uses FAISS)
        matches = self._service.search(query, top_k=20)

        if matches:
            self._populate_from_semantic(matches)
        elif self._scan_results:
            # Fallback: simple keyword match on the cached scan results
            self._populate_from_keyword(query)
        else:
            self.status_label.setText("No index found. Run 'Build Index' from Settings first.")
            self.result_stack.setCurrentIndex(0)

    def _populate_from_semantic(self, matches: list[dict]) -> None:
        """Fill table from FileService.search() results."""
        self.table.setRowCount(len(matches))
        for row, m in enumerate(matches):
            p = Path(m["path"])
            score_pct = int(m["score"] * 100)

            # Try to look up category from cached scan results
            category = "—"
            for r in self._scan_results:
                if r["path"] == str(p):
                    category = r.get("category", "—")
                    break

            self.table.setItem(row, 0, QTableWidgetItem(p.name))
            self.table.setItem(row, 1, QTableWidgetItem(category))
            self.table.setItem(row, 2, QTableWidgetItem(f"{score_pct}%"))
            self.table.setItem(row, 3, QTableWidgetItem(str(p.parent)))
            self.table.setRowHeight(row, 36)

        self.result_stack.setCurrentIndex(1)

    def _populate_from_keyword(self, query: str) -> None:
        """Fallback keyword search over scan results."""
        q = query.lower()
        matches = [
            r for r in self._scan_results
            if q in r["filename"].lower()
            or q in r.get("category", "").lower()
        ]

        self.table.setRowCount(len(matches))
        for row, r in enumerate(matches):
            p = Path(r["path"])
            self.table.setItem(row, 0, QTableWidgetItem(r["filename"]))
            self.table.setItem(row, 1, QTableWidgetItem(r.get("category", "—")))
            self.table.setItem(row, 2, QTableWidgetItem("keyword"))
            self.table.setItem(row, 3, QTableWidgetItem(str(p.parent)))
            self.table.setRowHeight(row, 36)

        self.result_stack.setCurrentIndex(1 if matches else 0)
        if not matches:
            self.status_label.setText(f"No results for '{query}'.")
