"""
DesktopAI v2.0 — Setup Wizard
File: src/gui/dialogs/setup_wizard.py

First-run onboarding:
    1. Check Ollama availability.
    2. Select the initial scan folder.
    3. Scan files and build the semantic search index.

The wizard is safe to run with --mock-ai. In mock mode, the Ollama
connectivity requirement is bypassed because the application provider
has already been replaced by MockProvider in main.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import urllib.error
import urllib.request

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from infrastructure.config.settings import Settings
from services import ApplicationServices


class OllamaCheckThread(QThread):
    """Check Ollama availability without blocking the GUI."""

    check_completed = Signal(bool, str)

    def __init__(self, host: str = "http://localhost:11434") -> None:
        super().__init__()
        self._host = host.rstrip("/")

    def run(self) -> None:
        url = f"{self._host}/api/tags"

        try:
            request = urllib.request.Request(
                url,
                method="GET",
                headers={"Accept": "application/json"},
            )

            with urllib.request.urlopen(request, timeout=2.0) as response:
                ok = 200 <= response.status < 300

            if ok:
                self.check_completed.emit(
                    True,
                    f"Ollama is running at {self._host}",
                )
            else:
                self.check_completed.emit(
                    False,
                    f"Ollama returned HTTP {response.status}.",
                )

        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            self.check_completed.emit(
                False,
                f"Ollama is not reachable: {exc}",
            )
        except Exception as exc:
            self.check_completed.emit(
                False,
                f"Ollama check failed: {exc}",
            )


class IndexBuildThread(QThread):
    """Scan the selected folder and build the search index."""

    progress = Signal(int, str)
    build_completed = Signal(dict)
    error = Signal(str)

    def __init__(
        self,
        file_service,
        scan_folder: Path,
    ) -> None:
        super().__init__()
        self._file_service = file_service
        self._scan_folder = scan_folder

    def run(self) -> None:
        try:
            self.progress.emit(
                5,
                "Scanning selected folder…",
            )

            results = self._file_service.scan_folder(
                str(self._scan_folder),
                progress_callback=self._on_scan_progress,
            )

            self.progress.emit(
                50,
                f"Scan complete — {len(results)} files found.",
            )

            self.progress.emit(
                60,
                "Building semantic search index…",
            )

            index_result = self._file_service.build_index(
                files=results,
                progress_callback=self._on_index_progress,
            )

            if not isinstance(index_result, dict):
                index_result = {
                    "indexed": 0,
                    "error": "Invalid index-build response.",
                }

            error_message = index_result.get("error")
            if error_message:
                self.error.emit(str(error_message))
                return

            indexed = int(index_result.get("indexed", 0))

            self.progress.emit(
                100,
                f"Index complete — {indexed} files indexed.",
            )

            self.build_completed.emit(
                {
                    "scanned": len(results),
                    "indexed": indexed,
                    "folder": str(self._scan_folder),
                }
            )

        except Exception as exc:
            self.error.emit(str(exc))

    def _on_scan_progress(
        self,
        value: int,
        message: str,
    ) -> None:
        # Map scan progress (0–100) into wizard progress (5–50).
        mapped = 5 + int(max(0, min(100, value)) * 0.45)
        self.progress.emit(mapped, message)

    def _on_index_progress(
        self,
        value: int,
        message: str,
    ) -> None:
        # Map index progress (0–100) into wizard progress (60–100).
        mapped = 60 + int(max(0, min(100, value)) * 0.40)
        self.progress.emit(mapped, message)


class WelcomePage(QWizardPage):
    """Page 1: welcome and Ollama connectivity check."""

    def __init__(
        self,
        allow_offline: bool = False,
    ) -> None:
        super().__init__()

        self.setTitle("Welcome to DesktopAI")
        self.setSubTitle(
            "Set up your local AI file organizer."
        )

        self._allow_offline = allow_offline
        self._ollama_ok = False
        self._thread: OllamaCheckThread | None = None

        layout = QVBoxLayout()

        welcome_text = QLabel(
            "DesktopAI organizes, searches, and understands your files locally.\n\n"
            "This setup will:\n"
            "1. Check your local AI provider\n"
            "2. Let you choose a scan folder\n"
            "3. Build the semantic search index"
        )
        welcome_text.setWordWrap(True)
        layout.addWidget(welcome_text)

        layout.addSpacing(20)

        self.ollama_status_lbl = QLabel(
            "Checking Ollama…"
        )
        self.ollama_status_lbl.setWordWrap(True)
        self.ollama_status_lbl.setFont(
            QFont("Segoe UI", 10)
        )
        layout.addWidget(self.ollama_status_lbl)

        self.check_btn = QPushButton(
            "Check Ollama Status"
        )
        self.check_btn.clicked.connect(
            self._check_ollama
        )
        layout.addWidget(self.check_btn)

        if self._allow_offline:
            self.mock_note = QLabel(
                "Mock AI mode detected. Ollama is optional for this run."
            )
            self.mock_note.setWordWrap(True)
            self.mock_note.setObjectName("Muted")
            layout.addWidget(self.mock_note)

        layout.addStretch()
        self.setLayout(layout)

        if self._allow_offline:
            self._ollama_ok = True
            self.ollama_status_lbl.setText(
                "✓ Offline/mock mode enabled — Ollama check skipped."
            )
            self.check_btn.setEnabled(False)
        else:
            self._check_ollama()

    def _check_ollama(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            return

        self.check_btn.setEnabled(False)
        self.ollama_status_lbl.setText(
            "Checking Ollama…"
        )

        self._thread = OllamaCheckThread(
            host=Settings.ai.host
        )
        self._thread.check_completed.connect(
            self._on_ollama_check_done
        )
        self._thread.finished.connect(
            self._on_ollama_thread_finished
        )
        self._thread.start()

    def _on_ollama_check_done(
        self,
        is_running: bool,
        message: str,
    ) -> None:
        if is_running:
            self._ollama_ok = True
            self.ollama_status_lbl.setText(
                f"✓ {message}"
            )
            self.check_btn.setEnabled(False)
        else:
            self._ollama_ok = False
            self.ollama_status_lbl.setText(
                "✗ Ollama is not running.\n\n"
                f"{message}\n\n"
                "Start Ollama and click 'Check Ollama Status' again."
            )
            self.check_btn.setEnabled(True)

        self.completeChanged.emit()

    def _on_ollama_thread_finished(self) -> None:
        thread = self._thread
        self._thread = None

        if thread is not None:
            thread.deleteLater()

    def isComplete(self) -> bool:
        return self._ollama_ok


class ScanFolderPage(QWizardPage):
    """Page 2: select the initial scan folder."""

    def __init__(self) -> None:
        super().__init__()

        self.setTitle("Select Scan Folder")
        self.setSubTitle(
            "Choose the folder DesktopAI should scan."
        )

        self.scan_folder: Optional[Path] = None

        layout = QVBoxLayout()

        self.folder_lbl = QLabel(
            "No folder selected."
        )
        self.folder_lbl.setWordWrap(True)
        layout.addWidget(self.folder_lbl)

        browse_btn = QPushButton(
            "Browse…"
        )
        browse_btn.clicked.connect(
            self._pick_folder
        )
        layout.addWidget(browse_btn)

        layout.addSpacing(20)

        info = QLabel(
            "DesktopAI will scan this folder and its supported files.\n"
            "Large directories may take longer during the initial setup."
        )
        info.setWordWrap(True)
        info.setObjectName("Muted")
        layout.addWidget(info)

        layout.addStretch()
        self.setLayout(layout)

        # Reuse previously selected folder when available.
        configured = str(
            getattr(Settings.app, "scan_folder", "") or ""
        ).strip()

        if configured:
            candidate = Path(configured)
            if candidate.exists() and candidate.is_dir():
                self.scan_folder = candidate
                self.folder_lbl.setText(
                    f"Folder: {candidate}"
                )

    def _pick_folder(self) -> None:
        current = (
            str(self.scan_folder)
            if self.scan_folder
            else str(Path.home())
        )

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Scan",
            current,
        )

        if not folder:
            return

        selected = Path(folder).resolve()

        if not selected.exists() or not selected.is_dir():
            self.scan_folder = None
            self.folder_lbl.setText(
                "The selected path is not a valid folder."
            )
            self.completeChanged.emit()
            return

        self.scan_folder = selected
        self.folder_lbl.setText(
            f"Folder: {selected}"
        )
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        return (
            self.scan_folder is not None
            and self.scan_folder.exists()
            and self.scan_folder.is_dir()
        )


class IndexBuildPage(QWizardPage):
    """Page 3: scan files and build the semantic index."""

    def __init__(
        self,
        services: ApplicationServices,
    ) -> None:
        super().__init__()

        self.setTitle("Build Search Index")
        self.setSubTitle(
            "Scan your files and prepare semantic search."
        )

        self.services = services
        self.is_built = False
        self._thread: IndexBuildThread | None = None

        layout = QVBoxLayout()

        self.info_lbl = QLabel(
            "Ready to scan the selected folder and build the search index."
        )
        self.info_lbl.setWordWrap(True)
        layout.addWidget(self.info_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.build_btn = QPushButton(
            "Build Index Now"
        )
        self.build_btn.clicked.connect(
            self._build_index
        )
        layout.addWidget(self.build_btn)

        layout.addStretch()
        self.setLayout(layout)

    def _build_index(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            return

        wizard = self.wizard()

        if wizard is None:
            self._show_error(
                "Wizard instance is not available."
            )
            return

        scan_page = wizard.scan_page

        if scan_page.scan_folder is None:
            self._show_error(
                "No scan folder selected."
            )
            return

        self.is_built = False
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.build_btn.setEnabled(False)

        self.info_lbl.setText(
            f"Preparing: {scan_page.scan_folder}"
        )
        self.completeChanged.emit()

        self._thread = IndexBuildThread(
            self.services.file_service,
            scan_page.scan_folder,
        )

        self._thread.progress.connect(
            self._on_progress
        )
        self._thread.build_completed.connect(
            self._on_build_success
        )
        self._thread.error.connect(
            self._on_build_error
        )
        self._thread.finished.connect(
            self._on_thread_finished
        )
        self._thread.start()

    def _on_progress(
        self,
        value: int,
        message: str,
    ) -> None:
        self.progress_bar.setValue(
            max(0, min(100, int(value)))
        )
        self.info_lbl.setText(message)

    def _on_build_success(
        self,
        result: dict,
    ) -> None:
        self.is_built = True

        scanned = int(
            result.get("scanned", 0)
        )
        indexed = int(
            result.get("indexed", 0)
        )

        self.progress_bar.setValue(100)
        self.info_lbl.setText(
            "✓ Setup index completed.\n\n"
            f"Scanned: {scanned} files\n"
            f"Indexed: {indexed} files\n\n"
            "Click Finish to launch DesktopAI."
        )

        self.build_btn.setEnabled(False)
        self.completeChanged.emit()

    def _on_build_error(
        self,
        error_message: str,
    ) -> None:
        self.is_built = False
        self.progress_bar.setValue(0)
        self.info_lbl.setText(
            f"✗ Index build failed:\n\n{error_message}"
        )
        self.build_btn.setEnabled(True)
        self.completeChanged.emit()

    def _on_thread_finished(self) -> None:
        thread = self._thread
        self._thread = None

        if thread is not None:
            thread.deleteLater()

    def _show_error(
        self,
        message: str,
    ) -> None:
        self.info_lbl.setText(
            f"✗ {message}"
        )
        self.is_built = False
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        return self.is_built


class SetupWizard(QWizard):
    """Main first-run setup wizard."""

    def __init__(
        self,
        services: ApplicationServices,
        *,
        allow_offline: bool = False,
    ) -> None:
        super().__init__()

        self.setWindowTitle(
            "DesktopAI Setup"
        )
        self.setMinimumSize(
            560,
            440,
        )

        self.services = services
        self.allow_offline = allow_offline

        self.welcome_page = WelcomePage(
            allow_offline=allow_offline
        )
        self.scan_page = ScanFolderPage()
        self.index_page = IndexBuildPage(
            services
        )

        self.addPage(
            self.welcome_page
        )
        self.addPage(
            self.scan_page
        )
        self.addPage(
            self.index_page
        )

        self.finished.connect(
            self._on_wizard_finished
        )

    def _on_wizard_finished(
        self,
        _result: int,
    ) -> None:
        """Persist first-run settings after successful wizard completion."""
        if not self.index_page.is_built:
            return

        scan_folder = self.scan_page.scan_folder

        if scan_folder is None:
            return

        Settings.app.scan_folder = str(
            scan_folder
        )
        Settings.app.first_run = False
        Settings.save()