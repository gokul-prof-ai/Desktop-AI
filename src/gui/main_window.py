"""
DesktopAI
Desktop GUI (Phase 10)

A PySide6 desktop interface with four tabs:
- Dashboard: scan a folder and see what was found
- Search:    build the semantic search index and search it
- AI Chat:   talk to the local Ollama model directly
- Settings:  see the active configuration at a glance

Every operation that could take a while (Ollama calls, FAISS
indexing) runs on a background QThread so the window never
freezes — important on the low-end laptop this is built for.
Qt widgets must only be touched from the main thread, so each
worker below only ever emits a signal with a plain result; the
tab that owns it applies that result to the UI when the signal
fires.
"""

from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ai.ollama_client import generate_response
from core import config
from core.logger import get_logger
from database.database import DatabaseManager
from scanner.scanner import FileScanner
from search.search_engine import build_search_index, semantic_search

logger = get_logger("gui")


# ---------------------------------------------------------------
# Background workers
# ---------------------------------------------------------------


class ScanWorker(QThread):
    """Scans a folder and saves the results to the database."""

    finished = Signal(list)  # list[FileInfo]
    failed = Signal(str)

    def __init__(self, folder: Path):
        super().__init__()
        self.folder = folder

    def run(self):
        try:
            scanner = FileScanner()
            files = scanner.scan(self.folder)

            db = DatabaseManager(config.DATABASE_PATH)
            db.connect()
            for file_info in files:
                db.save_file(file_info)
            db.close()

            self.finished.emit(files)
        except Exception as error:  # noqa: BLE001 - surface any failure to the UI
            logger.exception("Scan failed")
            self.failed.emit(str(error))


class BuildIndexWorker(QThread):
    """Builds the semantic search index from whatever's in the database."""

    finished = Signal(int)
    failed = Signal(str)

    def run(self):
        try:
            count = build_search_index()
            self.finished.emit(count)
        except Exception as error:  # noqa: BLE001
            logger.exception("Index build failed")
            self.failed.emit(str(error))


class SearchWorker(QThread):
    """Runs one semantic search query."""

    finished = Signal(list)  # list[SearchResult]
    failed = Signal(str)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self):
        try:
            results = semantic_search(self.query)
            self.finished.emit(results)
        except Exception as error:  # noqa: BLE001
            logger.exception("Search failed")
            self.failed.emit(str(error))


class ChatWorker(QThread):
    """Sends one prompt to the local Ollama model."""

    finished = Signal(str)  # response text, "" if the AI was unavailable
    failed = Signal(str)

    def __init__(self, prompt: str):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            response = generate_response(self.prompt)
            self.finished.emit(response or "")
        except Exception as error:  # noqa: BLE001
            logger.exception("Chat request failed")
            self.failed.emit(str(error))


# ---------------------------------------------------------------
# Dashboard tab
# ---------------------------------------------------------------


class DashboardTab(QWidget):
    """Scan a folder and see what DesktopAI found in it."""

    def __init__(self):
        super().__init__()
        self._worker: ScanWorker | None = None
        self._selected_folder = config.SCAN_FOLDER

        layout = QVBoxLayout(self)

        self.folder_label = QLabel(f"Folder to scan: {self._selected_folder}")
        layout.addWidget(self.folder_label)

        button_row = QHBoxLayout()
        choose_button = QPushButton("Choose Folder...")
        choose_button.clicked.connect(self._choose_folder)
        button_row.addWidget(choose_button)

        self.scan_button = QPushButton("Scan Now")
        self.scan_button.clicked.connect(self._start_scan)
        button_row.addWidget(self.scan_button)
        layout.addLayout(button_row)

        self.status_label = QLabel("Ready.")
        layout.addWidget(self.status_label)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Size (bytes)", "Type"])
        layout.addWidget(self.table)

        self._load_existing_files()

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose a folder to scan")
        if folder:
            self._selected_folder = Path(folder)
            self.folder_label.setText(f"Folder to scan: {self._selected_folder}")

    def _start_scan(self):
        if self._worker is not None and self._worker.isRunning():
            return  # a scan is already in progress

        self.status_label.setText(f"Scanning {self._selected_folder} ...")
        self.scan_button.setEnabled(False)

        self._worker = ScanWorker(self._selected_folder)
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.failed.connect(self._on_scan_failed)
        self._worker.start()

    def _on_scan_finished(self, files):
        self.scan_button.setEnabled(True)
        self.status_label.setText(f"Found {len(files)} file(s). Saved to database.")
        self._populate_table(files)

    def _on_scan_failed(self, message: str):
        self.scan_button.setEnabled(True)
        self.status_label.setText("Scan failed.")
        QMessageBox.warning(self, "Scan Failed", message)

    def _load_existing_files(self):
        """Show whatever's already in the database on startup."""
        try:
            db = DatabaseManager(config.DATABASE_PATH)
            db.connect()
            files = db.load_files()
            db.close()
            self._populate_table(files)
            self.status_label.setText(f"{len(files)} file(s) previously scanned.")
        except Exception:  # noqa: BLE001 - a missing/empty DB is fine on first run
            logger.info("No existing database to load yet.")

    def _populate_table(self, files):
        self.table.setRowCount(len(files))
        for row, file_info in enumerate(files):
            self.table.setItem(row, 0, QTableWidgetItem(file_info.name))
            self.table.setItem(row, 1, QTableWidgetItem(str(file_info.size)))
            self.table.setItem(
                row, 2, QTableWidgetItem(file_info.detected_type or "unknown")
            )


