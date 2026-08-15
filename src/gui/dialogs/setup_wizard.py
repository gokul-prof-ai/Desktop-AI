"""
SetupWizard: First-run onboarding flow.
- Checks Ollama availability
- Lets user pick scan folder
- Builds FAISS index asynchronously
"""
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout,
    QLabel, QPushButton, QFileDialog, QProgressBar
)
from PySide6.QtCore import QThread, pyqtSignal
from PySide6.QtGui import QFont

from infrastructure.config.settings import Settings
from services import ApplicationServices


class OllamaCheckThread(QThread):
    """Background thread to check Ollama availability."""
    finished = pyqtSignal(bool)
    
    def run(self):
        try:
            import subprocess
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                timeout=2,
                capture_output=True
            )
            self.finished.emit(result.returncode == 0)
        except Exception:
            self.finished.emit(False)


class IndexBuildThread(QThread):
    """Background thread to scan and build index."""
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, file_service, scan_folder: Path):
        super().__init__()
        self.file_service = file_service
        self.scan_folder = scan_folder
    
    def run(self):
        try:
            self.progress.emit(10)
            self.file_service.scan_folder(str(self.scan_folder))
            self.progress.emit(50)
            self.file_service.build_index()
            self.progress.emit(100)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class WelcomePage(QWizardPage):
    """Page 1: Welcome + Ollama check."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to DesktopAI")
        self.setSubTitle("Let's set up your offline AI assistant.")
        self._ollama_ok = False
        
        layout = QVBoxLayout()
        
        welcome_text = QLabel(
            "DesktopAI helps you organize, search, and understand your files locally.\n\n"
            "This wizard will:\n"
            "1. Check if Ollama is running\n"
            "2. Set up your scan folder\n"
            "3. Build a searchable index"
        )
        welcome_text.setWordWrap(True)
        layout.addWidget(welcome_text)
        
        layout.addSpacing(20)
        self.ollama_status_lbl = QLabel("Checking Ollama...")
        self.ollama_status_lbl.setFont(QFont("Courier", 10))
        layout.addWidget(self.ollama_status_lbl)
        
        self.check_btn = QPushButton("Check Ollama Status")
        self.check_btn.clicked.connect(self._check_ollama)
        layout.addWidget(self.check_btn)
        
        layout.addStretch()
        self.setLayout(layout)
        
        self._check_ollama()
    
    def _check_ollama(self):
        self.check_btn.setEnabled(False)
        self.ollama_status_lbl.setText("Checking Ollama...")
        
        self._thread = OllamaCheckThread()
        self._thread.finished.connect(self._on_ollama_check_done)
        self._thread.start()
    
    def _on_ollama_check_done(self, is_running: bool):
        if is_running:
            self.ollama_status_lbl.setText("✓ Ollama is running on http://localhost:11434")
            self._ollama_ok = True
            self.completeChanged.emit()
        else:
            self.ollama_status_lbl.setText(
                "✗ Ollama is not running.\n"
                "Please start Ollama before continuing:\n"
                "  1. Download from https://ollama.ai\n"
                "  2. Run: ollama serve\n"
                "  3. Come back and click 'Check Ollama Status'"
            )
            self.check_btn.setEnabled(True)
    
    def isComplete(self) -> bool:
        return self._ollama_ok


class ScanFolderPage(QWizardPage):
    """Page 2: Select scan folder."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Select Scan Folder")
        self.setSubTitle("Which folder would you like to organize?")
        
        self.scan_folder: Optional[Path] = None
        
        layout = QVBoxLayout()
        
        self.folder_lbl = QLabel("No folder selected.")
        layout.addWidget(self.folder_lbl)
        
        pick_btn = QPushButton("Browse...")
        pick_btn.clicked.connect(self._pick_folder)
        layout.addWidget(pick_btn)
        
        layout.addSpacing(20)
        info = QLabel(
            "We'll scan this folder and all subfolders for files.\n"
            "This might take a while for large directories."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _pick_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Scan",
            str(Path.home())
        )
        if folder:
            self.scan_folder = Path(folder)
            self.folder_lbl.setText(f"Folder: {self.scan_folder.name}")
            self.completeChanged.emit()
    
    def isComplete(self) -> bool:
        return self.scan_folder is not None


class IndexBuildPage(QWizardPage):
    """Page 3: Build index confirmation + progress."""
    
    def __init__(self, services: ApplicationServices):
        super().__init__()
        self.setTitle("Build Index")
        self.setSubTitle("Scan and index your files.")
        self.services = services
        self.is_built = False
        self._thread: Optional[IndexBuildThread] = None
        
        layout = QVBoxLayout()
        
        self.info_lbl = QLabel(
            "Ready to build the FAISS index.\n"
            "This will scan your folder and create embeddings for all files."
        )
        self.info_lbl.setWordWrap(True)
        layout.addWidget(self.info_lbl)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.build_btn = QPushButton("Build Index Now")
        self.build_btn.clicked.connect(self._build_index)
        layout.addWidget(self.build_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _build_index(self):
        self.progress_bar.setVisible(True)
        self.build_btn.setEnabled(False)
        self.info_lbl.setText("Building index... (this may take a while)")
        
        wizard = self.wizard()
        scan_page = wizard.scan_page
        if not scan_page.scan_folder:
            self.info_lbl.setText("✗ No scan folder selected!")
            self.build_btn.setEnabled(True)
            return
        
        self._thread = IndexBuildThread(
            self.services.file_service,
            scan_page.scan_folder
        )
        self._thread.progress.connect(self.progress_bar.setValue)
        self._thread.error.connect(self._on_build_error)
        self._thread.finished.connect(self._on_build_success)
        self._thread.start()
    
    def _on_build_success(self):
        self.is_built = True
        self.info_lbl.setText("✓ Index built successfully!")
        self.progress_bar.setValue(100)
        self.completeChanged.emit()
    
    def _on_build_error(self, error_msg: str):
        self.info_lbl.setText(f"✗ Error: {error_msg}")
        self.build_btn.setEnabled(True)
    
    def isComplete(self) -> bool:
        return self.is_built


class SetupWizard(QWizard):
    """Main setup wizard for first-run configuration."""
    
    def __init__(self, services: ApplicationServices):
        super().__init__()
        self.setWindowTitle("DesktopAI Setup")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.services = services
        
        self.welcome_page = WelcomePage()
        self.scan_page = ScanFolderPage()
        self.index_page = IndexBuildPage(services)
        
        self.addPage(self.welcome_page)
        self.addPage(self.scan_page)
        self.addPage(self.index_page)
        
        self.finished.connect(self._on_wizard_finished)
    
    def _on_wizard_finished(self):
        """Save config when wizard completes."""
        if self.scan_page.scan_folder:
            Settings.app.scan_folder = str(self.scan_page.scan_folder)
            Settings.app.first_run = False
            Settings.save()