"""
DesktopAI v2.0 — Icon System
File: src/gui/components/icons.py

Single coherent 24-grid stroke icon family, rendered with QPainter.
Consistent stroke width, round caps/joins. Colorable per theme.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

DRAW = {}


def _reg(name):
    def deco(fn):
        DRAW[name] = fn
        return fn
    return deco


def _pt(r: QRectF, x: float, y: float) -> QPointF:
    return QPointF(r.left() + x * r.width() / 24.0, r.top() + y * r.height() / 24.0)


def _poly(p, r, pts, closed=False):
    path = QPainterPath()
    path.moveTo(_pt(r, *pts[0]))
    for x, y in pts[1:]:
        path.lineTo(_pt(r, x, y))
    if closed:
        path.closeSubpath()
    p.drawPath(path)


def _rrect(p, r, x, y, w, h, rad=2.0):
    p.drawRoundedRect(QRectF(_pt(r, x, y), _pt(r, x + w, y + h)), rad, rad)


def _circle(p, r, cx, cy, rad):
    p.drawEllipse(_pt(r, cx, cy), rad * r.width() / 24.0, rad * r.height() / 24.0)


def _dot(p, r, cx, cy, rad, color):
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(color))
    _circle(p, r, cx, cy, rad)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(color, p.pen().width() or 1.5))


@_reg("home")
def _(p, r, c):
    _poly(p, r, [(5, 11), (12, 4.5), (19, 11)])
    _poly(p, r, [(6.5, 9.5), (6.5, 19.5), (17.5, 19.5), (17.5, 9.5)])
    _poly(p, r, [(10, 19.5), (10, 14.5), (14, 14.5), (14, 19.5)])


@_reg("organize")
def _(p, r, c):
    for x, y in ((4, 4), (13, 4), (4, 13), (13, 13)):
        _rrect(p, r, x, y, 7, 7, 1.8)


@_reg("search")
def _(p, r, c):
    _circle(p, r, 11, 11, 6)
    _poly(p, r, [(15.6, 15.6), (20, 20)])


@_reg("chat")
def _(p, r, c):
    _rrect(p, r, 4, 4.5, 16, 12, 3)
    _poly(p, r, [(9, 16.5), (8, 20), (12.5, 16.5)])


@_reg("history")
def _(p, r, c):
    _circle(p, r, 12, 12, 7.5)
    _poly(p, r, [(12, 8), (12, 12.3), (15, 13.8)])


@_reg("watcher")
def _(p, r, c):
    _dot(p, r, 8, 12, 1.8, c)
    for rad in (5, 9):
        p.drawArc(QRectF(_pt(r, 8 - rad, 12 - rad), _pt(r, 8 + rad, 12 + rad)), -50 * 16, 100 * 16)


@_reg("settings")
def _(p, r, c):
    _circle(p, r, 12, 12, 3.2)
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        x1, y1 = 12 + 5.6 * math.cos(a), 12 + 5.6 * math.sin(a)
        x2, y2 = 12 + 8.2 * math.cos(a), 12 + 8.2 * math.sin(a)
        _poly(p, r, [(x1, y1), (x2, y2)])


@_reg("folder")
def _(p, r, c):
    _poly(p, r, [(3.5, 6.5), (9.5, 6.5), (11.5, 8.5), (20.5, 8.5), (20.5, 19), (3.5, 19)], True)


@_reg("file")
def _(p, r, c):
    _poly(p, r, [(6, 3.5), (14.5, 3.5), (18.5, 7.5), (18.5, 20.5), (6, 20.5)], True)
    _poly(p, r, [(14.5, 3.5), (14.5, 7.5), (18.5, 7.5)])
    _poly(p, r, [(9, 12), (15.5, 12)])
    _poly(p, r, [(9, 15.5), (15.5, 15.5)])


@_reg("code")
def _(p, r, c):
    _poly(p, r, [(9, 8), (5, 12), (9, 16)])
    _poly(p, r, [(15, 8), (19, 12), (15, 16)])


@_reg("image")
def _(p, r, c):
    _rrect(p, r, 4, 5, 16, 14, 2)
    _circle(p, r, 9.2, 10, 1.6)
    _poly(p, r, [(6, 17.5), (10.5, 12.5), (13.5, 15.5), (16.5, 11.5), (18, 14)])


@_reg("video")
def _(p, r, c):
    _rrect(p, r, 3.5, 6, 17, 12, 2.5)
    _poly(p, r, [(10.5, 9.5), (10.5, 14.5), (15, 12)], True)


@_reg("audio")
def _(p, r, c):
    _circle(p, r, 8.5, 17, 2.5)
    _poly(p, r, [(11, 17), (11, 5.5), (16.5, 4.5), (16.5, 9.5)])


@_reg("archive")
def _(p, r, c):
    _rrect(p, r, 4, 4, 16, 5, 1.5)
    _rrect(p, r, 5.5, 9, 13, 11, 1.5)
    _poly(p, r, [(10, 13), (14, 13)])


@_reg("sheet")
def _(p, r, c):
    _rrect(p, r, 5, 3.5, 14, 17, 2)
    _poly(p, r, [(5, 9.5), (19, 9.5)])
    _poly(p, r, [(5, 15), (19, 15)])
    _poly(p, r, [(12, 9.5), (12, 20.5)])


@_reg("slides")
def _(p, r, c):
    _rrect(p, r, 3.5, 4.5, 17, 11.5, 2)
    _poly(p, r, [(12, 16), (12, 19)])
    _poly(p, r, [(8, 19.5), (16, 19.5)])


@_reg("spark")
def _(p, r, c):
    _poly(p, r, [(12, 4), (13.6, 10.4), (20, 12), (13.6, 13.6), (12, 20), (10.4, 13.6), (4, 12), (10.4, 10.4)], True)


@_reg("success")
def _(p, r, c):
    _circle(p, r, 12, 12, 8)
    _poly(p, r, [(8.5, 12.5), (11, 15), (15.8, 9.5)])


@_reg("warning")
def _(p, r, c):
    _poly(p, r, [(12, 4.5), (20.5, 19), (3.5, 19)], True)
    _poly(p, r, [(12, 10), (12, 14.2)])
    _dot(p, r, 12, 16.6, 1.1, c)


@_reg("error")
def _(p, r, c):
    _circle(p, r, 12, 12, 8)
    _poly(p, r, [(9.5, 9.5), (14.5, 14.5)])
    _poly(p, r, [(14.5, 9.5), (9.5, 14.5)])


@_reg("refresh")
def _(p, r, c):
    p.drawArc(QRectF(_pt(r, 5, 5), _pt(r, 19, 19)), 45 * 16, 260 * 16)
    _poly(p, r, [(17.2, 10.8), (17, 7.2), (13.4, 7)])


@_reg("undo")
def _(p, r, c):
    _poly(p, r, [(8, 6), (4, 10), (8, 14)])
    _poly(p, r, [(4, 10), (17, 10)])
    p.drawArc(QRectF(_pt(r, 13, 10), _pt(r, 21, 18)), 90 * 16, -90 * 16)


@_reg("open")
def _(p, r, c):
    _rrect(p, r, 4.5, 9.5, 15, 10.5, 2)
    _poly(p, r, [(10, 14), (19.5, 4.5)])
    _poly(p, r, [(13.5, 4.5), (19.5, 4.5), (19.5, 10.5)])


@_reg("filter")
def _(p, r, c):
    _poly(p, r, [(4, 5), (20, 5), (14, 12.5), (14, 18.5), (10, 16.5), (10, 12.5)], True)


@_reg("sort")
def _(p, r, c):
    _poly(p, r, [(8, 5), (8, 19)])
    _poly(p, r, [(5, 16), (8, 19), (11, 16)])
    _poly(p, r, [(16, 19), (16, 5)])
    _poly(p, r, [(13, 8), (16, 5), (19, 8)])


@_reg("more")
def _(p, r, c):
    for x in (5.5, 12, 18.5):
        _dot(p, r, x, 12, 1.5, c)


@_reg("close")
def _(p, r, c):
    _poly(p, r, [(6.5, 6.5), (17.5, 17.5)])
    _poly(p, r, [(17.5, 6.5), (6.5, 17.5)])


@_reg("sun")
def _(p, r, c):
    _circle(p, r, 12, 12, 4)
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        _poly(p, r, [(12 + 6.2 * math.cos(a), 12 + 6.2 * math.sin(a)),
                     (12 + 8.6 * math.cos(a), 12 + 8.6 * math.sin(a))])


@_reg("moon")
def _(p, r, c, ):
    outer = QPainterPath()
    outer.addEllipse(QRectF(_pt(r, 5, 5), _pt(r, 19, 19)))
    inner = QPainterPath()
    inner.addEllipse(QRectF(_pt(r, 9, 3), _pt(r, 23, 17)))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(c))
    p.drawPath(outer.subtracted(inner))
    p.setBrush(Qt.NoBrush)


@_reg("scan")
def _(p, r, c):
    _poly(p, r, [(4, 15), (4, 19.5), (20, 19.5), (20, 15)])
    _poly(p, r, [(12, 4), (12, 14)])
    _poly(p, r, [(8, 9.5), (12, 5.5), (16, 9.5)])


@_reg("stop")
def _(p, r, c):
    _rrect(p, r, 7, 7, 10, 10, 2)


_CACHE: dict = {}


def pixmap(name: str, size: int = 18, color=None) -> QPixmap:
    col = QColor(color) if color else QColor("#5F6675")
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(QPen(col, max(1.3, size * 0.085), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    m = size * 0.08
    fn = DRAW.get(name)
    if fn:
        fn(p, QRectF(m, m, size - 2 * m, size - 2 * m), col)
    p.end()
    return pm


def qicon(name: str, size: int = 18, color=None) -> QIcon:
    key = (name, size, color.name() if isinstance(color, QColor) else str(color))
    if key not in _CACHE:
        _CACHE[key] = QIcon(pixmap(name, size, color))
    return _CACHE[key]