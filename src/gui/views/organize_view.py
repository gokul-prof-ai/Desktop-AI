"""
DesktopAI v2.0 — Organize View (App Shell UI)
File: src/gui/views/organize_view.py

Settings-type layout:
  - Header (title + subtitle)
  - Status card (what to do)
  - Two-col: plan preview | action panel
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QSizePolicy,
)
from PySide6.QtCore import Qt

_PAD = 24


class OrganizeView(QWidget):
    """Organize screen — review AI plan, apply or undo."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(_PAD, _PAD, _PAD, _PAD)
        root.setSpacing(16)

        # ── Sub-header ─────────────────────────────────────────────
        sub = QLabel("Review AI categorization and apply changes to your folder.")
        sub.setStyleSheet("color: #A1A1A6; font-size: 13px;")
        root.addWidget(sub)

        # ── Status banner card ─────────────────────────────────────
        banner = self._build_banner()
        root.addWidget(banner)

        # ── Two-column: plan list | action panel ───────────────────
        two_col = QHBoxLayout()
        two_col.setSpacing(12)

        plan_panel = self._build_plan_panel()
        action_panel = self._build_action_panel()

        two_col.addWidget(plan_panel, 3)
        two_col.addWidget(action_panel, 1)

        root.addLayout(two_col, 1)

    def _build_banner(self) -> QFrame:
        """Info banner — tells user what to do next."""
        card = QFrame()
        card.setObjectName("Card")
        card.setFixedHeight(72)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 0, 20, 0)

        icon = QLabel("○")
        icon.setStyleSheet("color: #0A84FF; font-size: 18px;")
        layout.addWidget(icon)

        layout.addSpacing(12)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title = QLabel("No scan loaded")
        title.setStyleSheet("color: #F5F5F7; font-size: 13px; font-weight: 600;")
        text_col.addWidget(title)

        desc = QLabel("Go to Home, drop a folder, then return here to review and apply the organization plan.")
        desc.setStyleSheet("color: #A1A1A6; font-size: 12px;")
        text_col.addWidget(desc)

        layout.addLayout(text_col)
        layout.addStretch()

        return card

    def _build_plan_panel(self) -> QFrame:
        """Left panel — shows file plan list."""
        panel = QFrame()
        panel.setObjectName("Card")
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Panel header
        header = QHBoxLayout()
        title = QLabel("Organization Plan")
        title.setStyleSheet(
            "color: #F5F5F7; font-size: 13px; font-weight: 600;"
        )
        header.addWidget(title)
        header.addStretch()

        count = QLabel("0 files")
        count.setStyleSheet("color: #6C6C70; font-size: 12px;")
        header.addWidget(count)

        layout.addLayout(header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            "background: rgba(255,255,255,0.08); border: none; max-height: 1px;"
        )
        layout.addWidget(sep)

        # Empty state
        empty = QLabel("Scan a folder on the Home screen to see\nthe AI organization plan here.")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet(
            "color: #6C6C70; font-size: 13px; line-height: 1.6;"
        )
        layout.addWidget(empty, 1, Qt.AlignCenter)

        return panel

    def _build_action_panel(self) -> QFrame:
        """Right panel — apply / undo actions."""
        panel = QFrame()
        panel.setObjectName("Card")
        panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        panel.setFixedWidth(220)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title = QLabel("Actions")
        title.setStyleSheet(
            "color: #F5F5F7; font-size: 13px; font-weight: 600;"
        )
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            "background: rgba(255,255,255,0.08); border: none; max-height: 1px;"
        )
        layout.addWidget(sep)

        # Action buttons
        apply_btn = QPushButton("Apply Plan")
        apply_btn.setObjectName("PrimaryButton")
        apply_btn.setEnabled(False)
        layout.addWidget(apply_btn)

        undo_btn = QPushButton("Undo Last")
        undo_btn.setObjectName("SecondaryButton")
        undo_btn.setEnabled(False)
        layout.addWidget(undo_btn)

        export_btn = QPushButton("Export Report")
        export_btn.setObjectName("GhostButton")
        export_btn.setEnabled(False)
        layout.addWidget(export_btn)

        layout.addStretch()

        # Status note
        note = QLabel("No plan loaded.\nRun a scan first.")
        note.setAlignment(Qt.AlignCenter)
        note.setStyleSheet("color: #6C6C70; font-size: 11px;")
        layout.addWidget(note)

        return panel