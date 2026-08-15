"""
DesktopAI v2.0 — Command Palette (Ctrl+K)
File: src/gui/components/command_palette.py
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout,
)

from gui.theme.design_tokens import tokens_for


class CommandPalette(QDialog):
    def __init__(self, actions: list, theme: str = "dark", parent=None):
        super().__init__(parent)
        self._actions = actions
        self._chosen = None
        t = tokens_for(theme)
        self.setObjectName("cp")
        self.setFixedWidth(560)
        self.setStyleSheet(f"""
            QDialog#cp {{ background: {t['elevated']}; border: 1px solid {t['border']}; border-radius: 14px; }}
            QLineEdit#cpInput {{ background: transparent; border: none; border-bottom: 1px solid {t['border_subtle']};
                padding: 14px 18px; font-size: 15px; color: {t['text']}; }}
            QListWidget#cpList {{ background: transparent; border: none; padding: 8px; }}
            QListWidget#cpList::item {{ padding: 10px 12px; border-radius: 8px; color: {t['text_2']}; }}
            QListWidget#cpList::item:selected {{ background: {t['primary_soft']}; color: {t['nav_active_text']}; }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 8)
        lay.setSpacing(0)

        self.input = QLineEdit()
        self.input.setObjectName("cpInput")
        self.input.setPlaceholderText("Search commands…")
        self.input.textChanged.connect(self._filter)
        self.input.returnPressed.connect(self._activate_current)
        lay.addWidget(self.input)

        self.list = QListWidget()
        self.list.setObjectName("cpList")
        self.list.itemDoubleClicked.connect(lambda *a: self._activate_current())
        lay.addWidget(self.list)

        self._filter("")
        self.input.setFocus()

    def _filter(self, text: str):
        self.list.clear()
        for cid, label, hint in self._actions:
            if text.lower() in label.lower():
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, cid)
                if hint:
                    item.setText(f"{label}    {hint}")
                self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _activate_current(self):
        item = self.list.currentItem()
        if item:
            self._chosen = item.data(Qt.UserRole)
            self.accept()

    def exec(self) -> str | None:
        super().exec()
        return self._chosen