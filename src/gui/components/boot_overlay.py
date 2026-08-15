"""
DesktopAI v2.0 — Boot Overlay
File: src/gui/components/boot_overlay.py
Short, non-blocking startup experience with real stage feedback.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect, QLabel, QProgressBar, QVBoxLayout, QWidget,
)

from gui.components.brand import LogoMark

_STAGES_PRE = ["Initializing DesktopAI", "Loading configuration"]


class _BootWorker(QThread):
    done = Signal(dict)

    def run(self):
        info = {"ai": "unknown", "files": 0}
        try:
            from infrastructure.ai.gateway import AIGateway
            info["ai"] = "ok" if AIGateway.health_check() else "down"
        except Exception:
            info["ai"] = "down"
        try:
            from infrastructure.storage.database import DB
            info["files"] = DB.get_stats().get("total_files", 0)
        except Exception:
            pass
        self.done.emit(info)


class BootOverlay(QWidget):
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._info = None
        self._worker_done = False
        self._dot_count = 0

        self.setStyleSheet("background: #0D0D12;")
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(10)

        lay.addWidget(self._centered(LogoMark(64)))

        title = QLabel("DesktopAI")
        title.setStyleSheet("color: #E8E8F0; font-size: 26px; font-weight: 700;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)

        tag = QLabel("Your files. Understood.")
        tag.setStyleSheet("color: #8B8BA8; font-size: 13px;")
        tag.setAlignment(Qt.AlignCenter)
        lay.addWidget(tag)

        lay.addSpacing(18)

        self.stage = QLabel(_STAGES_PRE[0])
        self.stage.setStyleSheet("color: #8B8BA8; font-size: 12px;")
        self.stage.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.stage)

        self.bar = QProgressBar()
        self.bar.setFixedWidth(260)
        self.bar.setFixedHeight(6)
        self.bar.setRange(0, 0)  # indeterminate
        self.bar.setStyleSheet("""
            QProgressBar { background: #1A1A24; border: none; border-radius: 3px; }
            QProgressBar::chunk { background: #8B5CF6; border-radius: 3px; }
        """)
        lay.addWidget(self.bar, 0, Qt.AlignCenter)

        self._fx = QGraphicsOpacityEffect(self)
        self._fx.setOpacity(1.0)
        self.setGraphicsEffect(self._fx)

        # Dot animation
        self._dot_timer = QTimer(self)
        self._dot_timer.setInterval(350)
        self._dot_timer.timeout.connect(self._tick_dots)
        self._dot_timer.start()

        # Stage 1 after a beat
        QTimer.singleShot(180, lambda: self.stage.setText(_STAGES_PRE[1]))

        # Hard cap so startup never hangs
        QTimer.singleShot(2500, self._maybe_finish_stages)

        self._worker = _BootWorker()
        self._worker.done.connect(self._on_worker)
        self._worker.start()

        self._post_worker: list = []
        self._post_index = 0
        self._step_timer = QTimer(self)
        self._step_timer.setInterval(320)
        self._step_timer.timeout.connect(self._step_post)

    def _centered(self, w: QWidget) -> QWidget:
        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignCenter)
        lay.addWidget(w)
        return wrap

    def _tick_dots(self):
        self._dot_count = (self._dot_count + 1) % 4
        base = self._base_text or "Working"
        self.stage.setText(base + "." * self._dot_count)

    _base_text: str = _STAGES_PRE[0]

    def _set_stage(self, text: str):
        self._base_text = text
        self.stage.setText(text)

    def _on_worker(self, info: dict):
        self._info = info
        self._worker_done = True
        self._maybe_finish_stages()

    def _maybe_finish_stages(self):
        if self._post_worker or not self._worker_done:
            if not self._worker_done:
                # Cap hit before worker returned: proceed with unknowns
                self._info = self._info or {"ai": "unknown", "files": 0}
                self._worker_done = True
            else:
                return
        info = self._info or {"ai": "unknown", "files": 0}
        ai_text = (
            "Checking local AI — connected" if info["ai"] == "ok"
            else "Checking local AI — not reachable (AI features limited)"
        )
        files = info.get("files", 0)
        file_text = (
            f"Loading file intelligence — {files} files known"
            if files else "Loading file intelligence"
        )
        self._post_worker = [ai_text, file_text, "Ready"]
        self._post_index = 0
        self._step_timer.start()

    def _step_post(self):
        if self._post_index < len(self._post_worker):
            self._set_stage(self._post_worker[self._post_index])
            self._post_index += 1
        else:
            self._step_timer.stop()
            self._dot_timer.stop()
            self._fade_out()

    def _fade_out(self):
        anim = QPropertyAnimation if False else None  # placeholder to avoid import churn
        from PySide6.QtCore import QPropertyAnimation
        self._fade = QPropertyAnimation(self._fx, b"opacity")
        self._fade.setDuration(250)
        self._fade.setStartValue(1.0)
        self._fade.setEndValue(0.0)
        self._fade.finished.connect(self._close)
        self._fade.start()

    def _close(self):
        self._dot_timer.stop()
        self._step_timer.stop()
        self.finished.emit()
        self.deleteLater()