# ---------------------------------------------------------------
# Search tab
# ---------------------------------------------------------------


class SearchTab(QWidget):
    """Build the semantic search index and search it in plain language."""

    def __init__(self):
        super().__init__()
        self._build_worker: BuildIndexWorker | None = None
        self._search_worker: SearchWorker | None = None

        layout = QVBoxLayout(self)

        self.build_button = QPushButton("Build / Rebuild Search Index")
        self.build_button.clicked.connect(self._start_build)
        layout.addWidget(self.build_button)

        self.status_label = QLabel(
            "Index not built yet this session. Scan some files first "
            "(Dashboard tab), then build the index."
        )
        layout.addWidget(self.status_label)

        search_row = QHBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("e.g. tax documents from last year")
        self.query_input.returnPressed.connect(self._start_search)
        search_row.addWidget(self.query_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._start_search)
        search_row.addWidget(self.search_button)
        layout.addLayout(search_row)

        self.results_list = QListWidget()
        layout.addWidget(self.results_list)

    def _start_build(self):
        if self._build_worker is not None and self._build_worker.isRunning():
            return

        self.status_label.setText(
            "Building search index (calls the local AI once per file)..."
        )
        self.build_button.setEnabled(False)

        self._build_worker = BuildIndexWorker()
        self._build_worker.finished.connect(self._on_build_finished)
        self._build_worker.failed.connect(self._on_build_failed)
        self._build_worker.start()

    def _on_build_finished(self, count: int):
        self.build_button.setEnabled(True)
        if count == 0:
            self.status_label.setText(
                "Nothing was indexed. Make sure Ollama is running with the "
                f"'{config.EMBEDDING_MODEL}' model pulled, and that you've "
                "scanned files with real text content."
            )
        else:
            self.status_label.setText(f"Indexed {count} file(s). Ready to search.")

    def _on_build_failed(self, message: str):
        self.build_button.setEnabled(True)
        self.status_label.setText("Index build failed.")
        QMessageBox.warning(self, "Index Build Failed", message)

    def _start_search(self):
        query = self.query_input.text().strip()
        if not query:
            return
        if self._search_worker is not None and self._search_worker.isRunning():
            return

        self.results_list.clear()
        self.results_list.addItem("Searching...")
        self.search_button.setEnabled(False)

        self._search_worker = SearchWorker(query)
        self._search_worker.finished.connect(self._on_search_finished)
        self._search_worker.failed.connect(self._on_search_failed)
        self._search_worker.start()

    def _on_search_finished(self, results):
        self.search_button.setEnabled(True)
        self.results_list.clear()

        if not results:
            self.results_list.addItem(
                "No matches. Build the index first, or try a different query."
            )
            return

        for result in results:
            self.results_list.addItem(f"{result.score:.3f}  {result.path}")

    def _on_search_failed(self, message: str):
        self.search_button.setEnabled(True)
        self.results_list.clear()
        QMessageBox.warning(self, "Search Failed", message)


# ---------------------------------------------------------------
# AI Chat tab
# ---------------------------------------------------------------


