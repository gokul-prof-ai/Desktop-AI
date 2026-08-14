"""
DesktopAI v2.0 — History View (Activity Center)
File: src/gui/views/history_view.py
"""
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy,
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
        self.refresh()

        from core.events import AppEvents
        AppEvents.apply_completed.connect(self.refresh)
        AppEvents.undo_completed.connect(self.refresh)
        AppEvents.apply_failed.connect(self.refresh)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        sub = QLabel(
            "A complete audit trail of every file operation DesktopAI has performed."
        )
        sub.setObjectName("Muted")
        layout.addWidget(sub)

        # Stat row
        row = QHBoxLayout()
        row.setSpacing(12)
        self.stat_total    = self._stat_card("Total Operations", "0")
        self.stat_success  = self._stat_card("Successful", "0")
        self.stat_undone   = self._stat_card("Undone", "0")
        row.addWidget(self.stat_total, 1)
        row.addWidget(self.stat_success, 1)
        row.addWidget(self.stat_undone, 1)
        layout.addLayout(row)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        title = QLabel("Activity Log")
        title.setObjectName("SubHeading")
        toolbar.addWidget(title)
        toolbar.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("SecondaryButton")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # Table card
        card = QFrame()
        card.setObjectName("Card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Status", "Action", "File", "Category", "Destination", "When"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        c_layout.addWidget(self.table)
        layout.addWidget(card, 1)

        # Empty state
        self.empty_label = QLabel(
            "No history yet. Organize a folder to see activity here."
        )
        self.empty_label.setObjectName("Muted")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)

    def _stat_card(self, label: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("StatCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(2)
        val = QLabel(value)
        val.setObjectName("StatValue")
        lbl = QLabel(label)
        lbl.setObjectName("StatLabel")
        layout.addWidget(val)
        layout.addWidget(lbl)
        card.value_label = val
        return card

    def refresh(self) -> None:
        try:
            history = DB.get_history(limit=500)
        except Exception as exc:
            logger.warning("Cannot load history: %s", exc)
            return

        total    = len(history)
        success  = sum(1 for h in history if h.get("status") == "completed")
        undone   = sum(1 for h in history if h.get("status") == "undone")

        self.stat_total.value_label.setText(str(total))
        self.stat_success.value_label.setText(str(success))
        self.stat_undone.value_label.setText(str(undone))

        if not history:
            self.table.setVisible(False)
            self.empty_label.setVisible(True)
            return

        self.table.setVisible(True)
        self.empty_label.setVisible(False)
        self.table.setRowCount(len(history))

        for row, entry in enumerate(history):
            status = entry.get("status", "")
            icon, color = _STATUS_ICONS.get(status, ("•", "#A1A1A6"))

            status_item = QTableWidgetItem(f" {icon}  {status}")
            status_item.setForeground(
                self._color_from_hex(color)
            )
            self.table.setItem(row, 0, status_item)

            action = entry.get("action_type", "")
            self.table.setItem(row, 1, QTableWidgetItem(action))

            src = entry.get("source_path", "")
            from pathlib import Path
            self.table.setItem(row, 2, QTableWidgetItem(Path(src).name if src else ""))

            self.table.setItem(row, 3, QTableWidgetItem(entry.get("category") or "—"))

            tgt = entry.get("target_path", "") or ""
            self.table.setItem(row, 4, QTableWidgetItem(Path(tgt).name if tgt else "—"))

            when = entry.get("performed_at", "")
            self.table.setItem(row, 5, QTableWidgetItem(when[:16] if when else ""))
            self.table.setRowHeight(row, 36)

    def _color_from_hex(self, hex_color: str):
        from PySide6.QtGui import QColor
        return QColor(hex_color)