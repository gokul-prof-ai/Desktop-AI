"""
DesktopAI v2.0 — Settings View
File: src/gui/views/settings_view.py
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # AI Section
        section = QFrame()
        section.setStyleSheet("background-color: #0A0A0F; border: 1px solid #2A2A35; border-radius: 12px;")
        sec_layout = QVBoxLayout(section)
        sec_layout.setContentsMargins(24, 24, 24, 24)
        
        sec_title = QLabel("AI Configuration")
        sec_title.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        sec_title.setStyleSheet("color: #FFFFFF;")
        sec_layout.addWidget(sec_title)
        
        check1 = QCheckBox("Use Mock AI for development (No Ollama required)")
        check1.setStyleSheet("color: #A1A1AA; font-size: 14px; spacing: 8px;")
        sec_layout.addWidget(check1)
        
        check2 = QCheckBox("Enable automatic file scanning on folder changes")
        check2.setStyleSheet("color: #A1A1AA; font-size: 14px; spacing: 8px;")
        sec_layout.addWidget(check2)
        
        layout.addWidget(section)
        layout.addStretch()