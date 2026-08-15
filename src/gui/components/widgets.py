"""
DesktopAI v2.0 — Reusable UI Components
File: src/gui/components/widgets.py

Small, theme-agnostic widgets styled entirely by premium_theme QSS
via objectNames. Use these instead of hand-styling per screen.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)


class PrimaryButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("daPrimary")
        self.setCursor(Qt.PointingHandCursor)


class SecondaryButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("daSecondary")
        self.setCursor(Qt.PointingHandCursor)


class GhostButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("daGhost")
        self.setCursor(Qt.PointingHandCursor)


class IconButton(QPushButton):
    def __init__(self, glyph: str = "", tooltip: str = "", parent=None):
        super().__init__(glyph, parent)
        self.setObjectName("daIcon")
        if tooltip:
            self.setToolTip(tooltip)
        self.setCursor(Qt.PointingHandCursor)


class SectionHeader(QWidget):
    """Title + subtitle row with optional right-side action."""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        col = QVBoxLayout()
        col.setSpacing(2)
        self.title = QLabel(title)
        self.title.setObjectName("daSectionTitle")
        col.addWidget(self.title)
        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("daSectionSub")
        self.subtitle.setVisible(bool(subtitle))
        col.addWidget(self.subtitle)
        lay.addLayout(col)
        lay.addStretch()
        self.action_slot = QHBoxLayout()
        lay.addLayout(self.action_slot)

    def add_action(self, widget: QWidget):
        self.action_slot.addWidget(widget)


class StatCard(QFrame):
    """Icon + big number + label (+ optional trend line)."""

    def __init__(self, icon: str, value: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("daStatCard")
        self.setMinimumHeight(92)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(3)

        self.icon = QLabel(icon)
        self.icon.setObjectName("daStatIcon")
        lay.addWidget(self.icon)

        self.value = QLabel(value)
        self.value.setObjectName("daStatValue")
        lay.addWidget(self.value)

        self.label = QLabel(label)
        self.label.setObjectName("daStatLabel")
        lay.addWidget(self.label)

        self.trend = QLabel("")
        self.trend.setObjectName("daStatTrendOk")
        self.trend.hide()
        lay.addWidget(self.trend)

    def set_value(self, value: str):
        self.value.setText(value)

    def set_trend(self, text: str, kind: str = "ok"):
        self.trend.setText(text)
        self.trend.setObjectName(f"daStatTrend{'Ok' if kind == 'ok' else 'Warn'}")
        self.trend.show()


class _StateFrame(QFrame):
    """Base for empty / error / success states."""

    def __init__(self, icon: str, icon_kind: str, title: str, desc: str, parent=None):
        super().__init__(parent)
        self.setObjectName("daState")
        self.setMinimumHeight(180)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)

        ic = QLabel(icon)
        ic.setObjectName(f"daStateIcon daStateIcon{icon_kind.capitalize()}")
        ic.setAlignment(Qt.AlignCenter)
        lay.addWidget(ic)

        # Stored as attributes so views can update the text later.
        self.title = QLabel(title)
        self.title.setObjectName("daStateTitle")
        self.title.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.title)

        self.desc = QLabel(desc)
        self.desc.setObjectName("daStateDesc")
        self.desc.setAlignment(Qt.AlignCenter)
        self.desc.setWordWrap(True)
        self.desc.setMaximumWidth(420)
        lay.addWidget(self.desc)

        self.button_row = QHBoxLayout()
        self.button_row.setAlignment(Qt.AlignCenter)
        lay.addLayout(self.button_row)

    def add_action(self, button: QPushButton):
        self.button_row.addWidget(button)


class EmptyState(_StateFrame):
    def __init__(self, title: str, desc: str, icon: str = "◇", parent=None):
        super().__init__(icon, "info", title, desc, parent)


class ErrorState(_StateFrame):
    def __init__(self, title: str, desc: str, parent=None):
        super().__init__("!", "err", title, desc, parent)


class SuccessState(_StateFrame):
    def __init__(self, title: str, desc: str, parent=None):
        super().__init__("✓", "ok", title, desc, parent)


class ProgressCard(QFrame):
    """Determinate progress with detail line + cancel."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("daProgressCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        self.title = QLabel(title)
        self.title.setObjectName("daSectionTitle")
        lay.addWidget(self.title)

        self.bar = QProgressBar()
        self.bar.setObjectName("daBar")
        self.bar.setFixedHeight(10)
        self.bar.setTextVisible(False)
        lay.addWidget(self.bar)

        row = QHBoxLayout()
        self.detail = QLabel("")
        self.detail.setObjectName("daProgressText")
        row.addWidget(self.detail)
        row.addStretch()
        self.cancel = GhostButton("Cancel")
        row.addWidget(self.cancel)
        lay.addLayout(row)

    def set_progress(self, current: int, total: int):
        if total > 0:
            self.bar.setValue(int((current / total) * 100))
            self.detail.setText(f"{current} / {total}")

    def set_detail(self, text: str):
        self.detail.setText(text)


_BADGE_KIND = {
    "code": "Info", "documents": "Neutral", "finance": "Ok", "images": "Info",
    "work": "Info", "archives": "Warn", "misc": "Neutral", "unknown": "Neutral",
}


class CategoryBadge(QLabel):
    def __init__(self, category: str, parent=None):
        super().__init__(category.title(), parent)
        kind = _BADGE_KIND.get(category.lower(), "Neutral")
        self.setObjectName(f"daBadge{kind}")


class ConfidenceBadge(QLabel):
    def __init__(self, confidence: float, parent=None):
        super().__init__(f"{int(confidence * 100)}%", parent)
        kind = "Ok" if confidence >= 0.85 else ("Warn" if confidence >= 0.5 else "Err")
        self.setObjectName(f"daBadge{kind}")


class StatusIndicator(QWidget):
    """Dot + text status (icon+text, never color alone)."""

    def __init__(self, text: str, kind: str = "ok", parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.dot = QLabel("●")
        self.dot.setObjectName(f"daStateIcon{kind.capitalize()}")
        self.dot.setStyleSheet("font-size: 10px;")
        lay.addWidget(self.dot)
        self.text = QLabel(text)
        self.text.setObjectName("daProgressText")
        lay.addWidget(self.text)

    def set_status(self, text: str, kind: str):
        self.text.setText(text)
        self.dot.setObjectName(f"daStateIcon{kind.capitalize()}")
        self.dot.style().unpolish(self.dot)
        self.dot.style().polish(self.dot)