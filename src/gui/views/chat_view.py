"""
DesktopAI v2.0
AI Chat workspace.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextBrowser,
    QLineEdit,
    QPushButton,
)


class ChatWorker(QThread):

    completed = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        prompt: str,
        context: str,
        parent=None,
    ):
        super().__init__(parent)

        self.prompt = prompt
        self.context = context

    def run(self):

        try:

            from infrastructure.ai.gateway import (
                AIGateway,
                GenerateRequest,
            )

            system_prompt = """
You are DesktopAI, a local-first desktop file assistant.

You help users:
- understand their files
- explain organization results
- find files
- recommend organization strategies
- answer questions about the current scanned folder

Never claim that a file operation happened unless the application
actually executed it.

Be concise, practical and accurate.
"""

            full_prompt = (
                f"{system_prompt}\n\n"
                f"Current application context:\n"
                f"{self.context}\n\n"
                f"User request:\n"
                f"{self.prompt}"
            )

            response = AIGateway.generate(
                GenerateRequest(
                    prompt=full_prompt,
                    model_hint="default",
                    temperature=0.2,
                    max_tokens=1000,
                )
            )

            self.completed.emit(
                response.text.strip()
            )

        except Exception as exc:

            self.failed.emit(
                str(exc)
            )


class ChatView(QWidget):

    def __init__(self):
        super().__init__()

        self.scan_context = (
            "No folder has been scanned yet."
        )

        self.worker = None

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(12)

        self.chat = QTextBrowser()

        self.chat.setOpenExternalLinks(
            True
        )

        self._append_message(
            "DesktopAI",
            (
                "I am ready. Ask me about your scanned files, "
                "organization plan, categories or folder structure."
            ),
        )

        layout.addWidget(
            self.chat,
            1,
        )

        composer = QHBoxLayout()

        self.input = QLineEdit()

        self.input.setPlaceholderText(
            "Ask DesktopAI..."
        )

        self.input.returnPressed.connect(
            self._send
        )

        self.send_button = QPushButton(
            "Send"
        )

        self.send_button.setObjectName(
            "PrimaryButton"
        )

        self.send_button.clicked.connect(
            self._send
        )

        composer.addWidget(
            self.input,
            1,
        )

        composer.addWidget(
            self.send_button
        )

        layout.addLayout(
            composer
        )

    # ==================================================================
    # CONTEXT
    # ==================================================================

    def set_scan_context(
        self,
        scan_path: str,
        results: list,
    ):

        categories = sorted(
            {
                result.category
                for result in results
                if result.category
            }
        )

        filenames = [
            result.file_info.filename
            for result in results[:50]
        ]

        self.scan_context = (
            f"Scanned folder: {scan_path}\n"
            f"Files analyzed: {len(results)}\n"
            f"Categories: {', '.join(categories)}\n"
            f"Sample files: {', '.join(filenames)}"
        )

    # ==================================================================
    # SEND
    # ==================================================================

    def _send(self):

        prompt = (
            self.input.text()
            .strip()
        )

        if not prompt:
            return

        self.input.clear()

        self._append_message(
            "You",
            prompt,
        )

        self._append_message(
            "DesktopAI",
            "Thinking...",
        )

        self.input.setEnabled(
            False
        )

        self.send_button.setEnabled(
            False
        )

        self.worker = ChatWorker(
            prompt,
            self.scan_context,
        )

        self.worker.completed.connect(
            self._on_completed
        )

        self.worker.failed.connect(
            self._on_failed
        )

        self.worker.finished.connect(
            self._worker_finished
        )

        self.worker.start()

    def _on_completed(
        self,
        response: str,
    ):

        self._remove_last_thinking_message()

        self._append_message(
            "DesktopAI",
            response,
        )

    def _on_failed(
        self,
        error: str,
    ):

        self._remove_last_thinking_message()

        self._append_message(
            "DesktopAI",
            f"AI request failed: {error}",
        )

    def _worker_finished(self):

        self.input.setEnabled(
            True
        )

        self.send_button.setEnabled(
            True
        )

        self.input.setFocus()

        self.worker = None

    # ==================================================================
    # MESSAGE UI
    # ==================================================================

    def _append_message(
        self,
        sender: str,
        text: str,
    ):

        safe_text = (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )

        color = (
            "var(--primary)"
        )

        self.chat.append(
            f"""
            <p>
                <b>{sender}</b>
            </p>
            <p>{safe_text}</p>
            """
        )

    def _remove_last_thinking_message(self):

        cursor = self.chat.textCursor()

        cursor.movePosition(
            cursor.MoveOperation.End
        )

        document = self.chat.document()

        text = document.toPlainText()

        if "Thinking..." not in text:
            return

        # Rebuild is safer than manipulating arbitrary QTextBlocks.
        lines = text.splitlines()

        while lines and (
            lines[-1].strip() == ""
            or lines[-1].strip() == "Thinking..."
        ):
            lines.pop()

        self.chat.clear()

        if not lines:
            return

        self.chat.setPlainText(
            "\n".join(lines)
        )