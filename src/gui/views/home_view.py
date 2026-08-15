"""
DesktopAI v2.0 — Home View (Premium Dashboard)
File: src/gui/views/home_view.py

Uses centralized icon mapping and FileService-backed ViewModel.
"""
from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QFrame, QProgressBar,
    QSizePolicy,
)

from core.logger import get_logger
from core.events import AppEvents
from gui.components.trendy_drop_zone import MagneticDropZone
from gui.utils.file_icons import icon_for
from gui.viewmodels.home_vm import HomeViewModel
from services import FileService
from PySide6.QtWidgets import QFileDialog

logger = get_logger(__name__)


class HomeView(QWidget):
    """Home dashboard with drop zone, recent folders, and scan results."""
    
    scan_ready = Signal(str, list)  # (scan_path, results)

    def __init__(self, file_service: FileService, parent=None):
        super().__init__(parent)
        self.file_service = file_service
        self.vm = HomeViewModel(file_service)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Build the Home dashboard layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(24)

        # Greeting
        greeting = QLabel("Good morning")
        greeting.setStyleSheet("font-size: 28px; font-weight: 700; color: palette(text);")
        layout.addWidget(greeting)

        subtitle = QLabel("Drop a folder or browse to start organizing")
        subtitle.setStyleSheet("font-size: 14px; color: palette(dark);")
        layout.addWidget(subtitle)

        # Drop zone
        self.drop_zone = MagneticDropZone()
        layout.addWidget(self.drop_zone)

        # Or browse button
        browse_layout = QHBoxLayout()
        browse_btn = QPushButton("Browse Folder")
        browse_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px; border-radius: 8px; font-weight: 600;
                color: white; background-color: #8B5CF6; border: none;
            }
            QPushButton:hover { background-color: #7C3AED; }
        """)
        browse_btn.clicked.connect(self._browse_folder)
        browse_layout.addWidget(browse_btn)
        browse_layout.addStretch()
        layout.addLayout(browse_layout)

        # Stacked widget for scan states
        self.stack = QStackedWidget()
        
        # Page 0: Empty state (before scan)
        empty_page = QWidget()
        empty_layout = QVBoxLayout(empty_page)
        empty_label = QLabel("No scan results yet")
        empty_label.setStyleSheet("color: palette(dark); font-size: 16px;")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_label)
        self.stack.addWidget(empty_page)

        # Page 1: Progress
        progress_page = QWidget()
        progress_layout = QVBoxLayout(progress_page)
        self.progress_label = QLabel("Scanning...")
        self.progress_label.setStyleSheet("font-size: 16px; color: palette(text);")
        progress_layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background-color: #8B5CF6; border-radius: 4px; }
        """)
        progress_layout.addWidget(self.progress_bar)
        self.stack.addWidget(progress_page)

        # Page 2: Results table
        results_page = QWidget()
        results_layout = QVBoxLayout(results_page)
        
        self.results_header = QLabel("Scan Results")
        self.results_header.setStyleSheet("font-size: 20px; font-weight: 600; color: palette(text);")
        results_layout.addWidget(self.results_header)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File", "Category", "Confidence", "Size"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        results_layout.addWidget(self.table)

        self.stack.addWidget(results_page)

        layout.addWidget(self.stack, 1)

    def _connect_signals(self):
        """Connect ViewModel signals to view updates."""
        self.drop_zone.folder_selected.connect(self._on_folder_selected)
        self.vm.scan_started.connect(self._on_scan_started)
        self.vm.scan_progress.connect(self._on_scan_progress)
        self.vm.scan_completed.connect(self._on_scan_completed)
        self.vm.scan_failed.connect(self._on_scan_failed)

    def _browse_folder(self):
        """Open folder picker dialog."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self._on_folder_selected(folder)

    def _on_folder_selected(self, folder_path: str):
        """Start scan for the selected folder."""
        self.vm.start_scan(folder_path)

    def _on_scan_started(self):
        """Show progress UI."""
        self.stack.setCurrentIndex(1)
        self.progress_label.setText("Starting scan...")
        self.progress_bar.setValue(0)

    def _on_scan_progress(self, current: int, total: int):
        """Update progress bar."""
        self.progress_label.setText(f"Scanning {current} / {total} files...")
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)

    def _on_scan_completed(self, results: list[dict]):
        """Display scan results in table."""
        self.stack.setCurrentIndex(2)
        self.results_header.setText(f"Scan Results ({len(results)} files)")
        self.table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # File column with icon
            filename = result.get("filename", "unknown")
            icon = icon_for(filename)
            file_item = QTableWidgetItem(f"{icon} {filename}")
            self.table.setItem(row, 0, file_item)
            
            # Category
            category = result.get("category", "Unknown")
            self.table.setItem(row, 1, QTableWidgetItem(category))
            
            # Confidence (color-coded)
            confidence = result.get("confidence", 0.0)
            conf_item = QTableWidgetItem(f"{int(confidence * 100)}%")
            if confidence >= 0.85:
                conf_item.setForeground(Qt.green)
            elif confidence >= 0.5:
                conf_item.setForeground(Qt.yellow)
            else:
                conf_item.setForeground(Qt.red)
            self.table.setItem(row, 2, conf_item)
            
            # Size
            size_bytes = result.get("size_bytes", 0)
            size_str = self._format_size(size_bytes)
            self.table.setItem(row, 3, QTableWidgetItem(size_str))
        
        # Emit scan_ready for other views
        folder_path = str(Path(results[0]["path"]).parent) if results else ""
        self.scan_ready.emit(folder_path, results)

    def _on_scan_failed(self, error: str):
        """Show error message."""
        self.stack.setCurrentIndex(0)
        logger.error("Scan failed: %s", error)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human-readable form."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"