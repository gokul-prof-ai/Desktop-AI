"""
DesktopAI v2.0 — Chat View
File: src/gui/views/chat_view.py
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class ChatView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        
        title = QLabel("AI Assistant")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # Chat Area
        chat_area = QTextEdit()
        chat_area.setReadOnly(True)
        chat_area.setHtml("""
            <div style='color: #A1A1AA; font-size: 14px;'>
                <p style='color: #8B5CF6; font-weight: 600;'>DesktopAI</p>
                <p>Hello! I can help you organize files, find documents, or explain your folder structure. What would you like to do?</p>
            </div>
        """)
        chat_area.setStyleSheet("""
            QTextEdit {
                background-color: #0A0A0F;
                border: 1px solid #2A2A35;
                border-radius: 12px;
                color: #FFFFFF;
                padding: 16px;
            }
        """)
        layout.addWidget(chat_area, 1)
        
        # Input Area
        input_layout = QHBoxLayout()
        input_field = QLineEdit()
        input_field.setPlaceholderText("Message DesktopAI...")
        input_field.setFixedHeight(48)
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: #0A0A0F;
                border: 1px solid #2A2A35;
                border-radius: 8px;
                color: #FFFFFF;
                padding: 0 16px;
                font-size: 14px;
            }
        """)
        input_layout.addWidget(input_field, 1)
        
        send_btn = QPushButton("Send")
        send_btn.setFixedSize(80, 48)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                color: white; border: none; border-radius: 8px; font-weight: 600;
            }
        """)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)