class ChatTab(QWidget):
    """A simple chat window talking directly to the local Ollama model."""

    # Keep only the last few exchanges in the prompt sent to the model,
    # so prompts stay short and fast on low-end hardware.
    MAX_HISTORY_TURNS = 4

    def __init__(self):
        super().__init__()
        self._worker: ChatWorker | None = None
        self._history: list[tuple[str, str]] = []  # (user_text, ai_text)
        self._pending_user_text = ""

        layout = QVBoxLayout(self)

        self.transcript = QPlainTextEdit()
        self.transcript.setReadOnly(True)
        layout.addWidget(self.transcript)

        input_row = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText(
            f"Ask the local AI ({config.OLLAMA_MODEL}) something..."
        )
        self.input_box.returnPressed.connect(self._send)
        input_row.addWidget(self.input_box)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._send)
        input_row.addWidget(self.send_button)
        layout.addLayout(input_row)

    def _send(self):
        text = self.input_box.text().strip()
        if not text:
            return
        if self._worker is not None and self._worker.isRunning():
            return

        self.transcript.appendPlainText(f"You: {text}")
        self.input_box.clear()
        self.send_button.setEnabled(False)
        self._pending_user_text = text

        prompt = self._build_prompt(text)

        self._worker = ChatWorker(prompt)
        self._worker.finished.connect(self._on_response)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _build_prompt(self, new_text: str) -> str:
        """Include recent turns as plain-text context, most recent last."""
        recent = self._history[-self.MAX_HISTORY_TURNS :]
        pieces = [
            f"User: {user_text}\nAssistant: {ai_text}"
            for user_text, ai_text in recent
        ]
        pieces.append(f"User: {new_text}\nAssistant:")
        return "\n\n".join(pieces)

    def _on_response(self, response: str):
        self.send_button.setEnabled(True)

        if not response:
            response = (
                "(No response — is Ollama running with the "
                f"'{config.OLLAMA_MODEL}' model pulled?)"
            )

        self.transcript.appendPlainText(f"AI: {response}\n")
        self._history.append((self._pending_user_text, response))

    def _on_failed(self, message: str):
        self.send_button.setEnabled(True)
        self.transcript.appendPlainText(f"(error: {message})\n")


# ---------------------------------------------------------------
# Settings tab
# ---------------------------------------------------------------


class SettingsTab(QWidget):
    """A read-only view of the active configuration (see core/config.py)."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        lines = (
            [
                f"Project root:        {config.PROJECT_ROOT}",
                f"Scan folder:         {config.SCAN_FOLDER}",
                f"Database file:       {config.DATABASE_PATH}",
                f"Search index:        {config.SEARCH_INDEX_PATH}",
                f"Logs folder:         {config.LOGS_DIR}",
                "",
                f"Ollama URL:          {config.OLLAMA_URL}",
                f"Chat model:          {config.OLLAMA_MODEL}",
                f"Embedding model:     {config.EMBEDDING_MODEL}",
                "",
                "Watched folders (for the folder watcher, watch_app.py):",
            ]
            + [f"  - {folder}" for folder in config.WATCH_FOLDERS]
            + [
                "",
                "All of these can be overridden with DESKTOPAI_<NAME> "
                "environment variables — see core/config.py for the full list.",
            ]
        )

        text = QPlainTextEdit("\n".join(lines))
        text.setReadOnly(True)
        layout.addWidget(text)


# ---------------------------------------------------------------
# Main window
# ---------------------------------------------------------------


class MainWindow(QMainWindow):
    # Each tab's attribute name(s) that may hold a running QThread worker.
    _WORKER_ATTRS = {
        "dashboard": ("_worker",),
        "search": ("_build_worker", "_search_worker"),
        "chat": ("_worker",),
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DesktopAI")
        self.resize(800, 600)

        self._dashboard_tab = DashboardTab()
        self._search_tab = SearchTab()
        self._chat_tab = ChatTab()
        self._settings_tab = SettingsTab()

        tabs = QTabWidget()
        tabs.addTab(self._dashboard_tab, "Dashboard")
        tabs.addTab(self._search_tab, "Search")
        tabs.addTab(self._chat_tab, "AI Chat")
        tabs.addTab(self._settings_tab, "Settings")
        self.setCentralWidget(tabs)

    def closeEvent(self, event):
        """
        Stop any still-running background thread before the window
        closes. Without this, closing the app mid-scan (or mid-index-
        build, or mid-chat-request) destroys the QThread object while
        its run() is still executing in the background, which Qt
        warns about and which can crash on some platforms.
        """
        named_tabs = {
            "dashboard": self._dashboard_tab,
            "search": self._search_tab,
            "chat": self._chat_tab,
        }

        for tab_name, attrs in self._WORKER_ATTRS.items():
            tab = named_tabs[tab_name]
            for attr in attrs:
                worker = getattr(tab, attr, None)
                if worker is not None and worker.isRunning():
                    worker.quit()
                    if not worker.wait(3000):  # give it 3s to finish cleanly
                        worker.terminate()
                        worker.wait()

        event.accept()