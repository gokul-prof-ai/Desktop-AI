"""
DesktopAI v2.0 — Chat View (App Shell UI)
File: src/gui/views/chat_view.py

Workbench layout:
  - Chat history card (grows)
  - Composer bar pinned at bottom
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QLineEdit, QPushButton, QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt

_PAD = 24


class ChatView(QWidget):
    """AI chat assistant screen."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(_PAD, _PAD, _PAD, _PAD)
        root.setSpacing(12)

        # Sub-header
        sub = QLabel("Ask DesktopAI anything about your files or organization.")
        sub.setStyleSheet("color: #A1A1A6; font-size: 13px;")
        root.addWidget(sub)

        # ── Chat history card ──────────────────────────────────────
        history_card = QFrame()
        history_card.setObjectName("Card")
        history_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        card_layout = QVBoxLayout(history_card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(0)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFrameShape(QFrame.NoFrame)
        self.chat_area.setStyleSheet(
            "background: transparent; color: #F5F5F7; font-size: 13px; border: none;"
        )
        self.chat_area.setHtml(self._welcome_html())
        card_layout.addWidget(self.chat_area)

        root.addWidget(history_card, 1)

        # ── Composer bar ───────────────────────────────────────────
        composer = QFrame()
        composer.setObjectName("Card")
        composer.setFixedHeight(52)

        bar = QHBoxLayout(composer)
        bar.setContentsMargins(12, 0, 12, 0)
        bar.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Message DesktopAI...")
        self.input_field.setStyleSheet(
            "background: transparent; border: none; "
            "color: #F5F5F7; font-size: 13px;"
        )
        self.input_field.returnPressed.connect(self._send_message)
        bar.addWidget(self.input_field, 1)

        send_btn = QPushButton("Send")
        send_btn.setObjectName("PrimaryButton")
        send_btn.setFixedWidth(64)
        send_btn.clicked.connect(self._send_message)
        bar.addWidget(send_btn)

        root.addWidget(composer)

    def _welcome_html(self) -> str:
        return """
        <div style='font-family: -apple-system, Segoe UI, sans-serif; padding: 8px;'>
            <p style='color: #0A84FF; font-weight: 600; margin: 0 0 6px 0;
                      font-size: 13px;'>DesktopAI</p>
            <p style='color: #A1A1A6; margin: 0; font-size: 13px; line-height: 1.6;'>
                Hello! I can help you organize files, find documents,
                or explain your folder structure. What would you like to do?
            </p>
        </div>
        """

    def _send_message(self) -> None:
        text = self.input_field.text().strip()
        if not text:
            return

        # Append user message
        self.chat_area.append(
            f"<div style='margin: 12px 0 4px 0;'>"
            f"<p style='color: #F5F5F7; font-weight: 600; margin: 0 0 4px 0; font-size: 13px;'>You</p>"
            f"<p style='color: #F5F5F7; margin: 0; font-size: 13px;'>{text}</p>"
            f"</div>"
        )

        self.input_field.clear()

        # Placeholder AI response
        self.chat_area.append(
            "<div style='margin: 4px 0 12px 0;'>"
            "<p style='color: #0A84FF; font-weight: 600; margin: 0 0 4px 0; font-size: 13px;'>DesktopAI</p>"
            "<p style='color: #A1A1A6; margin: 0; font-size: 13px;'>"
            "AI chat is connected and ready. Full response streaming arrives in Phase 3."
            "</p></div>"
        )