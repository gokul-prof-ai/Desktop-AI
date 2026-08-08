"""
DesktopAI v2.0 — Jarvis Status Bar
File: src/gui/components/status_bar.py

Live HUD-style status bar showing:
- AI connection status
- System stats (CPU, memory)
- Current time
- Active session info
"""
from __future__ import annotations
import os
import platform
from datetime import datetime
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from core.logger import get_logger

logger = get_logger(__name__)


class JarvisStatusBar(QWidget):
    """Live status bar with system stats and AI status."""
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(28)
        
        self._setup_ui()
        self._setup_timers()
    
    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(20)
        
        # Font for status items
        font = QFont("JetBrains Mono", 10)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        
        # ── Left section: System info ──────────────────────────
        self._system_label = QLabel()
        self._system_label.setFont(font)
        self._system_label.setStyleSheet("color: #00D4FF;")
        layout.addWidget(self._system_label)
        
        # Separator
        sep1 = QLabel("│")
        sep1.setFont(font)
        sep1.setStyleSheet("color: #1A4D66;")
        layout.addWidget(sep1)
        
        # ── Center section: AI status ──────────────────────────
        self._ai_status_label = QLabel("AI: INITIALIZING")
        self._ai_status_label.setFont(font)
        self._ai_status_label.setStyleSheet("color: #FFB300;")
        layout.addWidget(self._ai_status_label)
        layout.addStretch()
        
        # Separator
        sep2 = QLabel("│")
        sep2.setFont(font)
        sep2.setStyleSheet("color: #1A4D66;")
        layout.addWidget(sep2)
        
        # ── Right section: Time ────────────────────────────────
        self._time_label = QLabel()
        self._time_label.setFont(font)
        self._time_label.setStyleSheet("color: #00D4FF;")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._time_label)
    
    def _setup_timers(self) -> None:
        """Update stats every second."""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(1000)
        self._update()
    
    def _update(self) -> None:
        """Refresh all status values."""
        # System info
        try:
            cpu_percent = self._get_cpu_percent()
            mem_percent = self._get_memory_percent()
            self._system_label.setText(
                f"CPU: {cpu_percent:4.1f}%  │  MEM: {mem_percent:4.1f}%  │  "
                f"{platform.system().upper()}"
            )
        except Exception:
            self._system_label.setText("SYSTEM: MONITORING")
        
        # Time
        now = datetime.now()
        self._time_label.setText(now.strftime("%H:%M:%S"))
    
    def set_ai_status(self, status: str, color: str = "#00D4FF") -> None:
        """Update the AI status indicator."""
        self._ai_status_label.setText(f"AI: {status.upper()}")
        self._ai_status_label.setStyleSheet(f"color: {color};")
    
    def _get_cpu_percent(self) -> float:
        """Get current CPU usage (cross-platform)."""
        try:
            if platform.system() == "Windows":
                # Windows: use os.popen with typeperf
                import subprocess
                result = subprocess.run(
                    ["wmic", "cpu", "get", "loadpercentage"],
                    capture_output=True, text=True, timeout=1
                )
                for line in result.stdout.strip().split("\n"):
                    line = line.strip()
                    if line.isdigit():
                        return float(line)
            else:
                # Unix: read /proc/stat
                with open("/proc/stat") as f:
                    line = f.readline()
                fields = line.split()[1:]
                idle = int(fields[3])
                total = sum(int(x) for x in fields)
                return (1 - idle / total) * 100
        except Exception:
            return 0.0
    
    def _get_memory_percent(self) -> float:
        """Get current memory usage (cross-platform)."""
        try:
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(
                    ["wmic", "os", "get", "freephysicalmemory,totalvisiblememorysize"],
                    capture_output=True, text=True, timeout=1
                )
                lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
                if len(lines) >= 2:
                    values = lines[-1].split()
                    if len(values) >= 2:
                        total = int(values[0])
                        free = int(values[1])
                        return ((total - free) / total) * 100
            else:
                with open("/proc/meminfo") as f:
                    lines = f.readlines()
                mem = {}
                for line in lines[:5]:
                    parts = line.split()
                    mem[parts[0].rstrip(":")] = int(parts[1])
                total = mem.get("MemTotal", 1)
                free = mem.get("MemAvailable", mem.get("MemFree", 0))
                return ((total - free) / total) * 100
        except Exception:
            return 0.0