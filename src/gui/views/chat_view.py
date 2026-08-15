"""
DesktopAI v2.0 — Chat View (AI Workspace)
File: src/gui/views/chat_view.py
Conversational interface over ChatWorkflow with thinking state,
suggested prompts, error retry, and scan awareness.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QScrollArea, QVBoxLayout, QWidget,
)

from core.logger import get_logger
from gui.components.brand import LogoMark
from gui.components.widgets import GhostButton, PrimaryButton, SectionHeader
from gui.theme.design_tokens import tokens_for

logger = get_logger(__name__)

_SUGGESTIONS = [
    "Find my largest files",
    "Show recent documents",
    "How should I organize this folder?",
]


class _ChatWorker(QThread):
    reply = Signal(str)
    failed = Signal(str)

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self._message = message

    def run(self):
        try:
            from app.workflows.chat_workflow import ChatWorkflow
            self.reply.emit(ChatWorkflow().ask(self._message))
        except Exception as exc:
            logger.exception("Chat failed")
            self.failed.emit(str(exc))


class ChatView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = "dark"
        self._thinking = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        layout.addWidget(SectionHeader(
            "Ask DesktopAI",
            "Ask questions about your files, folders, or organization.",
        ))

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.flow = QVBoxLayout(self.content)
        self.flow.setSpacing(12)
        self.flow.addStretch()
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll, 1)

        # Suggestions
        sug = QHBoxLayout()
        sug.setSpacing(8)
        for text in _SUGGESTIONS:
            b = GhostButton(text)
            b.clicked.connect(lambda _c, t=text: self._send_text(t))
            sug.addWidget(b)
        sug.addStretch()
        layout.addLayout(sug)

        # Input row
        row = QHBoxLayout()
        row.setSpacing(10)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask DesktopAI…")
        self.input.setFixedHeight(44)
        self.input.returnPressed.connect(lambda: self._send_text(self.input.text()))
        row.addWidget(self.input, 1)
        send = PrimaryButton("Send")
        send.setFixedWidth(90)
        send.clicked.connect(lambda: self._send_text(self.input.text()))
        row.addWidget(send)
        layout.addLayout(row)

        self._timer = QTimer(self)
        self._timer.setInterval(400)
        self._timer.timeout.connect(self._tick_thinking)
        self._dots = 0

    # ── Context from scans ────────────────────────────────────────
    def set_scan_context(self, path: str, results: list) -> None:
        if results:
            self._add_ai(f"Your latest scan analyzed {len(results)} files. Ask me about them.")

    # ── Messages ─────────────────────────────────────────────────
    def _send_text(self, text: str):
        text = (text or "").strip()
        if not text:
            return
        self.input.clear()
        self._add_user(text)
        self._start_thinking()
        self._worker = _ChatWorker(text)
        self._worker.reply.connect(self._on_reply)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_reply(self, text: str):
        self._stop_thinking()
        self._add_ai(text)

    def _on_failed(self, message: str):
        self._stop_thinking()
        self._add_ai(f"We couldn't answer that. {message}")

    def _add_user(self, text: str):
        t = tokens_for(self._theme)
        row = QHBoxLayout()
        row.addStretch()
        b = QLabel(text)
        b.setWordWrap(True)
        b.setMaximumWidth(520)
        b.setStyleSheet(
            f"background: {t['primary_soft']}; color: {t['text']}; "
            "border-radius: 10px; padding: 10px 14px;"
        )
        row.addWidget(b)
        self._insert(row)

    def _add_ai(self, text: str):
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(LogoMark(24))
        b = QLabel(text)
        b.setWordWrap(True)
        b.setObjectName("daCard")
        b.setMaximumWidth(560)
        b.setStyleSheet(b.styleSheet() + " padding: 10px 14px;")
        row.addWidget(b)
        row.addStretch()
        self._insert(row)

    def _start_thinking(self):
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(LogoMark(24))
        self._thinking = QLabel("DesktopAI is thinking")
        self._thinking.setObjectName("daProgressText")
        row.addWidget(self._thinking)
        row.addStretch()
        self._insert(row)
        self._timer.start()

    def _tick_thinking(self):
        self._dots = (self._dots + 1) % 4
        if self._thinking:
            self._thinking.setText("DesktopAI is thinking" + "." * self._dots)

    def _stop_thinking(self):
        self._timer.stop()
        if self._thinking:
            w = self._thinking
            self._thinking = None
            parent_row = w.parentWidget()
            if parent_row:
                parent_row.deleteLater()

    def _insert(self, row):
        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        wrap.setLayout(row)
        self.flow.insertWidget(self.flow.count() - 1, wrap)
        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )