"""
DesktopAI v2.0 — Drop Zone Component
File: src/gui/components/trendy_drop_zone.py

App Shell UI drop zone. Dashed border, hover highlight, clean typography.
"""
from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QFrame, QLabel, QVBoxLayout


class MagneticDropZone(QFrame):
    """
    Folder drop zone. Styled via QFrame#DropZone in app_shell.py.
    """

    folder_selected = Signal(str)
    files_dropped = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumSize(460, 220)
        self.setMaximumSize(640, 280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("⊞")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 32px; color: #6C6C70;")
        layout.addWidget(icon)

        title = QLabel("Drop folder here")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #F5F5F7;"
        )
        layout.addWidget(title)

        sub = QLabel("or click to browse your computer")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("font-size: 13px; color: #6C6C70;")
        layout.addWidget(sub)

        self._icon = icon

    # ── Drag events ────────────────────────────────────────────────

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            self._set_hover(True)
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self._set_hover(False)

    def dropEvent(self, event) -> None:
        self._set_hover(False)
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        folders = [p for p in paths if Path(p).is_dir()]
        if folders:
            self.files_dropped.emit(folders)
            self.folder_selected.emit(folders[0])
        event.acceptProposedAction()

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self.folder_selected.emit(folder)

    def _set_hover(self, active: bool) -> None:
        """Visual feedback during drag — update icon color."""
        color = "#0A84FF" if active else "#6C6C70"
        self._icon.setStyleSheet(f"font-size: 32px; color: {color};")