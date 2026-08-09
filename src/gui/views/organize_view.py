"""
DesktopAI v2.0 — Organize View (theme-aware)
File: src/gui/views/organize_view.py
"""
from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QFileDialog,
)
from PySide6.QtCore import Qt
from gui.components.sound_button import SoundButton
from gui.viewmodels.organize_vm import OrganizeViewModel
from core.logger import get_logger

logger = get_logger(__name__)


class OrganizeView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent;")
        self.vm = OrganizeViewModel()
        self._target_folder = Path.home() / "DesktopAI_Organized"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        folder_layout = QHBoxLayout()
        folder_label = QLabel("Target Folder:")
        folder_label.setObjectName("StatusLabel")
        folder_layout.addWidget(folder_label)

        self.folder_input = QLineEdit(str(self._target_folder))
        self.folder_input.setObjectName("Input")
        self.folder_input.setReadOnly(True)
        folder_layout.addWidget(self.folder_input, 1)

        browse = SoundButton("Browse")
        browse.setObjectName("SecondaryButton")
        browse.setFixedWidth(100)
        browse.clicked.connect(self._browse_folder)
        folder_layout.addWidget(browse)
        layout.addLayout(folder_layout)

        self.status_label = QLabel("Scan a folder in Home to preview the plan here.")
        self.status_label.setObjectName("StatusLabel")
        layout.addWidget(self.status_label)

        self.table = QTableWidget()
        self.table.setObjectName("Table")
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File Name", "Category", "Confidence", "Status"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for col in (1, 2, 3):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_undo = SoundButton("Undo Last Batch")
        self.btn_undo.setObjectName("DangerButton")
        self.btn_undo.setFixedSize(160, 44)
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self.vm.start_undo)
        btn_layout.addWidget(self.btn_undo)

        self.btn_apply = SoundButton("Apply Organization")
        self.btn_apply.setObjectName("PrimaryButton")
        self.btn_apply.setFixedSize(180, 44)
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(lambda: self.vm.start_apply(self._target_folder))
        btn_layout.addWidget(self.btn_apply)
        layout.addLayout(btn_layout)

        self.vm.apply_started.connect(self._on_apply_started)
        self.vm.apply_progress.connect(lambda d, t: self.status_label.setText(f"Moving files... ({d}/{t})"))
        self.vm.file_moved_signal.connect(self._on_file_moved)
        self.vm.apply_completed.connect(self._on_apply_completed)
        self.vm.apply_failed.connect(self._on_error)
        self.vm.undo_completed.connect(self._on_undo_completed)
        self.vm.undo_failed.connect(self._on_error)

    def load_results(self, results: list):
        self.vm.set_results(results)
        self.table.setRowCount(len(results))
        for row, r in enumerate(results):
            self.table.setItem(row, 0, QTableWidgetItem(r.file_info.filename))
            self.table.setItem(row, 1, QTableWidgetItem(r.category))
            pct = int(r.confidence * 100)
            item = QTableWidgetItem(f"{pct}%")
            item.setForeground(Qt.green if pct >= 80 else (Qt.yellow if pct >= 50 else Qt.red))
            self.table.setItem(row, 2, item)
            self.table.setItem(row, 3, QTableWidgetItem("Pending"))
        self.btn_apply.setEnabled(len(results) > 0)
        self.btn_undo.setEnabled(self.vm.can_undo)
        self.status_label.setText(f"Ready to organize {len(results)} files.")

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Target Folder", str(self._target_folder))
        if folder:
            self._target_folder = Path(folder)
            self.folder_input.setText(str(self._target_folder))

    def _on_apply_started(self):
        self.btn_apply.setEnabled(False)
        self.btn_undo.setEnabled(False)
        self.status_label.setText("Applying organization plan...")

    def _on_file_moved(self, source: str, target: str):
        for row in range(self.table.rowCount()):
            it = self.table.item(row, 0)
            if it and it.text() == source:
                self.table.setItem(row, 3, QTableWidgetItem("Moved ✓"))
                break

    def _on_apply_completed(self, s, f, k, batch_id):
        self.btn_apply.setEnabled(self.vm.has_results)
        self.btn_undo.setEnabled(s > 0)
        self.status_label.setText(f"Done! {s} moved, {f} failed, {k} skipped.")

    def _on_undo_completed(self, count, batch_id):
        for row in range(self.table.rowCount()):
            self.table.setItem(row, 3, QTableWidgetItem("Undone"))
        self.btn_undo.setEnabled(False)
        self.status_label.setText(f"Undo complete — {count} files restored.")

    def _on_error(self, msg):
        self.btn_apply.setEnabled(self.vm.has_results)
        self.status_label.setText(f"Error: {msg}")