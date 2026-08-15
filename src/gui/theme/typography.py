"""
DesktopAI v2.0 — Typography
File: src/gui/theme/typography.py
Inter with graceful Segoe UI fallback; single scale for the whole app.
"""
from __future__ import annotations

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

SCALE = {
    "hero": 32, "page": 24, "section": 17, "card": 28,
    "body": 14, "secondary": 13, "meta": 11,
}


def resolve_family() -> str:
    families = QFontDatabase.families()
    for cand in ("Inter", "Inter Variable", "Segoe UI Variable Text", "Segoe UI"):
        if cand in families:
            return cand
    return "Segoe UI"


def font(size: int, weight: int = 400) -> QFont:
    f = QFont(resolve_family(), size, weight)
    f.setStyleHint(QFont.SansSerif)
    return f


def apply_typography(app: QApplication) -> None:
    app.setFont(font(SCALE["body"], 400))