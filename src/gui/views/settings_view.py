"""
DesktopAI v2.0 — Settings View
File: src/gui/views/settings_view.py
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, 
    QCheckBox, QComboBox, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        # Header
        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        subtitle = QLabel("Configure DesktopAI to your preferences")
        subtitle.setStyleSheet("color: #A1A1AA; font-size: 14px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # AI Configuration Section
        ai_group = self._create_section("AI Configuration")
        ai_layout = ai_group.layout()  # FIX: Get existing layout, don't create a new one
        
        model_layout = QHBoxLayout()
        model_label = QLabel("AI Model:")
        model_label.setStyleSheet("color: #A1A1AA;")
        model_layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["llama3.2", "llama3.2:1b", "mistral", "codellama"])
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #0A0A0F; border: 1px solid #2A2A35;
                border-radius: 8px; color: #FFFFFF; padding: 8px 12px; min-width: 200px;
            }
        """)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        ai_layout.addLayout(model_layout)
        layout.addWidget(ai_group)
        
        # Scanner Configuration
        scanner_group = self._create_section("Scanner")
        scanner_layout = scanner_group.layout()  # FIX: Get existing layout
        
        self.skip_hidden_check = QCheckBox("Skip hidden files and folders")
        self.skip_hidden_check.setChecked(True)
        self.skip_hidden_check.setStyleSheet("color: #E4E4E7; spacing: 8px;")
        scanner_layout.addWidget(self.skip_hidden_check)
        
        self.skip_system_check = QCheckBox("Skip system files")
        self.skip_system_check.setChecked(True)
        self.skip_system_check.setStyleSheet("color: #E4E4E7; spacing: 8px;")
        scanner_layout.addWidget(self.skip_system_check)
        layout.addWidget(scanner_group)
        
        # Appearance
        appearance_group = self._create_section("Appearance")
        appearance_layout = appearance_group.layout()  # FIX: Get existing layout
        
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet("color: #A1A1AA;")
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])
        self.theme_combo.setCurrentText("Dark")
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background-color: #0A0A0F; border: 1px solid #2A2A35;
                border-radius: 8px; color: #FFFFFF; padding: 8px 12px; min-width: 150px;
            }
        """)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        appearance_layout.addLayout(theme_layout)
        layout.addWidget(appearance_group)
        
        # Actions
        layout.addStretch()
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setFixedSize(160, 44)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #F87171;
                border: 1px solid #F87171; border-radius: 8px; font-weight: 600;
            }
            QPushButton:hover { background-color: rgba(248, 113, 113, 0.1); }
        """)
        actions_layout.addWidget(reset_btn)
        
        save_btn = QPushButton("Save Settings")
        save_btn.setFixedSize(160, 44)
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8B5CF6, stop:1 #3B82F6);
                color: white; border: none; border-radius: 8px; font-weight: 600;
            }
            QPushButton:hover { opacity: 0.9; }
        """)
        actions_layout.addWidget(save_btn)
        layout.addLayout(actions_layout)
    
    def _create_section(self, title: str) -> QFrame:
        """Create a settings section group with its layout."""
        group = QFrame()
        group.setStyleSheet("""
            QFrame {
                background-color: #0A0A0F;
                border: 1px solid #1A1A24;
                border-radius: 12px;
            }
        """)
        
        # Create layout ONCE here
        layout = QVBoxLayout(group)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        title_label.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title_label)
        
        return group