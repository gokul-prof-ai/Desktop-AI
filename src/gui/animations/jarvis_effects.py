"""
DesktopAI v2.0 — Jarvis HUD Animation Effects
File: src/gui/animations/jarvis_effects.py

Signature visual elements that make the app feel alive:
- JarvisOrb: Rotating rings with pulsing core (replaces AIPulse)
- ScanLineEffect: Horizontal scan line across panels
- DataTicker: Scrolling data text like a HUD readout
- ParticleField: Background floating particles
- GlowBorder: Animated glowing borders on widgets
"""
from __future__ import annotations
import math
import random
from PySide6.QtCore import (
    Qt, QRectF, QPointF, QTimer, QPropertyAnimation,
    QEasingCurve, QObject, Signal
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QRadialGradient, QLinearGradient,
    QFont, QBrush, QConicalGradient
)
from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect


# ═══════════════════════════════════════════════════════════════════
# JARVIS ORB — Rotating rings with pulsing core
# ═══════════════════════════════════════════════════════════════════
class JarvisOrb(QWidget):
    """
    The signature Jarvis element: concentric rotating rings around
    a pulsing cyan core. Changes appearance based on state.
    
    States:
    - idle: Slow rotation, gentle pulse, cyan
    - thinking: Faster rotation, amber color, intense pulse
    - processing: Very fast rotation, multiple rings, cyan
    - complete: Green glow, slow rotation, steady
    - error: Red glow, erratic rotation
    """
    
    def __init__(self, parent: QWidget = None, size: int = 120) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._size = size
        self._phase = 0.0
        self._ring_phases = [0.0, 0.0, 0.0]
        self._state = "idle"
        self._core_pulse = 0.0
        
        # State-specific colors
        self._state_colors = {
            "idle":       QColor("#00D4FF"),
            "thinking":   QColor("#FFB300"),
            "processing": QColor("#00FFFF"),
            "complete":   QColor("#00E676"),
            "error":      QColor("#FF5252"),
        }
        
        # Animation timer (60 FPS)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)
    
    def set_state(self, state: str) -> None:
        """Change the orb's visual state."""
        if state in self._state_colors:
            self._state = state
            self.update()
    
    def _tick(self) -> None:
        """Update animation phases."""
        # Rotation speeds per state
        speeds = {
            "idle":       0.008,
            "thinking":   0.025,
            "processing": 0.05,
            "complete":   0.005,
            "error":      0.04,
        }
        speed = speeds.get(self._state, 0.008)
        
        self._phase = (self._phase + speed) % 1.0
        self._core_pulse = (math.sin(self._phase * 2 * math.pi) + 1) / 2
        
        # Each ring rotates at a different speed/direction
        self._ring_phases[0] = (self._ring_phases[0] + speed * 1.0) % 1.0
        self._ring_phases[1] = (self._ring_phases[1] - speed * 0.7) % 1.0
        self._ring_phases[2] = (self._ring_phases[2] + speed * 1.3) % 1.0
        
        self.update()
    
    def paintEvent(self, event) -> None:
        """Draw the orb."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        center = QPointF(self._size / 2, self._size / 2)
        color = self._state_colors.get(self._state, self._state_colors["idle"])
        
        # ── Outer glow ─────────────────────────────────────────
        glow_radius = self._size / 2
        glow = QRadialGradient(center, glow_radius)
        glow_color = QColor(color)
        glow_color.setAlphaF(0.15 + self._core_pulse * 0.1)
        glow.setColorAt(0.0, glow_color)
        glow.setColorAt(0.5, QColor(color.red(), color.green(), color.blue(), 30))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(center, glow_radius, glow_radius)
        
        # ── Rotating rings ─────────────────────────────────────
        ring_specs = [
            (0.85, 2.0, 0.7),   # (radius_ratio, thickness, alpha)
            (0.70, 1.5, 0.5),
            (0.55, 1.0, 0.4),
        ]
        
        for i, (radius_ratio, thickness, alpha) in enumerate(ring_specs):
            radius = self._size / 2 * radius_ratio
            ring_color = QColor(color)
            ring_color.setAlphaF(alpha)
            
            pen = QPen(ring_color)
            pen.setWidthF(thickness)
            pen.setStyle(Qt.PenStyle.DashLine if i > 0 else Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            # Rotate the ring
            painter.save()
            painter.translate(center)
            painter.rotate(self._ring_phases[i] * 360)
            painter.translate(-center)
            
            painter.drawEllipse(center, radius, radius)
            painter.restore()
        
        # ── Core (pulsing center) ──────────────────────────────
        core_radius = self._size / 2 * 0.25
        core_size = core_radius * (0.8 + self._core_pulse * 0.4)
        
        core_gradient = QRadialGradient(center, core_size)
        core_color = QColor(color)
        core_color.setAlphaF(0.9)
        core_gradient.setColorAt(0.0, QColor(255, 255, 255, 255))
        core_gradient.setColorAt(0.3, core_color)
        core_gradient.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(core_gradient))
        painter.drawEllipse(center, core_size, core_size)


# ═══════════════════════════════════════════════════════════════════
# SCAN LINE — Horizontal scanning effect
# ═══════════════════════════════════════════════════════════════════
class ScanLineEffect(QWidget):
    """A horizontal scan line that moves vertically across a widget."""
    
    def __init__(self, parent: QWidget = None, color: str = "#00D4FF") -> None:
        super().__init__(parent)
        if parent:
            self.setGeometry(parent.rect())
            self.setParent(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._color = QColor(color)
        self._position = 0.0  # 0.0 to 1.0 (top to bottom)
        self._speed = 0.003
        self._active = False
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
    
    def start(self) -> None:
        """Begin the scan animation."""
        self._active = True
        self._position = 0.0
        self.show()
        self._timer.start(16)
    
    def stop(self) -> None:
        """Stop the scan animation."""
        self._active = False
        self._timer.stop()
        self.hide()
    
    def _tick(self) -> None:
        self._position += self._speed
        if self._position > 1.0:
            self._position = 0.0
        self.update()
    
    def paintEvent(self, event) -> None:
        if not self._active:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        y = self.height() * self._position
        line_height = 2
        
        # Gradient line with fade
        gradient = QLinearGradient(0, y - 20, 0, y + 20)
        gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
        gradient.setColorAt(0.5, self._color)
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(0, y - 20, self.width(), 40)
        
        # Bright center line
        painter.setPen(QPen(self._color, line_height))
        painter.drawLine(0, y, self.width(), y)


# ═══════════════════════════════════════════════════════════════════
# DATA TICKER — Scrolling HUD text readout
# ═══════════════════════════════════════════════════════════════════
class DataTicker(QWidget):
    """
    Scrolling text readout like a HUD status display.
    Shows system-like messages cycling through.
    """
    
    def __init__(self, parent: QWidget = None, width: int = 400) -> None:
        super().__init__(parent)
        self.setFixedHeight(24)
        self.setMinimumWidth(width)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._messages = [
            "SYSTEM ONLINE",
            "NEURAL NETWORK: ACTIVE",
            "SCANNING LOCAL FILES...",
            "AI GATEWAY: CONNECTED",
            "MEMORY: OPTIMIZED",
            "AWAITING COMMAND",
            "STATUS: OPERATIONAL",
            "SECURITY: VERIFIED",
        ]
        self._current_index = 0
        self._offset = 0.0
        self._color = QColor("#00D4FF")
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)
    
    def set_messages(self, messages: list[str]) -> None:
        """Replace the ticker messages."""
        self._messages = messages
        self._current_index = 0
    
    def _tick(self) -> None:
        self._offset += 1
        if self._offset > 200:
            self._offset = 0
            self._current_index = (self._current_index + 1) % len(self._messages)
        self.update()
    
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        font = QFont("JetBrains Mono", 10)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(font)
        
        # Fade effect on edges
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
        gradient.setColorAt(0.1, self._color)
        gradient.setColorAt(0.9, self._color)
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        painter.setPen(QPen(QColor(self._color)))
        
        text = self._messages[self._current_index]
        # Add some decorative prefix
        display_text = f"▶ {text}"
        
        painter.drawText(
            QRectF(0, 0, self.width(), self.height()),
            Qt.AlignmentFlag.AlignCenter,
            display_text
        )


# ═══════════════════════════════════════════════════════════════════
# PARTICLE FIELD — Background floating particles
# ═══════════════════════════════════════════════════════════════════
class ParticleField(QWidget):
    """Background floating particles for depth."""
    
    def __init__(self, parent: QWidget = None, particle_count: int = 40) -> None:
        super().__init__(parent)
        if parent:
            self.setGeometry(parent.rect())
            self.setParent(parent)
            self.lower()  # Send to back
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._particles = []
        for _ in range(particle_count):
            self._particles.append({
                "x": random.random(),
                "y": random.random(),
                "vx": (random.random() - 0.5) * 0.0005,
                "vy": (random.random() - 0.5) * 0.0005,
                "size": random.uniform(1, 3),
                "alpha": random.uniform(0.2, 0.6),
            })
        
        self._color = QColor("#00D4FF")
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)  # 30 FPS is enough for particles
    
    def _tick(self) -> None:
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            # Wrap around
            if p["x"] < 0: p["x"] = 1.0
            if p["x"] > 1: p["x"] = 0.0
            if p["y"] < 0: p["y"] = 1.0
            if p["y"] > 1: p["y"] = 0.0
        self.update()
    
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        
        for p in self._particles:
            x = p["x"] * w
            y = p["y"] * h
            size = p["size"]
            alpha = p["alpha"]
            
            color = QColor(self._color)
            color.setAlphaF(alpha)
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(x, y), size, size)


# ═══════════════════════════════════════════════════════════════════
# GLOW BORDER — Animated glowing border effect
# ═══════════════════════════════════════════════════════════════════
class GlowBorder(QWidget):
    """Applies an animated glowing border to its parent widget."""
    
    def __init__(self, parent: QWidget = None, color: str = "#00D4FF") -> None:
        super().__init__(parent)
        if parent:
            self.setGeometry(parent.rect())
            self.setParent(parent)
            self.raise_()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._color = QColor(color)
        self._phase = 0.0
        self._active = True
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)
    
    def _tick(self) -> None:
        self._phase = (self._phase + 0.02) % 1.0
        self.update()
    
    def paintEvent(self, event) -> None:
        if not self._active:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pulse = (math.sin(self._phase * 2 * math.pi) + 1) / 2
        alpha = 0.4 + pulse * 0.4
        
        color = QColor(self._color)
        color.setAlphaF(alpha)
        
        pen = QPen(color)
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(QRectF(rect), 8, 8)