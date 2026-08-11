"""
DesktopAI v2.0 — Chat View (styled bubbles, real Ollama backend)
File: src/gui/views/chat_view.py
"""
from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QScrollArea, QFrame, QPushButton,
    QSizePolicy,
)

from core.logger import get_logger

logger = get_logger(__name__)

_SUGGESTIONS = [
    "What files did I scan?",
    "How many categories were found?",
    "Which are the largest files?",
    "Help me organize my downloads",
]


class _ChatWorker(QThread):
    finished_reply = Signal(str)

    def __init__(self, message: str, scan_context: tuple | None = None, parent=None):
        super().__init__(parent)
        self._message = message
        self._scan_context = scan_context

    def run(self) -> None:
        from app.workflows.chat_workflow import ChatWorkflow
        workflow = ChatWorkflow()

        if self._scan_context is not None:
            scan_path, scan_results = self._scan_context
            for fn_name in ("set_scan_context", "set_context"):
                fn = getattr(workflow, fn_name, None)
                if callable(fn):
                    try:
                        fn(scan_path, scan_results)
                    except Exception as exc:
                        logger.warning("ChatWorkflow context error: %s", exc)
                    break

        try:
            reply = workflow.ask(self._message)
        except Exception as exc:
            logger.error("ChatWorkflow.ask failed: %s", exc)
            reply = "Sorry — something went wrong. Please try again."

        self.finished_reply.emit(reply)


class ChatView(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self._worker: _ChatWorker | None = None
        self._scan_path: Path | None = None
        self._scan_results: list = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Sub-header
        sub = QLabel(
            "Ask me about your files — I'm connected to your scanner, organizer, and history."
        )
        sub.setObjectName("Muted")
        layout.addWidget(sub)

        # Chat scroll area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setObjectName("ChatScroll")
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(16, 16, 16, 16)
        self.chat_layout.setSpacing(10)
        self.chat_layout.setAlignment(Qt.AlignTop)

        self.chat_scroll.setWidget(self.chat_content)
        layout.addWidget(self.chat_scroll, 1)

        # Welcome message
        self._add_bot(
            "Hello! I'm DesktopAI. Scan a folder on Home, then ask me anything "
            "about your files, categories, or organization."
        )

        # Suggested prompts
        suggestions_row = QHBoxLayout()
        suggestions_row.setSpacing(6)
        for prompt in _SUGGESTIONS:
            btn = QPushButton(prompt)
            btn.setObjectName("SecondaryButton")
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda _, p=prompt: self._use_suggestion(p))
            suggestions_row.addWidget(btn)
        suggestions_row.addStretch()
        layout.addLayout(suggestions_row)

        # Composer
        composer = QFrame()
        composer.setObjectName("Card")
        composer.setFixedHeight(52)
        c_layout = QHBoxLayout(composer)
        c_layout.setContentsMargins(14, 0, 12, 0)
        c_layout.setSpacing(8)

        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("Input")
        self.chat_input.setPlaceholderText("Message DesktopAI…")
        self.chat_input.setStyleSheet(
            "border: none; background: transparent; font-size: 13px;"
        )
        self.chat_input.returnPressed.connect(self._send)
        c_layout.addWidget(self.chat_input, 1)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("PrimaryButton")
        self.send_btn.setFixedWidth(72)
        self.send_btn.clicked.connect(self._send)
        c_layout.addWidget(self.send_btn)

        layout.addWidget(composer)

    # ── Scan context ───────────────────────────────────────────────

    def set_scan_context(self, scan_path, results) -> None:
        self._scan_path = Path(scan_path) if scan_path else None
        self._scan_results = list(results or [])
        total = len(self._scan_results)
        if total == 0:
            return

        cats: dict[str, int] = {}
        for item in self._scan_results:
            if getattr(item, "skipped", False):
                continue
            cat = getattr(item, "category", None) or "Miscellaneous"
            cats[cat] = cats.get(cat, 0) + 1

        folder = self._scan_path.name if self._scan_path else "folder"
        top = sorted(cats.items(), key=lambda kv: -kv[1])[:3]
        top_str = ", ".join(f"{n} ({c})" for n, c in top)
        self._add_bot(
            f"Scan of '{folder}' complete — {total} files analyzed. "
            f"Top categories: {top_str}. Ask me anything about these files."
        )

    def get_scan_context(self) -> tuple:
        return self._scan_path, self._scan_results

    # ── Messaging ──────────────────────────────────────────────────

    def _add_bot(self, text: str) -> None:
        """Add a bot message bubble (left-aligned)."""
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        # Avatar dot
        avatar = QLabel("◎")
        avatar.setFixedWidth(20)
        avatar.setAlignment(Qt.AlignTop)
        avatar.setStyleSheet("color: #0A84FF; font-size: 14px; padding-top: 2px;")
        row.addWidget(avatar)

        bubble = QLabel(text)
        bubble.setObjectName("BotBubble")
        bubble.setWordWrap(True)
        bubble.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        row.addWidget(bubble, 1)
        row.addStretch()

        self._add_row(row)

    def _add_user(self, text: str) -> None:
        """Add a user message bubble (right-aligned)."""
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch()

        bubble = QLabel(text)
        bubble.setObjectName("UserBubble")
        bubble.setWordWrap(True)
        bubble.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        row.addWidget(bubble)

        self._add_row(row)

    def _add_row(self, row_layout: QHBoxLayout) -> None:
        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        wrap.setLayout(row_layout)
        self.chat_layout.addWidget(wrap)
        # Scroll to bottom
        sb = self.chat_scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _add_thinking(self) -> None:
        """Add a temporary 'thinking' indicator."""
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        avatar = QLabel("◎")
        avatar.setFixedWidth(20)
        avatar.setAlignment(Qt.AlignTop)
        avatar.setStyleSheet("color: #0A84FF; font-size: 14px; padding-top: 2px;")
        row.addWidget(avatar)

        thinking = QLabel("Thinking…")
        thinking.setObjectName("BotBubble")
        thinking.setStyleSheet(
            "color: #6C6C70; font-style: italic; "
            "background: transparent; border: none; padding: 4px 0;"
        )
        row.addWidget(thinking)
        row.addStretch()

        self._add_row(row)

    # ── Send ───────────────────────────────────────────────────────

    def _use_suggestion(self, prompt: str) -> None:
        self.chat_input.setText(prompt)
        self._send()

    def _send(self) -> None:
        text = self.chat_input.text().strip()
        if not text or (self._worker and self._worker.isRunning()):
            return

        self._add_user(text)
        self.chat_input.clear()
        self.send_btn.setEnabled(False)
        self._add_thinking()

        scan_path, scan_results = self.get_scan_context()
        ctx = (scan_path, scan_results) if scan_results else None

        self._worker = _ChatWorker(text, scan_context=ctx)
        self._worker.finished_reply.connect(self._on_reply)
        self._worker.start()

    def _on_reply(self, reply: str) -> None:
        # Remove the thinking indicator (last widget)
        count = self.chat_layout.count()
        if count > 0:
            item = self.chat_layout.takeAt(count - 1)
            if item and item.widget():
                item.widget().deleteLater()

        self._add_bot(reply)
        self.send_btn.setEnabled(True)