"""
DesktopAI v2.0 — Custom Title Bar
File: src/gui/components/title_bar.py

Mac-style title bar with traffic light buttons.
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class TitleBar(QWidget):
    """
    Custom title bar with Mac-style traffic light buttons.
    """
    close_clicked = Signal()
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    
    def __init__(self, title: str = "DesktopAI", parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self._setup_ui(title)
    
    def _setup_ui(self, title: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(12)
        
        # Traffic light buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        self.btn_close = QPushButton()
        self.btn_close.setFixedSize(14, 14)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #FF5F57;
                border-radius: 7px;
                border: none;
            }
            QPushButton:hover {
                background-color: #FF3B30;
            }
        """)
        self.btn_close.clicked.connect(self.close_clicked.emit)
        buttons_layout.addWidget(self.btn_close)
        
        self.btn_minimize = QPushButton()
        self.btn_minimize.setFixedSize(14, 14)
        self.btn_minimize.setStyleSheet("""
            QPushButton {
                background-color: #FEBC2E;
                border-radius: 7px;
                border: none;
            }
            QPushButton:hover {
                background-color: #FFA500;
            }
        """)
        self.btn_minimize.clicked.connect(self.minimize_clicked.emit)
        buttons_layout.addWidget(self.btn_minimize)
        
        self.btn_maximize = QPushButton()
        self.btn_maximize.setFixedSize(14, 14)
        self.btn_maximize.setStyleSheet("""
            QPushButton {
                background-color: #28C840;
                border-radius: 7px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1E9E32;
            }
        """)
        self.btn_maximize.clicked.connect(self.maximize_clicked.emit)
        buttons_layout.addWidget(self.btn_maximize)
        
        layout.addLayout(buttons_layout)
        
        # Title label
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("SF Pro Display", 14, QFont.Weight.Medium))
        self.title_label.setStyleSheet("color: #FFFFFF;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label, 1)
        
        # Spacer for balance
        spacer = QWidget()
        spacer.setFixedWidth(60)
        layout.addWidget(spacer)