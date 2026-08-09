"""
DesktopAI v2.0
Watcher workspace.

Start/stop the FolderWatcher and see new files appear in real time.
"""
from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import Qt, QMetaObject, Q_ARG
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QFrame,
)

from core import config


class WatcherView(QWidget):

    def __init__(self):
        super().__init__()
        self._watcher = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Info
        info = QLabel(
            "Monitor folders for new files in real time.\n"
            "Default folders: Downloads and Desktop.\n"
            "Override via DESKTOP_AI_WATCH_FOLDERS env var (colon-separated)."
        )
        info.setObjectName("PageSubtitle")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Controls
        ctrl_row = QHBoxLayout()
        self.btn_toggle = QPushButton("▶  Start Watcher")
        self.btn_toggle.setObjectName("PrimaryButton")
        self.btn_toggle.clicked.connect(self._toggle)
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setStyleSheet("color: #EF4444; font-weight: 600;")
        ctrl_row.addWidget(self.btn_toggle)
        ctrl_row.addWidget(self.status_label)
        ctrl_row.addStretch()

        btn_clear = QPushButton("Clear Log")
        btn_clear.setObjectName("SecondaryButton")
        btn_clear.clicked.connect(self._clear)
        ctrl_row.addWidget(btn_clear)
        layout.addLayout(ctrl_row)

        # Watched folders display
        folders_text = "  •  ".join(str(f) for f in config.WATCH_FOLDERS)
        self.folders_label = QLabel(f"Watching: {folders_text}")
        self.folders_label.setStyleSheet("color: #71717A; font-size: 12px;")
        self.folders_label.setWordWrap(True)
        layout.addWidget(self.folders_label)

        # Log card
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)

        log_header = QLabel("Detected files")
        log_header.setStyleSheet("font-weight: 600; color: #A1A1AA;")
        card_layout.addWidget(log_header)

        self.log_list = QListWidget()
        card_layout.addWidget(self.log_list)
        layout.addWidget(card, 1)

    # ── Slots ─────────────────────────────────────────────────────────

    def _toggle(self):
        if self._watcher is None or not self._watcher._started:
            self._start()
        else:
            self._stop()

    def _start(self):
        from watcher.watcher import FolderWatcher
        self._watcher = FolderWatcher(on_new_file=self._on_new_file)
        self._watcher.start()
        self.btn_toggle.setText("⏹  Stop Watcher")
        self.status_label.setText("Status: Running ✅")
        self.status_label.setStyleSheet("color: #10B981; font-weight: 600;")

    def _stop(self):
        if self._watcher:
            self._watcher.stop()
            self._watcher = None
        self.btn_toggle.setText("▶  Start Watcher")
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("color: #EF4444; font-weight: 600;")

    def _on_new_file(self, path: Path):
        """Called from watcher background thread — must be thread-safe."""
        text = f"[{time.strftime('%H:%M:%S')}]  {path}"
        QMetaObject.invokeMethod(
            self.log_list, "addItem",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, text),
        )

    def _clear(self):
        self.log_list.clear()

    def closeEvent(self, event):
        self._stop()
        super().closeEvent(event)
