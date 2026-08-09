"""
DesktopAI v2.0 — Home View (App Shell UI)
File: src/gui/views/home_view.py

Console-type layout:
  - Stat row (3 cards: Files Scanned, Categories, Operations)
  - Drop zone hero card
  - Results table (appears after scan)
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QStackedWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gui.components.trendy_drop_zone import MagneticDropZone
from gui.viewmodels.home_vm import HomeViewModel
from infrastructure.storage.database import DB
from core.logger import get_logger

logger = get_logger(__name__)

_CONTENT_PADDING = 24


class HomeView(QWidget):
    """Home screen — stat cards + drop zone + results."""

    def __init__(self) -> None:
        super().__init__()
        self.vm = HomeViewModel()
        self._setup_ui()
        self._connect_signals()
        self._refresh_stats()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(_CONTENT_PADDING, _CONTENT_PADDING,
                                _CONTENT_PADDING, _CONTENT_PADDING)
        root.setSpacing(16)

        # Stat row
        stat_row = self._build_stat_row()
        root.addWidget(stat_row)

        # Page switcher: drop zone ↔ results
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_drop_page())
        self.stack.addWidget(self._build_results_page())
        root.addWidget(self.stack, 1)

    def _build_stat_row(self) -> QWidget:
        """Three stat cards in a horizontal row."""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.stat_files = self._stat_card("Files Tracked", "0")
        self.stat_cats  = self._stat_card("Categories", "11")
        self.stat_ops   = self._stat_card("Operations", "0")

        layout.addWidget(self.stat_files)
        layout.addWidget(self.stat_cats)
        layout.addWidget(self.stat_ops)

        return row

    def _stat_card(self, label: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("StatCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("StatValue")
        layout.addWidget(val_lbl)

        lbl = QLabel(label)
        lbl.setObjectName("StatLabel")
        layout.addWidget(lbl)

        # Store reference for updates
        card._value_label = val_lbl
        return card

    def _build_drop_page(self) -> QWidget:
        """Drop zone hero page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        subtitle = QLabel("Drop a folder to begin AI-powered organization")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #A1A1A6; font-size: 13px;")
        layout.addWidget(subtitle)

        self.drop_zone = MagneticDropZone()
        self.drop_zone.folder_selected.connect(self._on_folder_selected)
        layout.addWidget(self.drop_zone, alignment=Qt.AlignCenter)

        return page

    def _build_results_page(self) -> QWidget:
        """Results table page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Sub-header
        self.results_label = QLabel("Analyzing files...")
        self.results_label.setStyleSheet("color: #A1A1A6; font-size: 13px;")
        layout.addWidget(self.results_label)

        # Results table in a card
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["File Name", "Category", "Confidence"])
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        card_layout.addWidget(self.table)
        layout.addWidget(card, 1)

        # Footer
        footer = QHBoxLayout()
        footer.addStretch()

        back_btn = QPushButton("Scan Another Folder")
        back_btn.setObjectName("SecondaryButton")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        footer.addWidget(back_btn)

        layout.addLayout(footer)
        return page

    def _connect_signals(self) -> None:
        self.vm.scan_progress.connect(self._on_scan_progress)
        self.vm.scan_completed.connect(self._on_scan_completed)
        self.vm.scan_failed.connect(self._on_scan_failed)

    def _refresh_stats(self) -> None:
        """Pull live stats from the database."""
        try:
            stats = DB.get_stats()
            self.stat_files._value_label.setText(str(stats["total_files"]))
            self.stat_ops._value_label.setText(str(stats["total_operations"]))
        except Exception:
            pass

    # ── Handlers ───────────────────────────────────────────────────

    def _on_folder_selected(self, path: str) -> None:
        logger.info("Folder selected: %s", path)
        self.vm.start_scan(path)
        self.table.setRowCount(0)
        self.results_label.setText("Scanning files...")
        self.stack.setCurrentIndex(1)

    def _on_scan_progress(self, done: int, total: int) -> None:
        self.results_label.setText(f"Classifying files... ({done} / {total})")

    def _on_scan_completed(self, results: list) -> None:
        self.results_label.setText(
            f"Scan complete — {len(results)} files analyzed"
        )
        self.table.setRowCount(len(results))
        self._refresh_stats()

        for row, result in enumerate(results):
            # Filename
            self.table.setItem(row, 0,
                QTableWidgetItem(result.file_info.filename))

            # Category
            self.table.setItem(row, 1,
                QTableWidgetItem(result.category))

            # Confidence pill-style
            pct = int(result.confidence * 100)
            conf_item = QTableWidgetItem(f"{pct}%")
            if pct >= 80:
                conf_item.setForeground(Qt.green)
            elif pct >= 50:
                conf_item.setForeground(Qt.yellow)
            else:
                conf_item.setForeground(Qt.red)
            self.table.setItem(row, 2, conf_item)

    def _on_scan_failed(self, msg: str) -> None:
        self.results_label.setText(f"Scan failed: {msg}")
        logger.error("Scan failed: %s", msg)