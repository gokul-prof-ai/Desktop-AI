"""
DesktopAI v2.0 — Trendy Drop Zone
File: src/gui/components/trendy_drop_zone.py

A modern, glassmorphic drop zone featuring:
- Aurora background effect on drag-over
- Flowing gradient border animation
- Physics-based icon bouncing
- Ripple effect on drop
- Click-to-browse functionality
"""
from __future__ import annotations
import math
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog, QApplication
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, 
    QPointF, QRectF, Signal, Property
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient, 
    QRadialGradient, QFont, QDragEnterEvent, QDragMoveEvent, 
    QDropEvent, QMouseEvent, QPainterPath, QConicalGradient
)


class TrendyDropZone(QWidget):
    """
    A highly interactive, modern drop zone widget.
    """
    folder_selected = Signal(str)
    files_dropped = Signal(list)  # Emits list of file paths

    # Animation states
    STATE_IDLE = 0
    STATE_HOVER = 1
    STATE_DRAG_OVER = 2
    STATE_SUCCESS = 3

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        
        # Internal state
        self._state = self.STATE_IDLE
        self._border_phase = 0.0  # 0.0 to 1.0 for flowing border
        self._icon_scale = 1.0
        self._icon_bounce = 0.0
        self._glow_intensity = 0.0
        self._ripple_radius = 0.0
        self._ripple_alpha = 0.0
        self._ripple_pos = QPointF(0, 0)
        
        # Colors
        self._color_bg = QColor("#0A0A0F")
        self._color_border = QColor("#2A2A35")
        self._color_accent = QColor("#8B5CF6")  # Purple
        self._color_accent2 = QColor("#3B82F6") # Blue
        self._color_success = QColor("#10B981") # Green
        self._color_text = QColor("#E4E4E7")
        self._color_text_muted = QColor("#71717A")

        # Setup animation timer (60 FPS)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._update_animations)
        self._anim_timer.start(16)  # ~60 FPS

        # Setup UI layout (for text and icon)
        self._setup_ui()
        
        # Set fixed size for the drop zone
        self.setFixedSize(480, 320)

    def _setup_ui(self):
        """Setup the internal layout for text."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        
        # We will draw the icon manually in paintEvent for better animation control
        # So we just add the text labels here.
        
        self.title_label = QLabel("Drop files here")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #E4E4E7;
                font-size: 22px;
                font-weight: 600;
                font-family: 'SF Pro Display', 'Inter', sans-serif;
                letter-spacing: -0.5px;
            }
        """)
        layout.addWidget(self.title_label)
        
        self.subtitle_label = QLabel("or click to browse your computer")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: #71717A;
                font-size: 14px;
                font-family: 'SF Pro Display', 'Inter', sans-serif;
            }
        """)
        layout.addWidget(self.subtitle_label)
        
        layout.addStretch()

    # ── Animation Loop ─────────────────────────────────────────────
    def _update_animations(self):
        """Update all animation parameters every frame."""
        # Flowing border
        self._border_phase = (self._border_phase + 0.005) % 1.0
        
        # Target values based on state
        target_glow = 0.0
        target_icon_scale = 1.0
        target_icon_bounce = 0.0
        
        if self._state == self.STATE_HOVER:
            target_glow = 0.3
            target_icon_scale = 1.05
        elif self._state == self.STATE_DRAG_OVER:
            target_glow = 1.0
            target_icon_scale = 1.15
            target_icon_bounce = 1.0  # Max bounce
        elif self._state == self.STATE_SUCCESS:
            target_glow = 0.8
            
        # Smooth interpolation (lerp)
        speed = 0.15
        self._glow_intensity += (target_glow - self._glow_intensity) * speed
        self._icon_scale += (target_icon_scale - self._icon_scale) * speed
        
        # Bounce physics (sine wave decay)
        if target_icon_bounce > 0:
            self._icon_bounce = math.sin(self._border_phase * math.pi * 4) * target_icon_bounce * 0.2
        else:
            self._icon_bounce *= 0.8  # Decay
            
        # Ripple decay
        if self._ripple_alpha > 0:
            self._ripple_radius += 8
            self._ripple_alpha -= 0.05
            if self._ripple_alpha < 0:
                self._ripple_alpha = 0
                
        self.update()  # Trigger repaint

    # ── Custom Painting ────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        radius = 24.0
        
        # 1. Draw Background (Glassmorphism + Aurora)
        self._draw_background(painter, rect, radius)
        
        # 2. Draw Flowing Border
        self._draw_border(painter, rect, radius)
        
        # 3. Draw Icon (Manual for animation control)
        self._draw_icon(painter, rect)
        
        # 4. Draw Ripple
        if self._ripple_alpha > 0:
            self._draw_ripple(painter)

    def _draw_background(self, painter: QPainter, rect: QRectF, radius: float):
        """Draw the glass background with aurora effect."""
        # Base glass background
        bg_color = QColor(self._color_bg)
        bg_color.setAlpha(200 + int(55 * self._glow_intensity))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, radius, radius)
        
        # Aurora effect (only when dragging over)
        if self._glow_intensity > 0.01:
            painter.setCompositionMode(QPainter.CompositionMode_Plus)
            
            # Blob 1 (Purple)
            grad1 = QRadialGradient(
                QPointF(rect.width() * 0.3, rect.height() * 0.3), 
                rect.width() * 0.6
            )
            c1 = QColor(self._color_accent)
            c1.setAlphaF(0.15 * self._glow_intensity)
            grad1.setColorAt(0, c1)
            grad1.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(grad1))
            painter.drawRoundedRect(rect, radius, radius)
            
            # Blob 2 (Blue)
            grad2 = QRadialGradient(
                QPointF(rect.width() * 0.7, rect.height() * 0.7), 
                rect.width() * 0.6
            )
            c2 = QColor(self._color_accent2)
            c2.setAlphaF(0.15 * self._glow_intensity)
            grad2.setColorAt(0, c2)
            grad2.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(grad2))
            painter.drawRoundedRect(rect, radius, radius)
            
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

    def _draw_border(self, painter: QPainter, rect: QRectF, radius: float):
        """Draw a glowing, flowing gradient border."""
        # Outer glow
        if self._glow_intensity > 0.01:
            glow_color = QColor(self._color_accent)
            glow_color.setAlphaF(0.3 * self._glow_intensity)
            painter.setPen(QPen(QBrush(glow_color), 8))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)
        
        # Main border
        border_color = QColor(self._color_border)
        border_color.setAlphaF(0.5 + 0.5 * self._glow_intensity)
        painter.setPen(QPen(QBrush(border_color), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)
        
        # Flowing light effect (conical gradient rotating)
        if self._glow_intensity > 0.1:
            painter.save()
            painter.setClipPath(QPainterPath().addRoundedRect(rect, radius, radius))
            
            center = rect.center()
            grad = QConicalGradient(center, self._border_phase * 360)
            grad.setColorAt(0, QColor(0, 0, 0, 0))
            grad.setColorAt(0.4, QColor(0, 0, 0, 0))
            grad.setColorAt(0.5, QColor(self._color_accent))
            grad.setColorAt(0.6, QColor(0, 0, 0, 0))
            grad.setColorAt(1, QColor(0, 0, 0, 0))
            
            painter.setPen(QPen(QBrush(grad), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)
            painter.restore()

    def _draw_icon(self, painter: QPainter, rect: QRectF):
        """Draw the folder icon with bounce animation."""
        painter.save()
        
        # Position and scale
        icon_size = 64
        center_x = rect.center().x()
        center_y = rect.center().y() - 40 + self._icon_bounce * 20  # Bounce offset
        
        painter.translate(center_x, center_y)
        painter.scale(self._icon_scale, self._icon_scale)
        
        # Draw a sleek folder icon using QPainter primitives
        folder_color = QColor(self._color_accent)
        folder_color.setAlphaF(0.8 + 0.2 * self._glow_intensity)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(folder_color))
        
        # Folder shape (simplified modern folder)
        path = QPainterPath()
        path.moveTo(-20, -10)
        path.lineTo(-5, -10)
        path.lineTo(0, -5)
        path.lineTo(20, -5)
        path.lineTo(20, 15)
        path.lineTo(-20, 15)
        path.closeSubpath()
        
        # Add a subtle shadow/glow to the icon
        if self._glow_intensity > 0.1:
            painter.setCompositionMode(QPainter.CompositionMode_Plus)
            shadow_color = QColor(self._color_accent)
            shadow_color.setAlphaF(0.4 * self._glow_intensity)
            painter.setBrush(QBrush(shadow_color))
            painter.drawPath(path)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            
        painter.setBrush(QBrush(folder_color))
        painter.drawPath(path)
        
        painter.restore()

    def _draw_ripple(self, painter: QPainter):
        """Draw the drop ripple effect."""
        painter.save()
        ripple_color = QColor(self._color_success)
        ripple_color.setAlphaF(self._ripple_alpha)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(ripple_color))
        painter.drawEllipse(self._ripple_pos, self._ripple_radius, self._ripple_radius)
        painter.restore()

    # ── Drag & Drop Events ─────────────────────────────────────────
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._state = self.STATE_DRAG_OVER
            self.update()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._state = self.STATE_HOVER
        self.update()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
            # Set ripple position
            self._ripple_pos = event.position()
            self._ripple_radius = 10
            self._ripple_alpha = 0.6
            
            # Trigger success state briefly
            self._state = self.STATE_SUCCESS
            QTimer.singleShot(1000, lambda: self._reset_state())
            
            # Process files
            files = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    files.append(url.toLocalFile())
            
            if files:
                self.files_dropped.emit(files)
                # For this demo, we just take the first folder/file
                self.folder_selected.emit(files[0])

    # ── Mouse Events (Click to browse) ─────────────────────────────
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._open_file_dialog()

    def enterEvent(self, event):
        self._state = self.STATE_HOVER
        self.update()

    def leaveEvent(self, event):
        self._state = self.STATE_IDLE
        self.update()

    def _reset_state(self):
        self._state = self.STATE_IDLE
        self.update()

    def _open_file_dialog(self):
        """Open a native file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File or Folder",
            "",
            "All Files (*);;Folders (.)"
        )
        if file_path:
            self.folder_selected.emit(file_path)