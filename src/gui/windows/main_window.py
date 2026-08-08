"""
DesktopAI v2.0 — Main Window Shell
File: src/gui/windows/main_window.py

The primary application window. Acts ONLY as a navigation shell.
Contains no business logic. Business logic belongs in ViewModels.
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QListWidgetItem, QStackedWidget, QLabel, QFrame
)
from PySide6.QtCore import Qt, QSize
from core.constants import WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT, APP_NAME

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(1024, 680)
        
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Build the main window layout: Sidebar + Content Area."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ── Sidebar ────────────────────────────────────────────────
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        nav_items = [
            ("🏠", "Home"),
            ("📂", "Organize"),
            ("🔍", "Search"),
            ("💬", "Chat"),
            ("⚙️", "Settings"),
        ]
        
        for icon, text in nav_items:
            item = QListWidgetItem(f"  {icon}  {text}")
            item.setSizeHint(QSize(220, 48))
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.sidebar.addItem(item)
            
        self.sidebar.currentRowChanged.connect(self._on_nav_changed)
        
        # ── Content Area ───────────────────────────────────────────
        self.content_area = QStackedWidget()
        self.content_area.setObjectName("ContentArea")
        
        # Placeholder views (will be replaced by actual views in M9-M13)
        for name in ["Home", "Organize", "Search", "Chat", "Settings"]:
            view = self._create_placeholder_view(name)
            self.content_area.addWidget(view)
            
        # Add widgets to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area, 1)  # Content takes remaining space
        
        # Select "Home" by default
        self.sidebar.setCurrentRow(0)

    def _create_placeholder_view(self, name: str) -> QWidget:
        """Create a temporary placeholder view for navigation testing."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel(f"{name} View")
        title.setObjectName("Title")
        
        subtitle = QLabel(f"This is the placeholder for the {name} screen. Will be built in upcoming milestones.")
        subtitle.setObjectName("Subtitle")
        
        # Neomorphic card example
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(QLabel("Future UI components will live inside cards like this."))
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(24)
        layout.addWidget(card)
        layout.addStretch()
        
        return container

    def _on_nav_changed(self, index: int) -> None:
        """Switch the stacked widget to the selected view."""
        self.content_area.setCurrentIndex(index)