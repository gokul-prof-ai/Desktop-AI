"""
DesktopAI v2.0 — Brand Mark
File: src/gui/components/brand.py
Rounded square + geometric D + cyan intelligence node.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

_G1, _G2, _NODE = "#8B5CF6", "#5B21B6", "#22D3EE"


def paint_mark(p: QPainter, rect: QRectF) -> None:
    p.setRenderHint(QPainter.Antialiasing, True)
    g = QLinearGradient(rect.topLeft(), rect.bottomRight())
    g.setColorAt(0, _G1)
    g.setColorAt(1, _G2)
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawRoundedRect(rect, rect.width() * 0.22, rect.height() * 0.22)

    w = rect.width()
    pen = QPen(QColor("#FFFFFF"), w * 0.09, Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    x0 = rect.left() + w * 0.34
    y1, y2 = rect.top() + w * 0.28, rect.top() + w * 0.72
    r = (y2 - y1) / 2
    p.drawLine(QPointF(x0, y1), QPointF(x0, y2))
    p.drawArc(QRectF(x0 - r, y1, 2 * r, 2 * r), 90 * 16, -180 * 16)

    p.setPen(Qt.NoPen)
    p.setBrush(QColor(_NODE))
    p.drawEllipse(QPointF(x0 + r, (y1 + y2) / 2), w * 0.07, w * 0.07)


from PySide6.QtCore import QPointF  # noqa: E402


class LogoMark(QWidget):
    def __init__(self, size: int = 30, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        paint_mark(p, QRectF(0, 0, self._size, self._size))
        p.end()


def app_icon(size: int = 64) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    paint_mark(p, QRectF(0, 0, size, size))
    p.end()
    return QIcon(pm)


_SVG_MARK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#8B5CF6"/><stop offset="1" stop-color="#5B21B6"/>
</linearGradient></defs>
<rect width="64" height="64" rx="14" fill="url(#g)"/>
<path d="M22 18 v28" stroke="#fff" stroke-width="5.5" stroke-linecap="round" fill="none"/>
<path d="M22 18 a14 14 0 0 1 0 28" stroke="#fff" stroke-width="5.5" stroke-linecap="round" fill="none"/>
<circle cx="36" cy="32" r="4.5" fill="#22D3EE"/>
</svg>
"""


def ensure_brand_assets() -> None:
    root = Path(__file__).resolve().parents[3]
    out = root / "assets" / "branding"
    out.mkdir(parents=True, exist_ok=True)
    target = out / "desktopai-mark.svg"
    if not target.exists():
        target.write_text(_SVG_MARK, encoding="utf-8")