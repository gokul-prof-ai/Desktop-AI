"""
DesktopAI v2.0 — Chat View
File: src/gui/views/chat_view.py
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
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
        
        subtitle = QLabel("Ask me anything about your files")
        subtitle.setStyleSheet("color: #A1A1AA; font-size: 14px;")
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_scroll.setStyleSheet("QScrollArea { background-color: #0A0A0F; border: 1px solid #1A1A24; border-radius: 12px; }")
        
        self.chat_content = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_layout.setSpacing(16)
        self.chat_layout.setAlignment(Qt.AlignTop)
        
        self._add_message("Hello! I'm your DesktopAI assistant. I can help you find files, organize your documents, or answer questions about your data. What would you like to do?", is_user=False)
        
        self.chat_scroll.setWidget(self.chat_content)
        layout.addWidget(self.chat_scroll, 1)
        
        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Message DesktopAI...")
        self.chat_input.setFixedHeight(48)
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #0A0A0F; border: 1px solid #2A2A35;
                border-radius: 8px; color: #FFFFFF; padding: 0 16px; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #8B5CF6; }
        """)
        self.chat_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.chat_input, 1)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedSize(80, 48)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8B5CF6, stop:1 #3B82F6);
                color: white; border: none; border-radius: 8px; font-weight: 600;
            }
            QPushButton:hover { opacity: 0.9; }
        """)
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)
    
    def _add_message(self, text: str, is_user: bool):
        msg_widget = QWidget()
        msg_layout = QHBoxLayout(msg_widget)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        
        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        if is_user:
            msg_label.setStyleSheet("QLabel { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8B5CF6, stop:1 #3B82F6); color: white; padding: 12px 16px; border-radius: 12px; }")
            msg_layout.addStretch()
            msg_layout.addWidget(msg_label)
        else:
            msg_label.setStyleSheet("QLabel { background-color: #1A1A24; color: #E4E4E7; padding: 12px 16px; border-radius: 12px; }")
            msg_layout.addWidget(msg_label)
            msg_layout.addStretch()
        
        self.chat_layout.addWidget(msg_widget)
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())
    
    def _send_message(self):
        text = self.chat_input.text().strip()
        if not text: return
        
        self._add_message(text, is_user=True)
        self.chat_input.clear()
        
        response = "I can help you with:\n• Finding files by content or name\n• Organizing files into folders\n• Summarizing documents\n\nWhat would you like to do?"
        QTimer.singleShot(500, lambda: self._add_message(response, is_user=False))