"""
DesktopAI v2.0 — Home View
File: src/gui/views/home_view.py
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from gui.components.trendy_drop_zone import TrendyDropZone

class HomeView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Welcome to DesktopAI")
        title.setStyleSheet("""
            font-size: 32px; 
            font-weight: 700; 
            color: #FFFFFF;
            letter-spacing: -1px;
            font-family: 'SF Pro Display', 'Inter', sans-serif;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        sub = QLabel("Organize your files intelligently with AI.")
        sub.setStyleSheet("""
            font-size: 16px; 
            color: #A1A1AA;
            font-family: 'SF Pro Display', 'Inter', sans-serif;
        """)
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)
        
        layout.addSpacing(40)
        
        # The New Trendy Drop Zone
        self.drop_zone = TrendyDropZone()
        self.drop_zone.folder_selected.connect(self._on_folder_selected)
        layout.addWidget(self.drop_zone, alignment=Qt.AlignCenter)
        
    def _on_folder_selected(self, path: str):
        print(f"HomeView: Folder/File selected -> {path}")
        # TODO: Pass this to the ViewModel/Workflow in the next milestone