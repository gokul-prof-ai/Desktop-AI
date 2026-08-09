"""
DesktopAI v2.0 — Home View (theme-aware)
File: src/gui/views/home_view.py
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QStackedWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QHBoxLayout,
)
from PySide6.QtCore import Qt
from gui.components.trendy_drop_zone import MagneticDropZone
from gui.components.sound_button import SoundButton
from gui.viewmodels.home_vm import HomeViewModel
from core.logger import get_logger

logger = get_logger(__name__)


class HomeView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent;")
        self.vm = HomeViewModel()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")

        # ── Page 0: Drop Zone ─────────────────────────────────────
        drop_page = QWidget()
        drop_layout = QVBoxLayout(drop_page)
        drop_layout.setAlignment(Qt.AlignCenter)
        drop_layout.setSpacing(20)

        hint = QLabel("Drop a folder to scan, or click to browse")
        hint.setObjectName("PageSubtitle")
        hint.setAlignment(Qt.AlignCenter)
        drop_layout.addWidget(hint)

        self.drop_zone = MagneticDropZone()
        self.drop_zone.folder_selected.connect(self._on_folder_selected)
        drop_layout.addWidget(self.drop_zone, alignment=Qt.AlignCenter)
        self.stack.addWidget(drop_page)

        # ── Page 1: Results ───────────────────────────────────────
        results_page = self._create_results_page()
        self.stack.addWidget(results_page)

        layout.addWidget(self.stack, 1)

        self.vm.scan_progress.connect(self._on_scan_progress)
        self.vm.scan_completed.connect(self._on_scan_completed)
        self.vm.scan_failed.connect(self._on_scan_failed)

    def _create_results_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Scan Results")
        title.setObjectName("AccentLabel")
        layout.addWidget(title)

        self.results_subtitle = QLabel("Analyzing files...")
        self.results_subtitle.setObjectName("StatusLabel")
        layout.addWidget(self.results_subtitle)

        self.table = QTableWidget()
        self.table.setObjectName("Table")
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["File Name", "Category", "Confidence"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table, 1)

        footer = QHBoxLayout()
        footer.addStretch()
        self.btn_back = SoundButton("Scan Another Folder")
        self.btn_back.setObjectName("SecondaryButton")
        self.btn_back.setFixedSize(180, 44)
        self.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        footer.addWidget(self.btn_back)
        layout.addLayout(footer)
        return page

    def _on_folder_selected(self, path: str):
        self.vm.start_scan(path)
        self.stack.setCurrentIndex(1)
        self.results_subtitle.setText("Scanning files...")
        self.table.setRowCount(0)

    def _on_scan_progress(self, done: int, total: int):
        self.results_subtitle.setText(f"Classifying files... ({done}/{total})")

    def _on_scan_completed(self, results: list):
        self.results_subtitle.setText(f"Scan complete. {len(results)} files analyzed.")
        self.table.setRowCount(len(results))
        for row, r in enumerate(results):
            self.table.setItem(row, 0, QTableWidgetItem(r.file_info.filename))
            self.table.setItem(row, 1, QTableWidgetItem(r.category))
            pct = int(r.confidence * 100)
            item = QTableWidgetItem(f"{pct}%")
            item.setForeground(Qt.green if pct >= 80 else (Qt.yellow if pct >= 50 else Qt.red))
            self.table.setItem(row, 2, item)

    def _on_scan_failed(self, msg: str):
        self.results_subtitle.setText(f"Scan failed: {msg}")