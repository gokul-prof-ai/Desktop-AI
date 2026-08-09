"""
DesktopAI v2.0 — Magnetic Drop Zone (Fixed Folder Selection)
File: src/gui/components/trendy_drop_zone.py
"""
from __future__ import annotations
import math
import random
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF, Signal
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient, 
    QFont, QDragEnterEvent, QDragMoveEvent, QDropEvent, QMouseEvent, QPainterPath
)

class MagneticDropZone(QWidget):
    folder_selected = Signal(str)
    files_dropped = Signal(list)

    STATE_IDLE = 0
    STATE_HOVER = 1
    STATE_DRAG_OVER = 2
    STATE_SUCCESS = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        
        self._state = self.STATE_IDLE
        self._border_rotation = 0.0
        self._core_pulse = 0.0
        self._core_scale = 1.0
        self._glow_intensity = 0.0
        self._ripple_radius = 0.0
        self._ripple_alpha = 0.0
        self._ripple_pos = QPointF(0, 0)
        
        self._particles = []
        for _ in range(24):
            angle = random.uniform(0, 360)
            distance = random.uniform(80, 120)
            self._particles.append({
                "angle": angle, "distance": distance,
                "target_distance": distance,
                "size": random.uniform(2, 4),
                "speed": random.uniform(0.5, 1.5),
                "alpha": random.uniform(0.3, 0.8),
            })
        
        self._color_bg = QColor("#0A0A0F")
        self._color_core = QColor("#8B5CF6")
        self._color_core2 = QColor("#3B82F6")
        self._color_success = QColor("#10B981")

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._update_animations)
        self._anim_timer.start(16)

        self._setup_ui()
        self.setFixedSize(480, 320)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        
        self.title_label = QLabel("Drop folder here")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #E4E4E7; font-size: 22px; font-weight: 600; font-family: 'Segoe UI', sans-serif;")
        layout.addWidget(self.title_label)
        
        self.subtitle_label = QLabel("or click to browse your computer")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("color: #71717A; font-size: 14px; font-family: 'Segoe UI', sans-serif;")
        layout.addWidget(self.subtitle_label)
        layout.addStretch()

    def _update_animations(self):
        self._border_rotation = (self._border_rotation + 0.5) % 360.0
        self._core_pulse = (math.sin(self._border_rotation * 0.1) + 1) / 2
        
        target_glow = 0.0
        target_core_scale = 1.0
        
        if self._state == self.STATE_HOVER:
            target_glow = 0.3
            target_core_scale = 1.05
        elif self._state == self.STATE_DRAG_OVER:
            target_glow = 1.0
            target_core_scale = 1.15
        elif self._state == self.STATE_SUCCESS:
            target_glow = 0.8
            
        speed = 0.15
        self._glow_intensity += (target_glow - self._glow_intensity) * speed
        self._core_scale += (target_core_scale - self._core_scale) * speed
        
        for p in self._particles:
            if self._state == self.STATE_DRAG_OVER:
                p["target_distance"] = 40 + (p["distance"] - 40) * 0.3
            elif self._state == self.STATE_HOVER:
                p["target_distance"] = 60 + (p["distance"] - 60) * 0.5
            else:
                p["target_distance"] = p["distance"]
            
            p["distance"] += (p["target_distance"] - p["distance"]) * 0.1
            p["angle"] = (p["angle"] + p["speed"]) % 360
        
        if self._ripple_alpha > 0:
            self._ripple_radius += 8
            self._ripple_alpha -= 0.05
            if self._ripple_alpha < 0:
                self._ripple_alpha = 0
        
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        try:
            rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
            radius = 24.0
            
            self._draw_background(painter, rect, radius)
            self._draw_dot_border(painter, rect, radius)
            self._draw_particles(painter, rect)
            self._draw_core(painter, rect)
            
            if self._ripple_alpha > 0:
                self._draw_ripple(painter)
        finally:
            painter.end()

    def _draw_background(self, painter, rect, radius):
        bg_color = QColor(self._color_bg)
        bg_color.setAlpha(200 + int(55 * self._glow_intensity))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, radius, radius)
        
        if self._glow_intensity > 0.01:
            glow_color = QColor(self._color_core)
            glow_color.setAlphaF(0.1 * self._glow_intensity)
            painter.setBrush(QBrush(glow_color))
            painter.drawRoundedRect(rect, radius, radius)

    def _draw_dot_border(self, painter, rect, radius):
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        
        perimeter = 2 * (rect.width() + rect.height())
        dot_spacing = 20
        num_dots = int(perimeter / dot_spacing)
        
        for i in range(num_dots):
            progress = (i / num_dots + self._border_rotation / 360.0) % 1.0
            point = path.pointAtPercent(progress)
            
            dot_size = 2 + self._glow_intensity * 2
            alpha = 0.3 + self._glow_intensity * 0.5
            
            color = QColor(self._color_core)
            color.setAlphaF(alpha)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(point, dot_size, dot_size)

    def _draw_particles(self, painter, rect):
        center = rect.center()
        
        for p in self._particles:
            angle_rad = math.radians(p["angle"])
            x = center.x() + math.cos(angle_rad) * p["distance"]
            y = center.y() + math.sin(angle_rad) * p["distance"]
            
            size = p["size"] * (1 + self._glow_intensity * 0.5)
            alpha = p["alpha"] * (0.5 + self._glow_intensity * 0.5)
            
            color = QColor(self._color_core2)
            color.setAlphaF(alpha)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(x, y), size, size)

    def _draw_core(self, painter, rect):
        center = rect.center()
        
        base_size = 40
        pulse_size = base_size * self._core_scale * (0.9 + self._core_pulse * 0.2)
        
        gradient = QRadialGradient(center, pulse_size)
        gradient.setColorAt(0, QColor(255, 255, 255, 200))
        gradient.setColorAt(0.3, self._color_core)
        
        transparent_color = QColor(self._color_core)
        transparent_color.setAlpha(0)
        gradient.setColorAt(1, transparent_color)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(center, pulse_size, pulse_size)
        
        inner_size = pulse_size * 0.4
        inner_alpha = 150 + int(105 * self._glow_intensity)
        inner_color = QColor(255, 255, 255, inner_alpha)
        painter.setBrush(QBrush(inner_color))
        painter.drawEllipse(center, inner_size, inner_size)

    def _draw_ripple(self, painter):
        ripple_color = QColor(self._color_success)
        ripple_color.setAlphaF(self._ripple_alpha)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(ripple_color))
        painter.drawEllipse(self._ripple_pos, self._ripple_radius, self._ripple_radius)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._state = self.STATE_DRAG_OVER

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._state = self.STATE_HOVER

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._ripple_pos = event.position()
            self._ripple_radius = 10
            self._ripple_alpha = 0.6
            self._state = self.STATE_SUCCESS
            QTimer.singleShot(1000, lambda: self._reset_state())
            
            # Get the first dropped item (folder or file)
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    self.folder_selected.emit(url.toLocalFile())
                    break

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._open_folder_dialog()

    def enterEvent(self, event):
        self._state = self.STATE_HOVER

    def leaveEvent(self, event):
        self._state = self.STATE_IDLE

    def _reset_state(self):
        self._state = self.STATE_IDLE

    # ── FIXED: Now opens a Folder Selection Dialog ─────────────────────
    def _open_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            "Select Folder to Organize", 
            "", 
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if folder_path:
            self.folder_selected.emit(folder_path)