"""
DesktopAI v2.0 — History View (Activity Center)
File: src/gui/views/history_view.py

Wired to DB.get_history() — shows a live audit trail of every
file operation DesktopAI has performed, with stats and auto-refresh.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView,
)

from infrastructure.storage.database import DB
from core.logger import get_logger

logger = get_logger(__name__)

_STATUS_ICONS = {
    "completed": ("✓", "#30D158"),
    "failed":    ("✕", "#FF453A"),
    "undone":    ("↶", "#FFD60A"),
}


class HistoryView(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()
        # Auto-refresh whenever the organizer emits global events
        try:
            from core.events import AppEvents
            AppEvents.apply_completed.connect(self.refresh)
            AppEvents.undo_completed.connect(self.refresh)
            AppEvents.apply_failed.connect(self.refresh)
        except Exception as exc:
            logger.debug("Could not connect AppEvents in HistoryView: %s", exc)

        self.refresh()

    # ── UI construction ────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        sub = QLabel(
            "A complete audit trail of every file operation DesktopAI has performed."
        )
        sub.setObjectName("Muted")
        layout.addWidget(sub)

        # ── Stat row ───────────────────────────────────────────────
        row = QHBoxLayout()
        row.setSpacing(12)
        self._stat_total   = self._stat_card("Total Operations", "0")
        self._stat_success = self._stat_card("Successful", "0")
        self._stat_undone  = self._stat_card("Undone", "0")
        row.addWidget(self._stat_total,   1)
        row.addWidget(self._stat_success, 1)
        row.addWidget(self._stat_undone,  1)
        layout.addLayout(row)

        # ── Toolbar ────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        title = QLabel("Activity Log")
        title.setObjectName("SubHeading")
        toolbar.addWidget(title)
        toolbar.addStretch()
        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.setObjectName("SecondaryButton")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        # ── Table card ─────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("Card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["Status", "Action", "File", "Category", "Destination", "When"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        c_layout.addWidget(self._table)
        layout.addWidget(card, 1)

        # ── Empty state ────────────────────────────────────────────
        self._empty = QLabel(
            "No history yet. Organize a folder to see activity here."
        )
        self._empty.setObjectName("Muted")
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setVisible(False)
        layout.addWidget(self._empty)

    def _stat_card(self, label: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("StatCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(2)
        val_lbl = QLabel(value)
        val_lbl.setObjectName("StatValue")
        cap_lbl = QLabel(label)
        cap_lbl.setObjectName("StatLabel")
        lay.addWidget(val_lbl)
        lay.addWidget(cap_lbl)
        card.value_label = val_lbl   # type: ignore[attr-defined]
        return card

    # ── Public refresh ─────────────────────────────────────────────

    def refresh(self, *_args) -> None:
        """Reload history from DB and repaint the table. Safe to call anytime."""
        try:
            history = DB.get_history(limit=500)
        except Exception as exc:
            logger.warning("HistoryView: cannot load history — %s", exc)
            history = []

        total   = len(history)
        success = sum(1 for h in history if h.get("status") == "completed")
        undone  = sum(1 for h in history if h.get("status") == "undone")

        self._stat_total.value_label.setText(str(total))
        self._stat_success.value_label.setText(str(success))
        self._stat_undone.value_label.setText(str(undone))

        if not history:
            self._table.setVisible(False)
            self._empty.setVisible(True)
            return

        self._table.setVisible(True)
        self._empty.setVisible(False)
        self._table.setRowCount(len(history))

        for row, entry in enumerate(history):
            status = entry.get("status", "")
            icon, color = _STATUS_ICONS.get(status, ("•", "#A1A1A6"))

            # Column 0 — Status icon + label
            status_item = QTableWidgetItem(f" {icon}  {status}")
            status_item.setForeground(QColor(color))
            self._table.setItem(row, 0, status_item)

            # Column 1 — Action type
            action = entry.get("action_type", "—")
            self._table.setItem(row, 1, QTableWidgetItem(action))

            # Column 2 — Source filename
            src = entry.get("source_path", "") or ""
            self._table.setItem(row, 2, QTableWidgetItem(Path(src).name if src else "—"))

            # Column 3 — Category
            self._table.setItem(row, 3, QTableWidgetItem(entry.get("category") or "—"))

            # Column 4 — Destination filename
            tgt = entry.get("target_path", "") or ""
            self._table.setItem(row, 4, QTableWidgetItem(Path(tgt).name if tgt else "—"))

            # Column 5 — Timestamp (truncated to minute)
            when = entry.get("performed_at", "") or ""
            self._table.setItem(row, 5, QTableWidgetItem(when[:16] if when else "—"))

            self._table.setRowHeight(row, 36)