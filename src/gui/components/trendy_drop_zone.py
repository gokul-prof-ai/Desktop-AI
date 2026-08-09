"""
DesktopAI v2.0
App Shell folder drop zone.

Simple, reliable and theme-friendly.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QLabel,
    QVBoxLayout,
)


class MagneticDropZone(QFrame):
    """
    Folder selection/drop component.

    The class name is retained for compatibility with the existing
    HomeView implementation.
    """

    folder_selected = Signal(str)
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("Card")
        self.setAcceptDrops(True)
        self.setMinimumSize(480, 260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Scan a folder")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 20px; font-weight: 600;"
        )

        subtitle = QLabel(
            "Drop a folder here or choose one from your computer."
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)

        button = QLabel(
            "Click anywhere to choose a folder"
        )
        button.setAlignment(Qt.AlignCenter)
        button.setObjectName("Muted")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(button)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]

        if not paths:
            return

        folders = [
            path
            for path in paths
            if self._is_directory(path)
        ]

        if folders:
            self.files_dropped.emit(folders)
            self.folder_selected.emit(folders[0])

        event.acceptProposedAction()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Scan",
        )

        if folder:
            self.folder_selected.emit(folder)

    @staticmethod
    def _is_directory(path: str) -> bool:
        from pathlib import Path

        return Path(path).is_dir()