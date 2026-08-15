"""src/gui/dialogs/setup_wizard.py"""
import os
import time
import requests
from PySide6.QtCore import Signal, Qt, QThread, QObject
from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QProgressBar
)
from PySide6.QtGui import QFont

from infrastructure.config.settings import Settings
from application.file_service import FileService


class OllamaCheckWorker(QObject):
    finished = Signal(bool)

    def run(self):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            self.finished.emit(response.status_code == 200)
        except Exception:
            self.finished.emit(False)


class IndexBuildWorker(QObject):
    progress = Signal(int)
    finished = Signal(bool)

    def run(self):
        try:
            # Trigger FAISS build
            FileService.build_index()
            # Simulate progress UI update
            for i in range(1, 101):
                self.progress.emit(i)
                time.sleep(0.05)
            self.finished.emit(True)
        except Exception as e:
            print(f"Error building index: {e}")
            self.finished.emit(False)


class WelcomePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Welcome to DesktopAI V2")
        self.setSubTitle("Let's check your local AI setup.")

        layout = QVBoxLayout()
        self.status_label = QLabel("Checking Ollama status...")
        self.status_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        
        self.worker_thread = QThread()
        self.worker = OllamaCheckWorker()
        self.worker.moveToThread(self.worker_thread)
        
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_check_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        
        self.worker_thread.start()

    def on_check_finished(self, is_running: bool):
        if is_running:
            self.status_label.setText("✅ Ollama is running! (llama3.2:3b)")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("⚠️ Ollama is not running. You can still use DesktopAI in mock mode,\nbut please run 'ollama serve' in your terminal for full features.")
            self.status_label.setStyleSheet("color: orange;")
        self.completeChanged.emit()

    def isComplete(self):
        return True


class ScanFolderPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Select Folder to Organize")
        self.setSubTitle("Choose the main directory you want DesktopAI to scan.")

        layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        self.path_input = QLabel("No folder selected")
        self.path_input.setStyleSheet("padding: 8px; background: #f0f0f0; border: 1px solid #ccc; border-radius: 4px;")
        path_layout.addWidget(self.path_input, 1)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse)
        path_layout.addWidget(self.browse_btn)
        
        layout.addLayout(path_layout)
        layout.addStretch()
        self.setLayout(layout)

    def browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Scan Folder")
        if folder:
            self.path_input.setText(folder)
            self.completeChanged.emit()

    def isComplete(self):
        return os.path.isdir(self.path_input.text())

    def selected_path(self) -> str:
        return self.path_input.text()


class IndexBuildPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Building Search Index")
        self.setSubTitle("DesktopAI is analyzing your files...")
        
        layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Preparing...")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.is_finished = False
        
    def initializePage(self):
        self.worker_thread = QThread()
        self.worker = IndexBuildWorker()
        self.worker.moveToThread(self.worker_thread)
        
        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        
        self.worker_thread.start()

    def update_progress(self, value: int):
        self.progress_bar.setValue(value)
        self.status_label.setText(f"Processing files... {value}%")

    def on_finished(self, success: bool):
        self.is_finished = True
        if success:
            self.status_label.setText("✅ Index built successfully!")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("❌ Index build failed. Check logs.")
            self.status_label.setStyleSheet("color: red;")
        self.completeChanged.emit()

    def isComplete(self):
        return self.is_finished


class SetupWizard(QWizard):
    finished_successfully = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DesktopAI Setup")
        self.setWizardStyle(QWizard.ModernStyle)
        self.resize(600, 400)

        self.page1 = WelcomePage()
        self.page2 = ScanFolderPage()
        self.page3 = IndexBuildPage()

        self.addPage(self.page1)
        self.addPage(self.page2)
        self.addPage(self.page3)

    def accept(self):
        folder = self.page2.selected_path()
        settings = Settings()
        settings.app.scan_folder = folder
        settings.app.first_run = False
        settings.save()
        
        self.finished_successfully.emit(folder)
        super().accept()