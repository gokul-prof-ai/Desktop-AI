"""
DesktopAI v2.0
Search workspace.

Uses fast local matching against the current scan first.
Semantic search can be added without breaking this fallback.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
)


class SearchView(QWidget):

    def __init__(self):
        super().__init__()

        self.results = []

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(14)

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search files by name, category, extension or path..."
        )

        self.search_input.returnPressed.connect(
            self._search
        )

        self.search_button = QPushButton(
            "Search"
        )

        self.search_button.setObjectName(
            "PrimaryButton"
        )

        self.search_button.clicked.connect(
            self._search
        )

        toolbar.addWidget(
            self.search_input,
            1,
        )

        toolbar.addWidget(
            self.search_button
        )

        layout.addLayout(
            toolbar
        )

        self.status = QLabel(
            "Scan a folder from Home to build the local search context."
        )

        self.status.setObjectName(
            "PageSubtitle"
        )

        layout.addWidget(
            self.status
        )

        card = QFrame()
        card.setObjectName(
            "Card"
        )

        card_layout = QVBoxLayout(
            card
        )

        self.table = QTableWidget()

        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels(
            [
                "File",
                "Category",
                "Confidence",
                "Path",
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )

        self.table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents,
        )

        self.table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents,
        )

        self.table.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.Stretch,
        )

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.table.cellDoubleClicked.connect(
            self._open_file
        )

        card_layout.addWidget(
            self.table
        )

        layout.addWidget(
            card,
            1,
        )

    # ==================================================================
    # STATE
    # ==================================================================

    def set_scan_context(
        self,
        _scan_path: str,
        results: list,
    ):

        self.results = results

        self.status.setText(
            f"{len(results)} scanned file(s) available for search."
        )

        self._search()

    # ==================================================================
    # SEARCH
    # ==================================================================

    def _search(self):

        query = (
            self.search_input.text()
            .strip()
            .lower()
        )

        if not query:
            self._show_results(
                self.results
            )

            return

        tokens = [
            token
            for token in query.split()
            if token
        ]

        scored = []

        for result in self.results:

            file_info = result.file_info

            filename = (
                file_info.filename.lower()
            )

            category = (
                result.category.lower()
            )

            extension = (
                file_info.extension.lower()
            )

            path = (
                str(file_info.path).lower()
            )

            haystack = (
                f"{filename} "
                f"{category} "
                f"{extension} "
                f"{path}"
            )

            score = 0

            if query in filename:
                score += 100

            if query in category:
                score += 80

            if query in extension:
                score += 60

            if query in path:
                score += 40

            for token in tokens:
                if token in filename:
                    score += 25

                if token in category:
                    score += 20

                if token in haystack:
                    score += 5

            if score > 0:
                scored.append(
                    (
                        score,
                        result,
                    )
                )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        matches = [
            result
            for _, result in scored
        ]

        self._show_results(
            matches
        )

        self.status.setText(
            f"{len(matches)} matching file(s)."
        )

    def _show_results(
        self,
        results: list,
    ):

        self.table.setRowCount(
            len(results)
        )

        for row, result in enumerate(
            results
        ):

            info = result.file_info

            self.table.setItem(
                row,
                0,
                QTableWidgetItem(
                    info.filename
                ),
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(
                    result.category
                ),
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    f"{int(result.confidence * 100)}%"
                ),
            )

            self.table.setItem(
                row,
                3,
                QTableWidgetItem(
                    str(info.path)
                ),
            )

    def _open_file(
        self,
        row: int,
        _column: int,
    ):

        if row < 0:
            return

        if row >= self.table.rowCount():
            return

        path_item = self.table.item(
            row,
            3,
        )

        if not path_item:
            return

        path = Path(
            path_item.text()
        )

        if path.exists():
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(
                    str(path)
                )
            )