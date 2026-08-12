"""
DesktopAI v2.0 — Drop Zone Component
File: src/gui/components/trendy_drop_zone.py
"""
from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QFrame, QLabel, QVBoxLayout


class MagneticDropZone(QFrame):
    """
    Folder drop/browse zone. Uses QFrame#DropZone objectName
    so the dashed-border rule in app_shell.qss applies correctly.
    """

    folder_selected = Signal(str)
    files_dropped = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # Must match QFrame#DropZone rule in app_shell.py
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumSize(480, 220)
        self.setMaximumSize(680, 260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 28, 40, 28)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        # Icon — uses objectName so QSS can color it
        self._icon = QLabel("⊞")
        self._icon.setObjectName("DropZoneIcon")
        self._icon.setAlignment(Qt.AlignCenter)

        # Title — uses SubHeading token (theme-aware)
        title = QLabel("Drop folder here")
        title.setObjectName("SubHeading")
        title.setAlignment(Qt.AlignCenter)

        # Subtitle
        subtitle = QLabel("or click to browse your computer")
        subtitle.setObjectName("Muted")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)

        layout.addWidget(self._icon)
        layout.addSpacing(4)
        layout.addWidget(title)
        layout.addWidget(subtitle)

    # ── Drag ──────────────────────────────────────────────────────

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            self._set_drag_active(True)
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self._set_drag_active(False)

    def dropEvent(self, event) -> None:
        self._set_drag_active(False)
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

    def _set_drag_active(self, active: bool) -> None:
        """Toggle the drag-active property so QSS :hover rule fires."""
        self.setProperty("dragActive", active)
        self.style().unpolish(self)
        self.style().polish(self)