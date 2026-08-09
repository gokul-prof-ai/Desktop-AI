"""
DesktopAI v2.0 — Search View (layout fixed)
File: src/gui/views/search_view.py
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt, QTimer


class SearchView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        subtitle = QLabel("Find anything in your files using natural language")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(subtitle)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("Input")
        self.search_input.setPlaceholderText("Search your files... (e.g., 'invoices from 2023')")
        self.search_input.setFixedHeight(52)
        self.search_input.textChanged.connect(self._on_changed)
        layout.addWidget(self.search_input)

        self.results_label = QLabel("Type to search...")
        self.results_label.setObjectName("StatusLabel")
        layout.addWidget(self.results_label)

        self.table = QTableWidget()
        self.table.setObjectName("Table")
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["File", "Category", "Relevance"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setVisible(False)
        layout.addWidget(self.table, 1)

        layout.addStretch(0)  # pack everything to the top

        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._perform_search)

    def _on_changed(self, text: str):
        if text.strip():
            self._timer.start(300)
        else:
            self.table.setVisible(False)
            self.results_label.setText("Type to search...")

    def _perform_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        mock = [
            ("invoice_2023.pdf", "Finance", "0.94"),
            ("budget_report.xlsx", "Finance", "0.87"),
            ("meeting_notes.docx", "Documents", "0.82"),
        ]
        self.table.setRowCount(len(mock))
        for row, (f, c, s) in enumerate(mock):
            self.table.setItem(row, 0, QTableWidgetItem(f))
            self.table.setItem(row, 1, QTableWidgetItem(c))
            self.table.setItem(row, 2, QTableWidgetItem(s))
        self.table.setVisible(True)
        self.results_label.setText(f"Found {len(mock)} results for '{query}'")