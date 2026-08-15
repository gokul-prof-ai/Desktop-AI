"""
DesktopAI v2.0 — Toast Notification System
File: src/gui/components/toast.py

Overlay toasts anchored top-right of the main window.
Auto-dismiss (4s), manual close, fade in/out, vertical stacking.
"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from gui.components.widgets import IconButton

_KIND_ICON = {"success": ("✓", "Ok"), "error": ("✕", "Err"), "warning": ("!", "Warn"), "info": ("◈", "Info")}


class _Toast(QFrame):
    def __init__(self, kind: str, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setObjectName("daToast")
        self.setFixedWidth(340)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 8, 12)
        lay.setSpacing(10)

        icon, icon_kind = _KIND_ICON.get(kind, _KIND_ICON["info"])
        ic = QLabel(icon)
        ic.setObjectName(f"daToastIcon{icon_kind}")
        lay.addWidget(ic)

        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("daToastTitle")
        col.addWidget(t)
        if message:
            m = QLabel(message)
            m.setObjectName("daToastMsg")
            m.setWordWrap(True)
            col.addWidget(m)
        lay.addLayout(col, 1)

        close = IconButton("✕", "Dismiss")
        close.clicked.connect(self.dismiss)
        lay.addWidget(close, 0, Qt.AlignTop)

        self._fx = QGraphicsOpacityEffect(self)
        self._fx.setOpacity(0.0)
        self.setGraphicsEffect(self._fx)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(4000)
        self._timer.timeout.connect(self.dismiss)

    def show_event_later(self):
        anim = QPropertyAnimation(self._fx, b"opacity")
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        self._show_anim = anim
        anim.start()
        self._timer.start()

    def dismiss(self):
        self._timer.stop()
        anim = QPropertyAnimation(self._fx, b"opacity")
        anim.setDuration(150)
        anim.setStartValue(self._fx.opacity())
        anim.setEndValue(0.0)
        anim.finished.connect(self.deleteLater)
        self._hide_anim = anim
        anim.start()


class ToastManager:
    """Owns toast stacking for one anchor widget (the MainWindow)."""

    def __init__(self, anchor: QWidget):
        self._anchor = anchor
        self._active: list[_Toast] = []

    def show(self, kind: str, title: str, message: str = ""):
        toast = _Toast(kind, title, message, self._anchor)
        toast.show()
        self._active.append(toast)
        self._relayout()
        toast.show_event_later()
        toast.destroyed.connect(lambda *a, t=toast: self._forget(t))

    def show_success(self, title: str, message: str = ""):
        self.show("success", title, message)

    def show_error(self, title: str, message: str = ""):
        self.show("error", title, message)

    def show_warning(self, title: str, message: str = ""):
        self.show("warning", title, message)

    def show_info(self, title: str, message: str = ""):
        self.show("info", title, message)

    def _forget(self, toast):
        if toast in self._active:
            self._active.remove(toast)
        self._relayout()

    def _relayout(self):
        y = 70
        for toast in reversed(self._active):
            toast.move(self._anchor.width() - toast.width() - 16, y)
            y += toast.sizeHint().height() + 10