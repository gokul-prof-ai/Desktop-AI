"""
DesktopAI v2.0 — Organize View
File: src/gui/views/organize_view.py

Review the AI plan, choose a target folder, Apply, and Undo.
"""
from __future__ import annotations
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLineEdit, QFileDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.logger import get_logger
from gui.viewmodels.organize_vm import OrganizeViewModel

logger = get_logger(__name__)


class OrganizeView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        self.vm = OrganizeViewModel()
        self._target_folder = Path.home() / "DesktopAI_Organized"
        self._moved: dict[str, str] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # ── Target folder row ─────────────────────────────────────
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Target Folder:")
        folder_label.setStyleSheet("color: #A1A1AA; font-size: 14px;")
        folder_layout.addWidget(folder_label)

        self.folder_input = QLineEdit(str(self._target_folder))
        self.folder_input.setReadOnly(True)
        self.folder_input.setStyleSheet("""
            QLineEdit {
                background-color: #0A0A0F; border: 1px solid #2A2A35;
                border-radius: 8px; color: #FFFFFF; padding: 8px 12px;
            }
        """)
        folder_layout.addWidget(self.folder_input, 1)

        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(100)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A1A24; color: #A1A1AA;
                border: 1px solid #2A2A35; border-radius: 8px; font-weight: 600;
            }
            QPushButton:hover { background-color: #2A2A35; color: #FFFFFF; }
        """)
        browse_btn.clicked.connect(self._browse_folder)
        folder_layout.addWidget(browse_btn)
        layout.addLayout(folder_layout)

        # ── Status label ──────────────────────────────────────────
        self.status_label = QLabel("Scan a folder in Home to preview the plan here.")
        self.status_label.setStyleSheet("color: #71717A; font-size: 14px;")
        layout.addWidget(self.status_label)

        # ── Plan table ────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File Name", "Category", "Confidence", "Status"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0A0A0F; border: 1px solid #1A1A24;
                border-radius: 12px; gridline-color: #1A1A24;
                color: #E4E4E7; font-size: 13px;
            }
            QTableWidget::item { padding: 10px 16px; border-bottom: 1px solid #1A1A24; }
            QHeaderView::section {
                background-color: #0A0A0F; color: #71717A; padding: 12px 16px;
                border: none; border-bottom: 2px solid #27272A; font-weight: 600;
                text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;
            }
        """)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table, 1)

        # ── Action buttons ────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_undo = QPushButton("Undo Last Batch")
        self.btn_undo.setFixedSize(160, 44)
        self.btn_undo.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #F87171;
                border: 1px solid #F87171; border-radius: 8px; font-weight: 600;
            }
            QPushButton:hover { background-color: rgba(248, 113, 113, 0.1); }
            QPushButton:disabled { color: #52525B; border-color: #52525B; }
        """)
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self._on_undo_clicked)
        btn_layout.addWidget(self.btn_undo)

        self.btn_apply = QPushButton("Apply Organization")
        self.btn_apply.setFixedSize(180, 44)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B5CF6, stop:1 #3B82F6);
                color: white; border: none; border-radius: 8px; font-weight: 600;
            }
            QPushButton:hover { opacity: 0.9; }
            QPushButton:disabled { background: #2A2A35; color: #71717A; }
        """)
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        btn_layout.addWidget(self.btn_apply)

        layout.addLayout(btn_layout)

        # ── ViewModel signals ─────────────────────────────────────
        self.vm.apply_started.connect(self._on_apply_started)
        self.vm.apply_progress.connect(self._on_progress)
        self.vm.file_moved_signal.connect(self._on_file_moved)
        self.vm.apply_completed.connect(self._on_apply_completed)
        self.vm.apply_failed.connect(self._on_apply_failed)
        self.vm.undo_started.connect(lambda: self.status_label.setText("Undoing batch..."))
        self.vm.undo_completed.connect(self._on_undo_completed)
        self.vm.undo_failed.connect(self._on_apply_failed)

    # ── Public API (called by MainWindow) ─────────────────────────
    def load_results(self, results: list) -> None:
        self.vm.set_results(results)
        self._moved.clear()
        self.table.setRowCount(len(results))
        for row, result in enumerate(results):
            self.table.setItem(row, 0, QTableWidgetItem(result.file_info.filename))
            self.table.setItem(row, 1, QTableWidgetItem(result.category))
            conf_pct = int(result.confidence * 100)
            conf_item = QTableWidgetItem(f"{conf_pct}%")
            if conf_pct >= 80:
                conf_item.setForeground(Qt.green)
            elif conf_pct >= 50:
                conf_item.setForeground(Qt.yellow)
            else:
                conf_item.setForeground(Qt.red)
            self.table.setItem(row, 2, conf_item)
            self.table.setItem(row, 3, QTableWidgetItem("Pending"))
        self.btn_apply.setEnabled(len(results) > 0)
        self.btn_undo.setEnabled(self.vm.can_undo)
        self.status_label.setText(f"Ready to organize {len(results)} files.")

    # ── Slots ─────────────────────────────────────────────────────
    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Target Folder", str(self._target_folder)
        )
        if folder:
            self._target_folder = Path(folder)
            self.folder_input.setText(str(self._target_folder))

    def _on_apply_clicked(self):
        self.vm.start_apply(self._target_folder)

    def _on_undo_clicked(self):
        self.vm.start_undo()

    def _on_apply_started(self):
        self.btn_apply.setEnabled(False)
        self.btn_undo.setEnabled(False)
        self.status_label.setText("Applying organization plan...")

    def _on_progress(self, done: int, total: int):
        self.status_label.setText(f"Moving files... ({done}/{total})")

    def _on_file_moved(self, source_name: str, target_path: str):
        self._moved[source_name] = target_path
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text() == source_name:
                self.table.setItem(row, 3, QTableWidgetItem("Moved ✓"))
                break

    def _on_apply_completed(self, success: int, failed: int, skipped: int, batch_id: str):
        self.btn_apply.setEnabled(self.vm.has_results)
        self.btn_undo.setEnabled(success > 0)
        self.status_label.setText(
            f"Done! {success} moved, {failed} failed, {skipped} skipped."
        )

    def _on_apply_failed(self, error: str):
        self.btn_apply.setEnabled(self.vm.has_results)
        self.status_label.setText(f"Error: {error}")

    def _on_undo_completed(self, count: int, batch_id: str):
        for row in range(self.table.rowCount()):
            self.table.setItem(row, 3, QTableWidgetItem("Undone"))
        self.btn_undo.setEnabled(False)
        self.status_label.setText(f"Undo complete — {count} files restored.")