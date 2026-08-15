"""
DesktopAI v2.0 — Watcher View (Monitoring Status)
File: src/gui/views/watcher_view.py
Communicates real watcher state; enable/disable with feedback.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core.logger import get_logger
from gui.components.widgets import (
    PrimaryButton, SecondaryButton, SectionHeader, StatusIndicator,
)

logger = get_logger(__name__)


class WatcherView(QWidget):
    def __init__(self, watcher_service=None, parent=None):
        super().__init__(parent)
        self.service = watcher_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(SectionHeader(
            "Folder Watcher",
            "Automatically monitor selected folders for changes.",
        ))

        hero = QFrame()
        hero.setObjectName("daCard")
        hero.setMinimumHeight(120)
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(20, 18, 20, 18)
        hl.setSpacing(10)

        self.status = StatusIndicator("Checking…", "info")
        hl.addWidget(self.status)

        self.folders_label = QLabel("")
        self.folders_label.setObjectName("daSectionSub")
        hl.addWidget(self.folders_label)

        btn_row = QHBoxLayout()
        self.toggle_btn = PrimaryButton("Enable Watcher")
        self.toggle_btn.clicked.connect(self._toggle)
        btn_row.addWidget(self.toggle_btn)
        btn_row.addStretch()
        hl.addLayout(btn_row)
        layout.addWidget(hero)

        watched = QFrame()
        watched.setObjectName("daCard")
        wl = QVBoxLayout(watched)
        wl.setContentsMargins(20, 16, 20, 16)
        wl.setSpacing(8)
        wt = QLabel("Monitored folders")
        wt.setObjectName("daSectionTitle")
        wl.addWidget(wt)
        self.folders_box = QVBoxLayout()
        self.folders_box.setSpacing(6)
        wl.addLayout(self.folders_box)
        wl.addStretch()
        layout.addWidget(watched, 1)

        self._reload()

    # ── State ────────────────────────────────────────────────────
    def _running(self) -> bool:
        if self.service is None:
            return False
        for attr in ("is_running", "running", "started"):
            val = getattr(self.service, attr, None)
            if callable(val):
                try:
                    return bool(val())
                except Exception:
                    continue
            if val is not None:
                return bool(val)
        return False

    def _folders(self) -> list:
        try:
            from infrastructure.config.settings import Settings
            val = getattr(getattr(Settings, "watcher", None), "folders", None)
            if val:
                return [str(f) for f in val]
        except Exception:
            pass
        try:
            from core.constants import WATCH_FOLDERS
            return [str(f) for f in WATCH_FOLDERS]
        except Exception:
            return []

    def _reload(self):
        running = self._running()
        if running:
            self.status.set_status("Watching", "ok")
            self.toggle_btn.setText("Pause Watcher")
        else:
            self.status.set_status("Watcher inactive", "warn")
            self.toggle_btn.setText("Enable Watcher")

        folders = self._folders()
        self.folders_label.setText(
            f"{len(folders)} folders monitored" if running else
            "Enable automatic monitoring to keep your library current."
        )

        while self.folders_box.count():
            item = self.folders_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not folders:
            none = QLabel("No folders configured yet.")
            none.setObjectName("daProgressText")
            self.folders_box.addWidget(none)
        for f in folders:
            row = QLabel(f"◦  {f}")
            row.setObjectName("daProgressText")
            self.folders_box.addWidget(row)

    def _toggle(self):
        try:
            if self._running():
                self.service.stop()
                self._toast("info", "Watcher paused", "Monitoring stopped.")
            else:
                self.service.start()
                self._toast("success", "Watcher enabled", "Monitoring your folders.")
        except Exception as exc:
            self._toast("error", "Watcher failed", str(exc))
        self._reload()

    def _toast(self, kind: str, title: str, msg: str):
        toasts = getattr(self.window(), "toasts", None)
        if toasts:
            getattr(toasts, f"show_{kind}")(title, msg)