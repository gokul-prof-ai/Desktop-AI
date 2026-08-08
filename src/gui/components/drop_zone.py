"""
DesktopAI v2.0 — Drop Zone Component
File: src/gui/components/drop_zone.py

Modern, clean drop zone with smooth hover effects.
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent


class DropZone(QWidget):
    """
    Modern drop zone for folder selection.
    Clean design with smooth hover animations.
    """
    folder_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._setup_ui()
        self._setup_animations()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignCenter)
        
        # Drop zone frame
        self.zone = QFrame()
        self.zone.setFixedSize(400, 280)
        self.zone.setStyleSheet("""
            QFrame {
                background-color: rgba(139, 92, 246, 0.05);
                border: 2px solid rgba(139, 92, 246, 0.3);
                border-radius: 20px;
            }
        """)
        
        zone_layout = QVBoxLayout(self.zone)
        zone_layout.setAlignment(Qt.AlignCenter)
        zone_layout.setSpacing(16)
        
        # Folder icon
        icon = QLabel("")
        icon.setFont(QFont("Segoe UI Emoji", 64))
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("color: #8B5CF6;")
        zone_layout.addWidget(icon)
        
        # Title
        title = QLabel("Drop folder here")
        title.setFont(QFont("SF Pro Display", 18, QFont.Weight.Medium))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFFFFF;")
        zone_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("or click to browse")
        subtitle.setFont(QFont("SF Pro Display", 13))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #A1A1AA;")
        zone_layout.addWidget(subtitle)
        
        layout.addWidget(self.zone)
    
    def _setup_animations(self):
        """Setup hover animations."""
        self._hover_anim = QPropertyAnimation(self.zone, b"geometry")
        self._hover_anim.setDuration(200)
        self._hover_anim.setEasingCurve(QEasingCurve.OutCubic)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # Animate on drag enter
            current = self.zone.geometry()
            expanded = current.adjusted(-5, -5, 5, 5)
            self._hover_anim.setStartValue(current)
            self._hover_anim.setEndValue(expanded)
            self._hover_anim.start()
            
            self.zone.setStyleSheet("""
                QFrame {
                    background-color: rgba(139, 92, 246, 0.15);
                    border: 2px solid rgba(139, 92, 246, 0.6);
                    border-radius: 20px;
                }
            """)
    
    def dragLeaveEvent(self, event):
        # Animate back
        current = self.zone.geometry()
        original = current.adjusted(5, 5, -5, -5)
        self._hover_anim.setStartValue(current)
        self._hover_anim.setEndValue(original)
        self._hover_anim.start()
        
        self.zone.setStyleSheet("""
            QFrame {
                background-color: rgba(139, 92, 246, 0.05);
                border: 2px solid rgba(139, 92, 246, 0.3);
                border-radius: 20px;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    self.folder_selected.emit(path)
                    from gui.utils.sounds import SOUNDS
                    SOUNDS.play_success()
                    break