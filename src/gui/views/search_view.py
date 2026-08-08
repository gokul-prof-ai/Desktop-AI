"""
DesktopAI v2.0 — Search View
File: src/gui/views/search_view.py
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class SearchView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        title = QLabel("Semantic Search")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        subtitle = QLabel("Find files using natural language. The AI understands context, not just keywords.")
        subtitle.setStyleSheet("color: #A1A1AA; font-size: 14px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Search Bar
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("🔍  e.g., 'invoices from last March' or 'python scripts about databases'")
        search_bar.setFixedHeight(56)
        search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #0A0A0F;
                border: 1px solid #2A2A35;
                border-radius: 12px;
                color: #FFFFFF;
                font-size: 16px;
                padding: 0 20px;
            }
            QLineEdit:focus {
                border: 1px solid #8B5CF6;
                background-color: #101018;
            }
        """)
        layout.addWidget(search_bar)
        
        # Results Placeholder
        placeholder = QFrame()
        placeholder.setStyleSheet("""
            QFrame {
                background-color: #0A0A0F;
                border: 1px dashed #2A2A35;
                border-radius: 12px;
            }
        """)
        ph_layout = QVBoxLayout(placeholder)
        ph_layout.setAlignment(Qt.AlignCenter)
        
        ph_text = QLabel("Search results will appear here")
        ph_text.setStyleSheet("color: #52525B; font-size: 14px;")
        ph_layout.addWidget(ph_text)
        
        layout.addWidget(placeholder, 1)