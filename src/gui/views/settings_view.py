"""
DesktopAI v2.0 — Settings View (feedback next to action)
File: src/gui/views/settings_view.py
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QCheckBox, QComboBox, QHBoxLayout,
)
from gui.components.sound_button import SoundButton
from gui.theme import theme_manager
from core.logger import get_logger

logger = get_logger(__name__)


class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        subtitle = QLabel("Configure DesktopAI to your preferences")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(subtitle)

        ai = self._card("AI Configuration")
        row = QHBoxLayout()
        ml = QLabel("AI Model:")
        ml.setObjectName("StatusLabel")
        row.addWidget(ml)
        self.model_combo = QComboBox()
        self.model_combo.setObjectName("Combo")
        self.model_combo.addItems(["llama3.2", "llama3.2:1b", "mistral", "codellama"])
        row.addWidget(self.model_combo)
        row.addStretch()
        ai.layout().addLayout(row)
        layout.addWidget(ai)

        sc = self._card("Scanner")
        self.skip_hidden = QCheckBox("Skip hidden files and folders")
        self.skip_hidden.setChecked(True)
        sc.layout().addWidget(self.skip_hidden)
        self.skip_system = QCheckBox("Skip system files")
        self.skip_system.setChecked(True)
        sc.layout().addWidget(self.skip_system)
        layout.addWidget(sc)

        ap = self._card("Appearance")
        trow = QHBoxLayout()
        tl = QLabel("Theme:")
        tl.setObjectName("StatusLabel")
        trow.addWidget(tl)
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("Combo")
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(theme_manager.current_theme())
        trow.addWidget(self.theme_combo)
        trow.addStretch()
        ap.layout().addLayout(trow)
        layout.addWidget(ap)

        layout.addStretch()

        # Status + actions on ONE row (feedback next to the action)
        actions = QHBoxLayout()
        actions.setSpacing(16)
        self.status = QLabel("")
        self.status.setObjectName("StatusLabel")
        actions.addWidget(self.status)
        actions.addStretch()
        reset = SoundButton("Reset to Defaults")
        reset.setObjectName("SecondaryButton")
        reset.setFixedSize(160, 44)
        reset.clicked.connect(self._reset)
        actions.addWidget(reset)
        save = SoundButton("Save Settings")
        save.setObjectName("PrimaryButton")
        save.setFixedSize(160, 44)
        save.clicked.connect(self._save)
        actions.addWidget(save)
        layout.addLayout(actions)

    def _card(self, title: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        l = QVBoxLayout(card)
        l.setContentsMargins(24, 24, 24, 24)
        l.setSpacing(16)
        t = QLabel(title)
        t.setObjectName("AccentLabel")
        l.addWidget(t)
        return card

    def _save(self):
        try:
            from infrastructure.config.settings import Settings
            Settings.ai.model = self.model_combo.currentText()
            Settings.scanner.skip_hidden = self.skip_hidden.isChecked()
            Settings.scanner.skip_system = self.skip_system.isChecked()
            Settings.app.theme = self.theme_combo.currentText()
            Settings.save()
            theme_manager.apply_theme(self.theme_combo.currentText(), persist=False)
            self.status.setText("✓ Settings saved.")
        except Exception as exc:
            self.status.setText(f"✗ Could not save: {exc}")
            logger.warning("Save failed: %s", exc)

    def _reset(self):
        self.model_combo.setCurrentText("llama3.2")
        self.skip_hidden.setChecked(True)
        self.skip_system.setChecked(True)
        self.theme_combo.setCurrentText("dark")
        self.status.setText("Defaults restored — click Save to apply.")