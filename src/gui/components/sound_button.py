"""
DesktopAI v2.0 — Animated Sound Button
File: src/gui/components/sound_button.py
Hover glow + click pulse + interactive sounds, layout-safe (opacity FX).
"""
from __future__ import annotations
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QPushButton, QGraphicsOpacityEffect
from gui.utils.sounds import SOUNDS


class SoundButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor) if (Qt := __import__("PySide6.QtCore", fromlist=["Qt"]).Qt) else None
        self._fx = QGraphicsOpacityEffect(self)
        self._fx.setOpacity(1.0)
        self.setGraphicsEffect(self._fx)
        self._anim = QPropertyAnimation(self._fx, b"opacity")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def _pulse_to(self, value: float):
        self._anim.stop()
        self._anim.setStartValue(self._fx.opacity())
        self._anim.setEndValue(value)
        self._anim.start()

    def enterEvent(self, event):
        SOUNDS.play_hover()
        self._pulse_to(0.85)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._pulse_to(1.0)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        SOUNDS.play_click()
        self._pulse_to(0.7)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pulse_to(1.0)
        super().mouseReleaseEvent(event)