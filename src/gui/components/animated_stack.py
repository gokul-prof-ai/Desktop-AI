"""
DesktopAI v2.0 — Animated Stacked Widget
File: src/gui/components/animated_stack.py

Clean fade transition between pages.
The previous version had a broken timer that never switched pages.
This version uses QTimer.singleShot correctly.
"""
from __future__ import annotations

from PySide6.QtWidgets import QStackedWidget, QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer


class AnimatedStackedWidget(QStackedWidget):
    """
    QStackedWidget with a smooth fade transition between pages.
    """

    DURATION = 200  # ms

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._animating = False

    def setCurrentIndex(self, index: int) -> None:
        """Switch to page `index` with a fade animation."""
        if index == self.currentIndex() or self._animating:
            # Fallback: force switch if not animating but same index requested
            if index != self.currentIndex():
                super().setCurrentIndex(index)
            return

        if index < 0 or index >= self.count():
            return

        current = self.currentWidget()
        target = self.widget(index)

        if current is None or target is None:
            super().setCurrentIndex(index)
            return

        self._animating = True

        # Fade out the current widget
        out_effect = QGraphicsOpacityEffect(current)
        current.setGraphicsEffect(out_effect)

        fade_out = QPropertyAnimation(out_effect, b"opacity", self)
        fade_out.setDuration(self.DURATION // 2)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.OutQuad)

        def _do_switch() -> None:
            """Called at midpoint — perform the actual page switch."""
            # Clean up outgoing widget effect
            current.setGraphicsEffect(None)

            # Switch the page
            super(AnimatedStackedWidget, self).setCurrentIndex(index)

            # Fade in the incoming widget
            in_effect = QGraphicsOpacityEffect(target)
            target.setGraphicsEffect(in_effect)
            in_effect.setOpacity(0.0)

            fade_in = QPropertyAnimation(in_effect, b"opacity", self)
            fade_in.setDuration(self.DURATION // 2)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.InQuad)

            def _done() -> None:
                target.setGraphicsEffect(None)
                self._animating = False

            fade_in.finished.connect(_done)
            fade_in.start()

        fade_out.finished.connect(_do_switch)
        fade_out.start()

        # Keep reference so animation isn't garbage collected
        self._active_anim = fade_out