"""
DesktopAI v2.0 — Chat View
File: src/gui/views/chat_view.py

Conversational UI wired to ChatWorkflow on a background thread.
"""
from __future__ import annotations
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from core.logger import get_logger

logger = get_logger(__name__)

try:
    from gui.utils.sounds import SOUNDS
except Exception:  # sounds module optional
    class _NullSounds:
        def play_click(self): pass
        def play_success(self): pass
    SOUNDS = _NullSounds()


class _ChatWorker(QThread):
    """Runs ChatWorkflow off the UI thread."""
    finished_reply = Signal(str)

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self._message = message

    def run(self):
        from app.workflows.chat_workflow import ChatWorkflow
        self.finished_reply.emit(ChatWorkflow().ask(self._message))


class ChatView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        self._worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("AI Assistant")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)

        subtitle = QLabel("Ask me about your files — I'm wired into your scanner, organizer, and history.")
        subtitle.setStyleSheet("color: #A1A1AA; font-size: 14px;")
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_scroll.setStyleSheet("""
            QScrollArea { background-color: #0A0A0F; border: 1px solid #1A1A24; border-radius: 12px; }
        """)
        self.chat_content = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_layout.setSpacing(12)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_scroll.setWidget(self.chat_content)
        layout.addWidget(self.chat_scroll, 1)

        self._add_message(
            "Hello! I'm your DesktopAI agent. Try 'hi', 'what are these files?', "
            "or ask anything about organizing your documents.",
            is_user=False,
        )

        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Message DesktopAI...")
        self.chat_input.setFixedHeight(48)
        self.chat_input.setStyleSheet("""
            QLineEdit { background-color: #0A0A0F; border: 1px solid #2A2A35; border-radius: 8px;
                        color: #FFFFFF; padding: 0 16px; font-size: 14px; }
            QLineEdit:focus { border: 1px solid #8B5CF6; }
        """)
        self.chat_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.chat_input, 1)

        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedSize(80, 48)
        self.send_btn.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8B5CF6, stop:1 #3B82F6);
                          color: white; border: none; border-radius: 8px; font-weight: 600; }
            QPushButton:hover { opacity: 0.9; }
            QPushButton:disabled { background: #2A2A35; color: #71717A; }
        """)
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

    # ── Messages ──────────────────────────────────────────────────
    def _add_message(self, text: str, is_user: bool):
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if is_user:
            bubble.setStyleSheet("""
                QLabel { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8B5CF6, stop:1 #3B82F6);
                         color: white; padding: 12px 16px; border-radius: 12px; }
            """)
            row.addStretch()
            row.addWidget(bubble)
        else:
            bubble.setStyleSheet("""
                QLabel { background-color: #1A1A24; color: #E4E4E7; padding: 12px 16px; border-radius: 12px; }
            """)
            row.addWidget(bubble)
            row.addStretch()
        wrap = QWidget()
        wrap.setLayout(row)
        self.chat_layout.addWidget(wrap)
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())

    def _send_message(self):
        text = self.chat_input.text().strip()
        if not text or (self._worker and self._worker.isRunning()):
            return
        SOUNDS.play_click()
        self._add_message(text, is_user=True)
        self.chat_input.clear()
        self.send_btn.setEnabled(False)
        self._add_message("…", is_user=False)  # thinking placeholder
        self._worker = _ChatWorker(text)
        self._worker.finished_reply.connect(self._on_reply)
        self._worker.start()

    def _on_reply(self, reply: str):
        # Remove the thinking placeholder (last widget)
        item = self.chat_layout.takeAt(self.chat_layout.count() - 1)
        if item and item.widget():
            item.widget().deleteLater()
        self._add_message(reply, is_user=False)
        self.send_btn.setEnabled(True)
        SOUNDS.play_success()