"""
DesktopAI v2.0 — Home View
File: src/gui/views/home_view.py

The main landing page. Features the MagneticDropZone and a 
real-time results table that appears after scanning.
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QStackedWidget, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from gui.components.trendy_drop_zone import MagneticDropZone
from gui.viewmodels.home_vm import HomeViewModel
from core.logger import get_logger

logger = get_logger(__name__)


class HomeView(QWidget):
    """
    Home screen with Drop Zone and Results Table.
    """
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        
        self.vm = HomeViewModel()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Stacked widget to switch between Drop Zone and Results
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")
        
        # ── Page 0: Drop Zone ──────────────────────────────────────
        drop_page = QWidget()
        drop_layout = QVBoxLayout(drop_page)
        drop_layout.setAlignment(Qt.AlignCenter)
        drop_layout.setSpacing(20)
        
        title = QLabel("Welcome to DesktopAI")
        title.setStyleSheet("""
            font-size: 32px; font-weight: 700; color: #FFFFFF;
            letter-spacing: -1px; font-family: 'SF Pro Display', 'Inter', sans-serif;
        """)
        title.setAlignment(Qt.AlignCenter)
        drop_layout.addWidget(title)
        
        sub = QLabel("Organize your files intelligently with AI.")
        sub.setStyleSheet("font-size: 16px; color: #A1A1AA; font-family: 'SF Pro Display', 'Inter', sans-serif;")
        sub.setAlignment(Qt.AlignCenter)
        drop_layout.addWidget(sub)
        
        drop_layout.addSpacing(40)
        
        self.drop_zone = MagneticDropZone()
        self.drop_zone.folder_selected.connect(self._on_folder_selected)
        drop_layout.addWidget(self.drop_zone, alignment=Qt.AlignCenter)
        
        self.stack.addWidget(drop_page)
        
        # ── Page 1: Results Table ──────────────────────────────────
        results_page = self._create_results_page()
        self.stack.addWidget(results_page)
        
        layout.addWidget(self.stack)
        
        # Connect ViewModel signals
        self.vm.scan_progress.connect(self._on_scan_progress)
        self.vm.scan_completed.connect(self._on_scan_completed)
        self.vm.scan_failed.connect(self._on_scan_failed)
        
    def _create_results_page(self) -> QWidget:
        """Build the results table UI."""
        page = QWidget()
        page.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        self.results_title = QLabel("Scan Results")
        self.results_title.setFont(QFont("SF Pro Display", 24, QFont.Weight.Bold))
        self.results_title.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(self.results_title)
        
        self.results_subtitle = QLabel("Analyzing files...")
        self.results_subtitle.setFont(QFont("SF Pro Display", 14))
        self.results_subtitle.setStyleSheet("color: #A1A1AA;")
        header_layout.addWidget(self.results_subtitle)
        
        layout.addLayout(header_layout)
        layout.addSpacing(20)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["File Name", "Category", "Confidence"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0A0A0F;
                border: 1px solid #1A1A24;
                border-radius: 12px;
                gridline-color: #1A1A24;
                color: #E4E4E7;
                font-family: 'SF Pro Display', 'Inter', sans-serif;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #1A1A24;
            }
            QHeaderView::section {
                background-color: #0A0A0F;
                color: #71717A;
                padding: 12px;
                border: none;
                border-bottom: 1px solid #1A1A24;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 11px;
                letter-spacing: 1px;
            }
            QScrollBar:vertical {
                background-color: #0A0A0F;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #2A2A35;
                border-radius: 4px;
                min-height: 30px;
            }
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.table, 1)
        
        # Footer / Back button
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        self.btn_back = QPushButton("Scan Another Folder")
        self.btn_back.setObjectName("SecondaryButton")
        self.btn_back.setFixedSize(180, 40)
        self.btn_back.clicked.connect(self._on_back_clicked)
        footer_layout.addWidget(self.btn_back)
        
        layout.addLayout(footer_layout)
        
        return page
        
    def _on_folder_selected(self, path: str):
        """Handle folder selection from drop zone."""
        logger.info("HomeView: Folder selected -> %s", path)
        self.vm.start_scan(path)
        self.stack.setCurrentIndex(1)  # Switch to results page
        self.results_subtitle.setText("Scanning files...")
        self.table.setRowCount(0)  # Clear previous results
        
    def _on_scan_progress(self, done: int, total: int):
        """Update progress subtitle."""
        self.results_subtitle.setText(f"Classifying files... ({done}/{total})")
        
    def _on_scan_completed(self, results: list):
        """Populate table with results."""
        self.results_subtitle.setText(f"Scan complete. {len(results)} files analyzed.")
        self.table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # File Name
            name_item = QTableWidgetItem(result.file_info.filename)
            name_item.setForeground(Qt.white)
            self.table.setItem(row, 0, name_item)
            
            # Category
            cat_item = QTableWidgetItem(result.category)
            cat_item.setForeground(Qt.white)
            self.table.setItem(row, 1, cat_item)
            
            # Confidence
            conf_pct = int(result.confidence * 100)
            conf_item = QTableWidgetItem(f"{conf_pct}%")
            
            # Color code confidence
            if conf_pct >= 80:
                conf_item.setForeground(Qt.green)
            elif conf_pct >= 50:
                conf_item.setForeground(Qt.yellow)
            else:
                conf_item.setForeground(Qt.red)
                
            self.table.setItem(row, 2, conf_item)
            
    def _on_scan_failed(self, error_msg: str):
        """Handle scan errors."""
        self.results_subtitle.setText(f"Scan failed: {error_msg}")
        logger.error("Scan failed: %s", error_msg)
        
    def _on_back_clicked(self):
        """Return to drop zone."""
        self.stack.setCurrentIndex(0)  # Back to drop zone