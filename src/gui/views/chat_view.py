"""
DesktopAI v2.0 — Chat View (theme-aware, Ollama-backed)
File: src/gui/views/chat_view.py
"""
from __future__ import annotations
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QScrollArea,
)
from gui.components.sound_button import SoundButton
from core.logger import get_logger

logger = get_logger(__name__)


class _ChatWorker(QThread):
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
        self.setStyleSheet("background: transparent;")
        self._worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        subtitle = QLabel("Ask me about your files — I'm wired into your scanner, organizer, and history.")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(subtitle)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setObjectName("ChatScroll")
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_layout.setSpacing(12)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_scroll.setWidget(self.chat_content)
        layout.addWidget(self.chat_scroll, 1)

        self._add_message(
            "Hello! I'm your DesktopAI agent. Try 'hi', 'what are these files?', "
            "or ask anything about organizing your documents.", False)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)
        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("Input")
        self.chat_input.setPlaceholderText("Message DesktopAI...")
        self.chat_input.setFixedHeight(48)
        self.chat_input.returnPressed.connect(self._send)
        input_layout.addWidget(self.chat_input, 1)

        self.send_btn = SoundButton("Send")
        self.send_btn.setObjectName("PrimaryButton")
        self.send_btn.setFixedSize(80, 48)
        self.send_btn.clicked.connect(self._send)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

    def _add_message(self, text: str, is_user: bool):
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setObjectName("UserBubble" if is_user else "BotBubble")
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if is_user:
            row.addStretch()
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch()
        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        wrap.setLayout(row)
        self.chat_layout.addWidget(wrap)
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())

    def _send(self):
        text = self.chat_input.text().strip()
        if not text or (self._worker and self._worker.isRunning()):
            return
        self._add_message(text, True)
        self.chat_input.clear()
        self.send_btn.setEnabled(False)
        self._add_message("…", False)
        self._worker = _ChatWorker(text)
        self._worker.finished_reply.connect(self._on_reply)
        self._worker.start()

    def _on_reply(self, reply: str):
        item = self.chat_layout.takeAt(self.chat_layout.count() - 1)
        if item and item.widget():
            item.widget().deleteLater()
        self._add_message(reply, False)
        self.send_btn.setEnabled(True)