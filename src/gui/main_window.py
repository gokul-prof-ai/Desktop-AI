"""
DesktopAI
Modern Desktop GUI (Enhanced with Pre-flight Check & UI Capping)
"""
import sys
import time
import requests
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QColor
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, 
    QMainWindow, QMessageBox, QProgressBar, QPushButton, 
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, 
    QHeaderView, QFrame, QTextEdit
)

from core import config
from core.logger import get_logger
from organizer.auto_organizer import AutoOrganizer, OrganizationPlan

logger = get_logger("gui")
MAX_PREVIEW_ROWS = 500 # Prevent GUI freezing on massive folders

DARK_THEME = """
QMainWindow, QWidget { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
QPushButton { background-color: #89b4fa; color: #1e1e2e; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold; }
QPushButton:hover { background-color: #b4befe; }
QPushButton:disabled { background-color: #45475a; color: #6c7086; }
QPushButton#danger { background-color: #f38ba8; color: #1e1e2e; }
QPushButton#danger:hover { background-color: #eba0ac; }
QPushButton#success { background-color: #a6e3a1; color: #1e1e2e; }
QPushButton#success:hover { background-color: #94e2d5; }
QPushButton#exit { background-color: #45475a; color: #cdd6f4; }
QPushButton#exit:hover { background-color: #585b70; }
QTableWidget { background-color: #181825; border: 1px solid #313244; border-radius: 6px; gridline-color: #313244; }
QTableWidget::item { padding: 8px; border-bottom: 1px solid #313244; }
QTableWidget::item:selected { background-color: #45475a; color: #cdd6f4; }
QHeaderView::section { background-color: #11111b; color: #a6adc8; padding: 10px; border: none; border-bottom: 2px solid #89b4fa; font-weight: bold; }
QProgressBar { border: 1px solid #313244; border-radius: 6px; text-align: center; background-color: #181825; color: #cdd6f4; height: 20px; }
QProgressBar::chunk { background-color: #89b4fa; border-radius: 5px; }
QTextEdit { background-color: #181825; border: 1px solid #313244; border-radius: 6px; padding: 8px; }
QLabel#title { font-size: 24px; font-weight: bold; color: #89b4fa; }
QLabel#subtitle { font-size: 12px; color: #a6adc8; }
QFrame#drop_zone { background-color: #181825; border: 2px dashed #45475a; border-radius: 8px; }
QFrame#drop_zone:hover { border-color: #89b4fa; background-color: #1e1e2e; }
"""

class OrganizeWorker(QThread):
    progress = Signal(int, int, str)
    finished_plan = Signal(object)
    failed = Signal(str)
    def __init__(self, organizer: AutoOrganizer, folder: Path):
        super().__init__()
        self.organizer, self.folder = organizer, folder
    def run(self):
        try:
            plan = self.organizer.analyze_and_plan(self.folder, progress_callback=lambda c, t, m: self.progress.emit(c, t, m))
            self.finished_plan.emit(plan)
        except Exception as e:
            self.failed.emit(str(e))

class ApplyWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(list)
    failed = Signal(str)
    def __init__(self, organizer: AutoOrganizer, plan: OrganizationPlan):
        super().__init__()
        self.organizer, self.plan = organizer, plan
    def run(self):
        try:
            actions = self.organizer.apply_plan(self.plan, progress_callback=lambda c, t, m: self.progress.emit(c, t, m))
            self.finished.emit(actions)
        except Exception as e:
            self.failed.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DesktopAI Organizer")
        self.resize(1100, 750)
        self.setStyleSheet(DARK_THEME)
        self.organizer = AutoOrganizer()
        self.current_plan: Optional[OrganizationPlan] = None
        self._setup_ui()
        self._setup_drag_drop()
        self._check_ollama_status() # Pre-flight check

    def _check_ollama_status(self):
        """Checks if Ollama is running before the user starts."""
        try:
            response = requests.get(config.OLLAMA_HOST, timeout=3)
            if response.status_code == 200:
                self._log("✅ Ollama is running and ready.", "success")
            else:
                self._log("⚠️ Ollama is reachable but returned an error.", "warning")
        except requests.exceptions.ConnectionError:
            self._log("❌ Ollama is NOT running. Please run 'ollama serve' in a terminal.", "error")
            QMessageBox.warning(self, "Ollama Not Found", "Ollama is not running. Please open a terminal and run 'ollama serve' before analyzing files.")

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        header_layout = QHBoxLayout()
        title = QLabel("🚀 DesktopAI Organizer")
        title.setObjectName("title")
        subtitle = QLabel("Intelligent, local, and private file organization powered by AI.")
        subtitle.setObjectName("subtitle")
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)

        self.drop_zone = QFrame()
        self.drop_zone.setObjectName("drop_zone")
        self.drop_zone.setMinimumHeight(100)
        drop_layout = QVBoxLayout(self.drop_zone)
        drop_layout.setAlignment(Qt.AlignCenter)
        self.folder_label = QLabel("Drag & Drop a folder here, or click to select")
        self.folder_label.setStyleSheet("font-size: 16px; color: #a6adc8;")
        drop_layout.addWidget(self.folder_label)
        self.folder_path_display = QLabel("No folder selected")
        self.folder_path_display.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 15px;")
        drop_layout.addWidget(self.folder_path_display)
        self.drop_zone.mousePressEvent = lambda _: self._select_folder()
        main_layout.addWidget(self.drop_zone)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["File Name", "Current Location", "Suggested Category", "Confidence", "AI Reason"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        main_layout.addWidget(self.table, stretch=2)

        log_label = QLabel("Activity Log")
        log_label.setStyleSheet("font-weight: bold; color: #a6adc8; font-size: 13px;")
        main_layout.addWidget(log_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(130)
        main_layout.addWidget(self.log_text)

        btn_layout = QHBoxLayout()
        self.btn_analyze = QPushButton("🔍 Analyze Folder")
        self.btn_analyze.clicked.connect(self._start_analysis)
        self.btn_analyze.setEnabled(False)
        self.btn_apply = QPushButton("✅ Apply Organization")
        self.btn_apply.setObjectName("success")
        self.btn_apply.clicked.connect(self._start_apply)
        self.btn_apply.setEnabled(False)
        self.btn_undo = QPushButton("↩️ Undo Last")
        self.btn_undo.clicked.connect(self._undo_last)
        self.btn_undo.setEnabled(False)
        self.btn_cancel = QPushButton("⏹️ Cancel")
        self.btn_cancel.setObjectName("danger")
        self.btn_cancel.clicked.connect(self._cancel_operation)
        self.btn_cancel.setEnabled(False)
        self.btn_exit = QPushButton("🚪 Exit App")
        self.btn_exit.setObjectName("exit")
        self.btn_exit.clicked.connect(self.close)
        
        btn_layout.addWidget(self.btn_analyze)
        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_undo)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_exit)
        main_layout.addLayout(btn_layout)

    def _setup_drag_drop(self):
        self.drop_zone.setAcceptDrops(True)
        self.drop_zone.dragEnterEvent = self._drag_enter_event
        self.drop_zone.dropEvent = self._drop_event
    def _drag_enter_event(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
    def _drop_event(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = Path(urls[0].toLocalFile())
            if path.is_dir(): self._set_folder(path)
            else: self._log("Please drop a folder, not a file.", "warning")
    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Organize")
        if folder: self._set_folder(Path(folder))
    def _set_folder(self, path: Path):
        self.target_folder = path
        self.folder_path_display.setText(str(path))
        self.folder_label.setText("Selected Folder:")
        self._log(f"Folder selected: {path}")
        self.btn_analyze.setEnabled(True)

    def _log(self, message: str, level: str = "info"):
        colors = {"info": "#89b4fa", "success": "#a6e3a1", "warning": "#f9e2af", "error": "#f38ba8"}
        color = colors.get(level, "#cdd6f4")
        self.log_text.append(f'<span style="color:{color}">[{time.strftime("%H:%M:%S")}] {message}</span>')
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def _start_analysis(self):
        if not hasattr(self, 'target_folder') or not self.target_folder.exists():
            self._log("Please select a valid folder first.", "warning"); return
        self._toggle_ui_state(analyzing=True)
        self.table.setRowCount(0)
        self.current_plan = None
        self.btn_apply.setEnabled(False)
        self.worker = OrganizeWorker(self.organizer, self.target_folder)
        self.worker.progress.connect(self._on_analyze_progress)
        self.worker.finished_plan.connect(self._on_analyze_finished)
        self.worker.failed.connect(self._on_analyze_failed)
        self.worker.start()

    def _on_analyze_progress(self, current: int, total: int, message: str):
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"{message} ({current}/{total})")

    def _on_analyze_finished(self, plan: OrganizationPlan):
        self._toggle_ui_state(analyzing=False)
        self.progress_bar.setVisible(False)
        self.current_plan = plan
        self._log(f"Analysis complete. Found {plan.summary['categorized']} files.", "success")
        
        # Cap preview to prevent GUI freezing
        preview_actions = plan.actions[:MAX_PREVIEW_ROWS]
        self.table.setRowCount(len(preview_actions))
        for row, action in enumerate(preview_actions):
            self.table.setItem(row, 0, QTableWidgetItem(action.source.name))
            self.table.setItem(row, 1, QTableWidgetItem(str(action.source.parent)))
            self.table.setItem(row, 2, QTableWidgetItem(action.category))
            conf_item = QTableWidgetItem(f"{action.confidence:.0%}")
            conf_item.setForeground(QColor("#a6e3a1" if action.confidence > 0.8 else "#f9e2af" if action.confidence > 0.5 else "#f38ba8"))
            self.table.setItem(row, 3, conf_item)
            self.table.setItem(row, 4, QTableWidgetItem(action.reason))
            
        if len(plan.actions) > MAX_PREVIEW_ROWS:
            self._log(f"⚠️ Showing first {MAX_PREVIEW_ROWS} files in preview to keep UI fast. All {len(plan.actions)} files will be processed.", "warning")
            
        self.btn_apply.setEnabled(True)
        self._log("Review suggestions above. Click 'Apply' to proceed.", "info")

    def _on_analyze_failed(self, error: str):
        self._toggle_ui_state(analyzing=False)
        self.progress_bar.setVisible(False)
        self._log(f"Analysis failed: {error}", "error")
        QMessageBox.critical(self, "Analysis Failed", error)

    def _start_apply(self):
        if not self.current_plan or not self.current_plan.actions: return
        reply = QMessageBox.question(self, "Confirm", f"Move {len(self.current_plan.actions)} files?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No: return
        self._toggle_ui_state(applying=True)
        self.btn_undo.setEnabled(False)
        self.apply_worker = ApplyWorker(self.organizer, self.current_plan)
        self.apply_worker.progress.connect(self._on_apply_progress)
        self.apply_worker.finished.connect(self._on_apply_finished)
        self.apply_worker.failed.connect(self._on_apply_failed)
        self.apply_worker.start()

    def _on_apply_progress(self, current: int, total: int, message: str):
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"{message} ({current}/{total})")

    def _on_apply_finished(self, actions: list):
        self._toggle_ui_state(applying=False)
        self.progress_bar.setVisible(False)
        self.btn_undo.setEnabled(True)
        moved = sum(1 for a in actions if a.status == "moved")
        failed = sum(1 for a in actions if a.status == "failed")
        self._log(f"Done: {moved} moved, {failed} failed.", "success")
        self.btn_apply.setEnabled(False)

    def _on_apply_failed(self, error: str):
        self._toggle_ui_state(applying=False)
        self.progress_bar.setVisible(False)
        self._log(f"Apply failed: {error}", "error")
        QMessageBox.critical(self, "Apply Failed", error)

    def _undo_last(self):
        self._log("Undoing...", "info")
        undone = self.organizer.undo_last()
        if undone:
            self._log(f"Undone {len(undone)} moves.", "success")
            self.btn_undo.setEnabled(False)
            self.btn_apply.setEnabled(True)
        else: self._log("Nothing to undo.", "warning")

    def _cancel_operation(self):
        self._log("Cancelling...", "warning")
        self.organizer.cancel()
        if hasattr(self, 'worker') and self.worker.isRunning(): self.worker.quit(); self.worker.wait()
        if hasattr(self, 'apply_worker') and self.apply_worker.isRunning(): self.apply_worker.quit(); self.apply_worker.wait()
        self._toggle_ui_state(analyzing=False, applying=False)
        self.progress_bar.setVisible(False)

    def _toggle_ui_state(self, analyzing: bool = False, applying: bool = False):
        is_busy = analyzing or applying
        self.btn_analyze.setEnabled(not is_busy)
        self.btn_apply.setEnabled(not is_busy and not analyzing)
        self.btn_cancel.setEnabled(is_busy)
        self.drop_zone.setEnabled(not is_busy)

    def closeEvent(self, event):
        self.organizer.cancel()
        if hasattr(self, 'worker') and self.worker.isRunning(): self.worker.quit(); self.worker.wait()
        if hasattr(self, 'apply_worker') and self.apply_worker.isRunning(): self.apply_worker.quit(); self.apply_worker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())