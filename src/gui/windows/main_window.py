"""
DesktopAI v2.0 — Main Window
File: src/gui/windows/main_window.py
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from core.constants import APP_NAME, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT
from gui.components.animated_stack import AnimatedStackedWidget
from gui.views.home_view import HomeView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(1000, 700)
        
        self._apply_mac_style()
        self._setup_ui()
        
    def _apply_mac_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #050508;
            }
        """)
        
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Main Content
        content = self._create_main_content()
        main_layout.addWidget(content, 1)

    def _create_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #0A0A0F;
                border-right: 1px solid #1A1A24;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 20, 0, 20)
        
        logo = QLabel("DesktopAI")
        logo.setFont(QFont("SF Pro Display", 20, QFont.Weight.Bold))
        logo.setStyleSheet("color: #FFFFFF; padding: 0 24px 20px 24px;")
        layout.addWidget(logo)
        
        nav = QListWidget()
        nav.setStyleSheet("""
            QListWidget {
                background: transparent; border: none; outline: none;
            }
            QListWidget::item {
                padding: 12px 24px; margin: 4px 12px; border-radius: 8px;
                color: #A1A1AA; font-size: 14px;
            }
            QListWidget::item:hover { background-color: rgba(255,255,255,0.05); color: #FFF; }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(139, 92, 246, 0.2), stop:1 rgba(59, 130, 246, 0.1));
                color: #FFF; border-left: 3px solid #8B5CF6;
            }
        """)
        for item in ["Home", "Organize", "Search", "Chat", "Settings"]:
            QListWidgetItem(item, nav)
        layout.addWidget(nav)
        layout.addStretch()
        return sidebar

    def _create_main_content(self) -> QWidget:
        content = QWidget()
        content.setStyleSheet("background-color: #050508;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 40, 40, 40)
        
        self.page_title = QLabel("Dashboard")
        self.page_title.setFont(QFont("SF Pro Display", 28, QFont.Weight.Bold))
        self.page_title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(self.page_title)
        layout.addSpacing(20)
        
        self.stack = AnimatedStackedWidget()
        self.stack.addWidget(HomeView())
        for _ in range(4):
            empty = QWidget()
            empty.setStyleSheet("background: transparent;")
            self.stack.addWidget(empty)
            
        layout.addWidget(self.stack, 1)
        return content