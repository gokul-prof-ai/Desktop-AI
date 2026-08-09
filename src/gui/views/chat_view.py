"""
DesktopAI v2.0 — Chat View (theme-aware, Ollama-backed)
File: src/gui/views/chat_view.py
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QScrollArea,
)

from gui.components.sound_button import SoundButton
from core.logger import get_logger

logger = get_logger(__name__)


class _ChatWorker(QThread):
    finished_reply = Signal(str)

    def __init__(
        self,
        message: str,
        scan_context: tuple | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._message = message
        # (scan_path: Path | None, results: list) — forwarded to ChatWorkflow.
        self._scan_context = scan_context

    def run(self):
        from app.workflows.chat_workflow import ChatWorkflow

        workflow = ChatWorkflow()

        # Forward scan context if the workflow supports it (duck-typed,
        # so this never breaks if ChatWorkflow has no such method).
        if self._scan_context is not None:
            scan_path, scan_results = self._scan_context
            for fn_name in ("set_scan_context", "set_context"):
                fn = getattr(workflow, fn_name, None)
                if callable(fn):
                    try:
                        fn(scan_path, scan_results)
                    except Exception as exc:
                        logger.warning("ChatWorkflow rejected scan context: %s", exc)
                    break

        try:
            reply = workflow.ask(self._message)
        except Exception as exc:
            logger.error("ChatWorkflow.ask failed: %s", exc)
            reply = "Sorry — something went wrong while processing that request."

        self.finished_reply.emit(reply)


class ChatView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent;")
        self._worker = None

        # Latest scan context (set by MainWindow after every scan).
        self._scan_path: Path | None = None
        self._scan_results: list = []

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

    # ── Scan context (called by MainWindow._on_scan_ready) ──────────────

    def set_scan_context(self, scan_path, results) -> None:
        """
        Store the latest scan results so the chat agent can answer
        questions about them ("how many finance files did I scan?").

        Called by MainWindow after every completed scan.

        Args:
            scan_path: The folder that was scanned (str or Path).
            results:   Scan results — list of dicts from
                       FileService.scan_folder() or AnalysisResult objects.
        """
        self._scan_path = Path(scan_path) if scan_path else None
        self._scan_results = list(results or [])

        total = len(self._scan_results)
        if total == 0:
            logger.info("ChatView.set_scan_context: empty scan, nothing stored.")
            return

        def _field(item, key, default=None):
            """Read a field from a dict or an object uniformly."""
            if isinstance(item, dict):
                return item.get(key, default)
            return getattr(item, key, default)

        categories: dict[str, int] = {}
        for item in self._scan_results:
            if _field(item, "skipped", False):
                continue
            cat = _field(item, "category", None) or "Miscellaneous"
            categories[cat] = categories.get(cat, 0) + 1

        folder_name = self._scan_path.name if self._scan_path else "folder"
        top = sorted(categories.items(), key=lambda kv: kv[1], reverse=True)[:3]
        top_str = ", ".join(f"{name} ({count})" for name, count in top)

        self._add_message(
            f"Scan of '{folder_name}' complete — {total} files analyzed. "
            f"Top categories: {top_str}. Ask me anything about these files.",
            False,
        )
        logger.info(
            "ChatView.set_scan_context: stored %d results from %s",
            total, self._scan_path,
        )

    def get_scan_context(self) -> tuple:
        """
        Return (scan_path, results) for the chat workflow.
        Safe to call before any scan has happened.
        """
        return (self._scan_path, self._scan_results)

    # ── Messaging ────────────────────────────────────────────────────────

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

        # Attach scan context only when a scan has actually happened.
        scan_path, scan_results = self.get_scan_context()
        ctx = (scan_path, scan_results) if scan_results else None

        self._worker = _ChatWorker(text, scan_context=ctx)
        self._worker.finished_reply.connect(self._on_reply)
        self._worker.start()

    def _on_reply(self, reply: str):
        item = self.chat_layout.takeAt(self.chat_layout.count() - 1)
        if item and item.widget():
            item.widget().deleteLater()
        self._add_message(reply, False)
        self.send_btn.setEnabled(True)