"""
DesktopAI v2.0 — Organize View
File: src/gui/views/organize_view.py
"""
from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QPushButton, QHBoxLayout, QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class OrganizeView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        title = QLabel("Organize Files")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        subtitle = QLabel("Review AI suggestions and apply organization plans.")
        subtitle.setStyleSheet("color: #A1A1AA; font-size: 14px;")
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(139, 92, 246, 0.1), stop:1 rgba(59, 130, 246, 0.05));
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: 16px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        
        card_title = QLabel("Ready to Organize")
        card_title.setFont(QFont("Segoe UI", 20, QFont.Weight.DemiBold))
        card_title.setStyleSheet("color: #FFFFFF;")
        card_layout.addWidget(card_title)
        
        card_text = QLabel("Select a folder to scan, review the AI's categorization plan, and apply changes with one click.")
        card_text.setWordWrap(True)
        card_text.setStyleSheet("color: #A1A1AA; font-size: 14px;")
        card_layout.addWidget(card_text)
        
        btn = QPushButton("Start New Organization")
        btn.setFixedSize(220, 48)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8B5CF6, stop:1 #3B82F6);
                color: white; border: none; border-radius: 8px; font-weight: 600; font-size: 14px;
            }
            QPushButton:hover { opacity: 0.9; }
        """)
        card_layout.addWidget(btn, alignment=Qt.AlignLeft)
        layout.addWidget(card)
        layout.addStretch()