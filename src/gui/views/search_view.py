"""
DesktopAI v2.0 — Search View (App Shell UI)
File: src/gui/views/search_view.py

Workbench layout:
  - Search bar (full width)
  - Results area (card with placeholder)
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QFrame, QPushButton, QSizePolicy,
)
from PySide6.QtCore import Qt

_PAD = 24


class SearchView(QWidget):
    """Semantic search screen."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(_PAD, _PAD, _PAD, _PAD)
        root.setSpacing(16)

        # Sub-header
        sub = QLabel(
            "Find files using natural language — the AI understands context, not just keywords."
        )
        sub.setStyleSheet("color: #A1A1A6; font-size: 13px;")
        root.addWidget(sub)

        # ── Search bar ─────────────────────────────────────────────
        bar_row = QHBoxLayout()
        bar_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText(
            "e.g.  invoices from March  or  python scripts about databases"
        )
        self.search_input.setFixedHeight(38)
        bar_row.addWidget(self.search_input, 1)

        search_btn = QPushButton("Search")
        search_btn.setObjectName("PrimaryButton")
        search_btn.setFixedHeight(38)
        search_btn.setFixedWidth(80)
        bar_row.addWidget(search_btn)

        root.addLayout(bar_row)

        # ── Results card ───────────────────────────────────────────
        card = QFrame()
        card.setObjectName("Card")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(0)

        # Card header
        card_header = QHBoxLayout()
        results_title = QLabel("Results")
        results_title.setStyleSheet(
            "color: #F5F5F7; font-size: 13px; font-weight: 600;"
        )
        card_header.addWidget(results_title)
        card_header.addStretch()

        self.results_count = QLabel("—")
        self.results_count.setStyleSheet("color: #6C6C70; font-size: 12px;")
        card_header.addWidget(self.results_count)

        card_layout.addLayout(card_header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            "background: rgba(255,255,255,0.08); border: none; max-height: 1px;"
        )
        card_layout.addSpacing(12)
        card_layout.addWidget(sep)
        card_layout.addSpacing(12)

        # Empty state
        self.empty_label = QLabel(
            "Type a search query above and press Search.\n"
            "Build the search index by scanning a folder first."
        )
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet(
            "color: #6C6C70; font-size: 13px; line-height: 1.6;"
        )
        card_layout.addWidget(self.empty_label, 1, Qt.AlignCenter)

        root.addWidget(card, 1)