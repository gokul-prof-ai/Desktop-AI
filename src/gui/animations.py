"""
DesktopAI v2.0 — Animation Utilities
File: src/gui/animations.py

Provides reusable animation effects for the GUI.
All animations use Qt's property animation system for smooth, hardware-accelerated effects.
"""
from __future__ import annotations
from PySide6.QtCore import (
    QPropertyAnimation, QEasingCurve, QVariantAnimation, 
    QObject, Signal, QParallelAnimationGroup, QSequentialAnimationGroup
)
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QRadialGradient
from PySide6.QtCore import Qt, QRectF, QTimer
import math


class FadeEffect(QGraphicsOpacityEffect):
    """
    Fade in/out effect for widgets.
    Usage:
        effect = FadeEffect(widget)
        effect.fade_in(duration=300)
    """
    def __init__(self, widget: QWidget) -> None:
        super().__init__(widget)
        self._widget = widget
        self.setOpacity(0.0)
        widget.setGraphicsEffect(self)
    
    def fade_in(self, duration: int = 300) -> None:
        """Fade the widget in over the specified duration (ms)."""
        anim = QPropertyAnimation(self, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()
        self._fade_anim = anim  # Keep reference to prevent garbage collection
    
    def fade_out(self, duration: int = 300) -> None:
        """Fade the widget out over the specified duration (ms)."""
        anim = QPropertyAnimation(self, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()
        self._fade_anim = anim


class PageTransition:
    """
    Smooth page transition effect for QStackedWidget.
    Combines fade + slide for a premium feel.
    """
    @staticmethod
    def transition(widget: QWidget, duration: int = 400) -> None:
        """
        Apply a fade-in + slide-up transition to a widget.
        Call this when a new page is shown in QStackedWidget.
        """
        # Fade effect
        fade = FadeEffect(widget)
        fade.fade_in(duration)
        
        # Slide effect (move widget up slightly during fade-in)
        slide = QPropertyAnimation(widget, b"pos")
        slide.setDuration(duration)
        start_pos = widget.pos()
        slide.setStartValue(start_pos + __import__('PySide6.QtCore').QtCore.QPoint(0, 20))
        slide.setEndValue(start_pos)
        slide.setEasingCurve(QEasingCurve.Type.OutCubic)
        slide.start()
        
        # Keep references
        widget._transition_fade = fade
        widget._transition_slide = slide


class AIPulseWidget(QWidget):
    """
    The signature "AI Pulse" animation — a breathing ring around a button.
    Idle: Slow blue pulse
    Thinking: Faster cyan pulse
    Done: Green pulse then fade
    """
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._phase = 0.0  # 0.0 to 1.0 for animation cycle
        self._state = "idle"  # "idle", "thinking", "done"
        self._opacity = 0.6
        
        # Animation timer (60 FPS)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_animation)
        self._timer.start(16)  # ~60 FPS
        
        # Colors for each state
        self._colors = {
            "idle": QColor("#4F8EF7"),      # Blue
            "thinking": QColor("#00C4FF"),  # Cyan
            "done": QColor("#34D399"),      # Green
        }
    
    def set_state(self, state: str) -> None:
        """Set the pulse state: 'idle', 'thinking', or 'done'."""
        self._state = state
        self.update()
    
    def _update_animation(self) -> None:
        """Update the animation phase."""
        speed = 0.02 if self._state == "idle" else 0.05
        self._phase = (self._phase + speed) % 1.0
        self.update()
    
    def paintEvent(self, event) -> None:
        """Draw the pulsing ring."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate ring size based on phase
        max_radius = min(self.width(), self.height()) / 2
        min_radius = max_radius * 0.85
        
        # Pulse expands and contracts
        pulse = math.sin(self._phase * 2 * math.pi) * 0.5 + 0.5
        radius = min_radius + (max_radius - min_radius) * pulse
        
        # Opacity fades as it expands
        opacity = self._opacity * (1.0 - pulse * 0.5)
        
        color = self._colors.get(self._state, self._colors["idle"])
        color.setAlphaF(opacity)
        
        # Draw the ring
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        
        center = QRectF(self.rect()).center()
        painter.drawEllipse(center, radius, radius)


class HoverAnimator(QObject):
    """
    Smooth color transition on hover for widgets.
    Automatically detects enter/leave events and animates background color.
    """
    def __init__(self, widget: QWidget, normal_color: str, hover_color: str) -> None:
        super().__init__(widget)
        self._widget = widget
        self._normal = QColor(normal_color)
        self._hover = QColor(hover_color)
        self._current = self._normal
        
        # Install event filter to catch hover events
        widget.installEventFilter(self)
        
        # Animation
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.valueChanged.connect(self._update_color)
    
    def eventFilter(self, obj, event) -> bool:
        """Intercept hover events."""
        if obj == self._widget:
            if event.type() == event.Type.Enter:
                self._animate_to(self._hover)
            elif event.type() == event.Type.Leave:
                self._animate_to(self._normal)
        return super().eventFilter(obj, event)
    
    def _animate_to(self, target: QColor) -> None:
        """Animate from current color to target."""
        self._anim.stop()
        self._anim.setStartValue(self._current)
        self._anim.setEndValue(target)
        self._anim.start()
    
    def _update_color(self, color: QColor) -> None:
        """Update the widget's background color."""
        self._current = color
        self._widget.setStyleSheet(f"background-color: {color.name()};")


class ToastNotification(QWidget):
    """
    Non-blocking notification that slides in from the bottom-right.
    Auto-dismisses after a few seconds.
    """
    def __init__(self, message: str, level: str = "info", parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Colors based on level
        colors = {
            "info": "#4F8EF7",
            "success": "#34D399",
            "warning": "#FBBF24",
            "error": "#F87171",
        }
        color = colors.get(level, colors["info"])
        
        # Style
        self.setStyleSheet(f"""
            QWidget {{
                background-color: #1A1A24;
                border: 2px solid {color};
                border-radius: 12px;
                padding: 16px 24px;
            }}
            QLabel {{
                color: #E8E8F0;
                font-size: 14px;
            }}
        """)
        
        # Layout
        from PySide6.QtWidgets import QVBoxLayout, QLabel
        layout = QVBoxLayout(self)
        label = QLabel(message)
        layout.addWidget(label)
        
        self.resize(300, 80)
        
        # Slide-in animation
        self._slide_anim = QPropertyAnimation(self, b"pos")
        self._slide_anim.setDuration(400)
        self._slide_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        
        # Fade effect
        self._fade = FadeEffect(self)
        
        # Auto-dismiss after 3 seconds
        QTimer.singleShot(3000, self._dismiss)
    
    def show_at(self, x: int, y: int) -> None:
        """Show the toast at the specified screen position."""
        self.move(x, y)
        self._slide_anim.setStartValue(self.pos() + __import__('PySide6.QtCore').QtCore.QPoint(0, 50))
        self._slide_anim.setEndValue(self.pos())
        self._slide_anim.start()
        self._fade.fade_in(300)
        self.show()
    
    def _dismiss(self) -> None:
        """Fade out and close."""
        self._fade.fade_out(300)
        QTimer.singleShot(300, self.close)