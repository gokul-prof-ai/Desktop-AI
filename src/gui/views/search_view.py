"""
DesktopAI v2.0 — Search View
File: src/gui/views/search_view.py
"""
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QFrame, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QStackedWidget,
)


class SearchView(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self._results: list = []
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

        # Search bar card
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
        self.table.setHorizontalHeaderLabels(["File", "Category", "Size", "Path"])
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

    def set_scan_context(self, scan_path: str, results: list) -> None:
        self._results = results
        self.status_label.setText(
            f"{len(results)} files indexed from scan.\n"
            "Enter a search query above."
        )

    def _do_search(self) -> None:
        query = self.search_input.text().strip().lower()
        if not query or not self._results:
            return

        matches = [
            r for r in self._results
            if query in r.file_info.filename.lower()
            or (r.category and query in r.category.lower())
            or (r.file_info.text_content and query in r.file_info.text_content.lower())
        ]

        self.table.setRowCount(len(matches))
        for row, r in enumerate(matches):
            fi = r.file_info
            self.table.setItem(row, 0, QTableWidgetItem(fi.filename))
            self.table.setItem(row, 1, QTableWidgetItem(r.category or "—"))
            self.table.setItem(row, 2, QTableWidgetItem(fi.display_size))
            self.table.setItem(row, 3, QTableWidgetItem(str(fi.path.parent)))
            self.table.setRowHeight(row, 36)

        self.result_stack.setCurrentIndex(1)