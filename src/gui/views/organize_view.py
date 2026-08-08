"""
DesktopAI v2.0 — Organize View
File: src/gui/views/organize_view.py
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

class OrganizeView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Drop Zone Placeholder
        drop_zone = QFrame()
        drop_zone.setFixedSize(400, 250)
        drop_zone.setStyleSheet("""
            QFrame {
                background-color: rgba(139, 92, 246, 0.05);
                border: 2px dashed #8B5CF6;
                border-radius: 16px;
            }
        """)
        
        zone_layout = QVBoxLayout(drop_zone)
        zone_layout.setAlignment(Qt.AlignCenter)
        
        icon = QLabel("📁")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignCenter)
        zone_layout.addWidget(icon)
        
        text = QLabel("Drag & Drop folder here")
        text.setStyleSheet("font-size: 16px; color: #A1A1AA;")
        text.setAlignment(Qt.AlignCenter)
        zone_layout.addWidget(text)
        
        layout.addWidget(drop_zone)