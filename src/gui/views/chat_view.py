"""
DesktopAI v2.0 — Chat View
File: src/gui/views/chat_view.py

Real streaming chat backed by ChatWorkflow (Ollama or MockProvider).
The _ChatWorker streams tokens via a Signal so the bubble updates
word-by-word instead of appearing all at once.
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


# ── Background worker ──────────────────────────────────────────────────────

class _ChatWorker(QThread):
    """
    Runs ChatWorkflow.ask() on a background thread.

    Emits token_received for each streamed chunk and finished_reply
    with the complete text when done.
    """
    token_received = Signal(str)   # incremental text chunk
    finished_reply = Signal(str)   # full reply when done

    def __init__(
        self,
        message: str,
        scan_path: str | None = None,
        scan_results: list | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._message      = message
        self._scan_path    = scan_path
        self._scan_results = scan_results or []

    def run(self) -> None:
        try:
            from app.workflows.chat_workflow import ChatWorkflow
            workflow = ChatWorkflow()

            # Inject scan context if the workflow supports it
            for method_name in ("set_scan_context", "set_context"):
                fn = getattr(workflow, method_name, None)
                if callable(fn) and self._scan_path:
                    try:
                        fn(self._scan_path, self._scan_results)
                    except Exception as exc:
                        logger.debug("ChatWorkflow context setter failed: %s", exc)
                    break

            # Try streaming first
            streamed = self._try_stream(workflow)
            if not streamed:
                # Fallback: blocking ask()
                reply = workflow.ask(self._message)
                self.token_received.emit(reply)
                self.finished_reply.emit(reply)

        except Exception as exc:
            logger.error("ChatWorker.run failed: %s", exc)
            fallback = "Sorry — something went wrong. Please try again."
            self.token_received.emit(fallback)
            self.finished_reply.emit(fallback)

    def _try_stream(self, workflow) -> bool:
        """
        Attempt to use ChatWorkflow.stream() if it exists.
        Returns True if streaming succeeded, False to trigger fallback.
        """
        stream_fn = getattr(workflow, "stream", None)
        if not callable(stream_fn):
            return False

        try:
            full = ""
            for chunk in stream_fn(self._message):
                if chunk:
                    self.token_received.emit(chunk)
                    full += chunk
            if full:
                self.finished_reply.emit(full)
                return True
            return False
        except Exception as exc:
            logger.debug("Streaming failed, falling back to blocking ask: %s", exc)
            return False


# ── ChatView ───────────────────────────────────────────────────────────────

class ChatView(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self._worker        : _ChatWorker | None = None
        self._scan_path     : str | None = None
        self._scan_results  : list = []
        self._streaming_lbl : QLabel | None = None   # bubble being built
        self._build_ui()

    # ── Build UI ───────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        sub = QLabel(
            "Ask me about your files — I'm connected to your scanner, organizer, and history."
        )
        sub.setObjectName("Muted")
        layout.addWidget(sub)

        # ── Chat scroll area ───────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setObjectName("ChatScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._chat_layout = QVBoxLayout(self._content)
        self._chat_layout.setContentsMargins(16, 16, 16, 16)
        self._chat_layout.setSpacing(10)
        self._chat_layout.setAlignment(Qt.AlignTop)
        self._scroll.setWidget(self._content)
        layout.addWidget(self._scroll, 1)

        self._add_bot(
            "Hello! I'm DesktopAI. Scan a folder on Home, then ask me anything "
            "about your files, categories, or organization."
        )

        # ── Suggestion chips ───────────────────────────────────────
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

        # ── Composer ───────────────────────────────────────────────
        composer = QFrame()
        composer.setObjectName("Card")
        composer.setFixedHeight(52)
        c_layout = QHBoxLayout(composer)
        c_layout.setContentsMargins(14, 0, 12, 0)
        c_layout.setSpacing(8)

        self._input = QLineEdit()
        self._input.setObjectName("Input")
        self._input.setPlaceholderText("Message DesktopAI…")
        self._input.setStyleSheet(
            "border: none; background: transparent; font-size: 13px;"
        )
        self._input.returnPressed.connect(self._send)
        c_layout.addWidget(self._input, 1)

        self._send_btn = QPushButton("Send")
        self._send_btn.setObjectName("PrimaryButton")
        self._send_btn.setFixedWidth(72)
        self._send_btn.clicked.connect(self._send)
        c_layout.addWidget(self._send_btn)

        layout.addWidget(composer)

    # ── Scan context ───────────────────────────────────────────────

    def set_scan_context(self, scan_path: str, results: list) -> None:
        self._scan_path    = str(scan_path) if scan_path else None
        self._scan_results = list(results or [])
        total = len(self._scan_results)
        if not total:
            return

        # Count categories (results may be dicts or AnalysisResult objects)
        cats: dict[str, int] = {}
        for item in self._scan_results:
            if isinstance(item, dict):
                if item.get("skipped"):
                    continue
                cat = item.get("category") or "Miscellaneous"
            else:
                if getattr(item, "skipped", False):
                    continue
                cat = getattr(item, "category", None) or "Miscellaneous"
            cats[cat] = cats.get(cat, 0) + 1

        folder = Path(self._scan_path).name if self._scan_path else "folder"
        top    = sorted(cats.items(), key=lambda kv: -kv[1])[:3]
        top_str = ", ".join(f"{n} ({c})" for n, c in top)
        self._add_bot(
            f"Scan of '{folder}' complete — {total} files analyzed. "
            f"Top categories: {top_str}. Ask me anything about these files."
        )

    # ── Bubble helpers ─────────────────────────────────────────────

    def _add_bot(self, text: str) -> QLabel:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

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
        return bubble

    def _add_user(self, text: str) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch()
        bubble = QLabel(text)
        bubble.setObjectName("UserBubble")
        bubble.setWordWrap(True)
        bubble.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        row.addWidget(bubble)
        self._add_row(row)

    def _add_thinking(self) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        avatar = QLabel("◎")
        avatar.setFixedWidth(20)
        avatar.setAlignment(Qt.AlignTop)
        avatar.setStyleSheet("color: #0A84FF; font-size: 14px; padding-top: 2px;")
        row.addWidget(avatar)
        lbl = QLabel("Thinking…")
        lbl.setObjectName("BotBubble")
        lbl.setStyleSheet(
            "color: #6C6C70; font-style: italic; "
            "background: transparent; border: none; padding: 4px 0;"
        )
        row.addWidget(lbl)
        row.addStretch()
        self._add_row(row)

    def _add_row(self, row_layout: QHBoxLayout) -> None:
        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        wrap.setLayout(row_layout)
        self._chat_layout.addWidget(wrap)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _remove_last_widget(self) -> None:
        """Remove the last bubble (thinking indicator)."""
        count = self._chat_layout.count()
        if count > 0:
            item = self._chat_layout.takeAt(count - 1)
            if item and item.widget():
                item.widget().deleteLater()

    # ── Send / receive ─────────────────────────────────────────────

    def _use_suggestion(self, prompt: str) -> None:
        self._input.setText(prompt)
        self._send()

    def _send(self) -> None:
        text = self._input.text().strip()
        if not text or (self._worker and self._worker.isRunning()):
            return

        self._add_user(text)
        self._input.clear()
        self._send_btn.setEnabled(False)
        self._add_thinking()

        self._worker = _ChatWorker(
            message      = text,
            scan_path    = self._scan_path,
            scan_results = self._scan_results,
        )
        self._worker.token_received.connect(self._on_token)
        self._worker.finished_reply.connect(self._on_done)
        self._streaming_lbl = None
        self._worker.start()

    def _on_token(self, chunk: str) -> None:
        """
        First token: remove 'Thinking…' and create a real bubble.
        Subsequent tokens: append to the existing bubble.
        """
        if self._streaming_lbl is None:
            self._remove_last_widget()
            self._streaming_lbl = self._add_bot(chunk)
        else:
            current = self._streaming_lbl.text()
            self._streaming_lbl.setText(current + chunk)
            self._scroll_to_bottom()

    def _on_done(self, _full_reply: str) -> None:
        """Called when the worker finishes. Re-enable send."""
        if self._streaming_lbl is None:
            # token_received was never emitted (shouldn't happen, but be safe)
            self._remove_last_widget()
            self._add_bot(_full_reply)
        self._streaming_lbl = None
        self._send_btn.setEnabled(True)