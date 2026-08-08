"""
DesktopAI v2.0 — Animated Stacked Widget
File: src/gui/components/animated_stack.py

Provides smooth fade + slide transitions between pages.
"""
from __future__ import annotations
from PySide6.QtWidgets import QStackedWidget, QGraphicsOpacityEffect
from PySide6.QtCore import (
    QPropertyAnimation, QEasingCurve, Qt, QPoint, QParallelAnimationGroup
)


class AnimatedStackedWidget(QStackedWidget):
    """
    A QStackedWidget with smooth fade and slide transitions.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animation_duration = 300
        self._is_animating = False
    
    def setCurrentIndex(self, index: int):
        """Switch to a page with animation."""
        if index == self.currentIndex() or self._is_animating:
            return
        
        self._is_animating = True
        
        # Get current and next widgets
        current_widget = self.currentWidget()
        next_widget = self.widget(index)
        
        if not current_widget or not next_widget:
            super().setCurrentIndex(index)
            self._is_animating = False
            return
        
        # Setup fade effects
        current_effect = QGraphicsOpacityEffect(current_widget)
        current_widget.setGraphicsEffect(current_effect)
        
        next_effect = QGraphicsOpacityEffect(next_widget)
        next_widget.setGraphicsEffect(next_effect)
        next_effect.setOpacity(0.0)
        
        # Create animations
        fade_out = QPropertyAnimation(current_effect, b"opacity")
        fade_out.setDuration(self._animation_duration)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        
        fade_in = QPropertyAnimation(next_effect, b"opacity")
        fade_in.setDuration(self._animation_duration)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Slide animation for next widget
        slide = QPropertyAnimation(next_widget, b"pos")
        slide.setDuration(self._animation_duration)
        slide.setStartValue(QPoint(50, 0))
        slide.setEndValue(QPoint(0, 0))
        slide.setEasingCurve(QEasingCurve.OutCubic)
        
        # Group animations
        group = QParallelAnimationGroup(self)
        group.addAnimation(fade_out)
        group.addAnimation(fade_in)
        group.addAnimation(slide)
        
        # Switch page at midpoint
        def switch_page():
            super().setCurrentIndex(index)
        
        timer = self.startTimer(self._animation_duration // 2)
        def on_timer():
            self.killTimer(timer)
            switch_page()
        
        # Cleanup after animation
        def on_finished():
            self._is_animating = False
            current_widget.setGraphicsEffect(None)
            next_widget.setGraphicsEffect(None)
        
        group.finished.connect(on_finished)
        
        # Keep references
        current_widget._fade_anim = fade_out
        current_widget._fade_effect = current_effect
        next_widget._fade_anim = fade_in
        next_widget._fade_effect = next_effect
        next_widget._slide_anim = slide
        
        group.start()