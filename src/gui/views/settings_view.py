"""
DesktopAI v2.0 — Settings View (Configuration Center)
File: src/gui/views/settings_view.py
Categorized cards: Appearance, AI, Scanning, Sound, Privacy.
Writes through the Settings service; never crashes on missing keys.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel,
    QMessageBox, QRadioButton, QScrollArea, QSlider, QVBoxLayout, QWidget,
)

from core.logger import get_logger
from gui.components.widgets import PrimaryButton, SectionHeader, StatusIndicator
from gui.theme.premium_theme import apply_premium_theme
from infrastructure.config.settings import Settings

try:
    from gui.utils.sounds import SOUNDS
except Exception:
    SOUNDS = None

logger = get_logger(__name__)


class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(SectionHeader("Settings", "Tune DesktopAI to your workflow."))

        layout.addWidget(self._appearance_card())
        layout.addWidget(self._ai_card())
        layout.addWidget(self._scanning_card())
        layout.addWidget(self._sound_card())
        layout.addWidget(self._privacy_card())

        save_row = QHBoxLayout()
        save_row.addStretch()
        save = PrimaryButton("Save Settings")
        save.clicked.connect(self._save)
        save_row.addWidget(save)
        layout.addLayout(save_row)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    # ── Cards ────────────────────────────────────────────────────
    def _card(self, title: str, desc: str):
        card = QFrame()
        card.setObjectName("daCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)
        t = QLabel(title)
        t.setObjectName("daSectionTitle")
        lay.addWidget(t)
        d = QLabel(desc)
        d.setObjectName("daSectionSub")
        lay.addWidget(d)
        return card, lay

    def _appearance_card(self):
        card, lay = self._card("Appearance", "Theme applies instantly and persists.")
        row = QHBoxLayout()
        self.theme_group = QButtonGroup(self)
        self.radio_light = QRadioButton("Light")
        self.radio_dark = QRadioButton("Dark")
        self.theme_group.addButton(self.radio_light)
        self.theme_group.addButton(self.radio_dark)
        current = getattr(Settings.app, "theme", "dark")
        self.radio_light.setChecked(current == "light")
        self.radio_dark.setChecked(current != "light")
        row.addWidget(self.radio_light)
        row.addWidget(self.radio_dark)
        row.addStretch()
        lay.addLayout(row)
        self.radio_light.toggled.connect(lambda on: on and self._apply_theme("light"))
        self.radio_dark.toggled.connect(lambda on: on and self._apply_theme("dark"))
        return card

    def _ai_card(self):
        card, lay = self._card("Local AI", "DesktopAI runs models on your device.")
        status_row = QHBoxLayout()
        self.ai_status = StatusIndicator("Checking…", "info")
        status_row.addWidget(self.ai_status)
        status_row.addStretch()
        lay.addLayout(status_row)

        model_row = QHBoxLayout()
        lbl = QLabel("Model")
        lbl.setObjectName("daSectionSub")
        model_row.addWidget(lbl)
        model_row.addStretch()
        self.model_combo = QComboBox()
        self.model_combo.addItems(["llama3.2", "llama3.2:1b", "mistral", "codellama"])
        try:
            self.model_combo.setCurrentText(Settings.ai.model)
        except Exception:
            pass
        model_row.addWidget(self.model_combo)
        lay.addLayout(model_row)
        self._refresh_ai_status()
        return card

    def _scanning_card(self):
        card, lay = self._card("Scanning", "Control what the scanner sees.")
        self.skip_hidden = QCheckBox("Skip hidden files and folders")
        self.skip_system = QCheckBox("Skip system files")
        try:
            self.skip_hidden.setChecked(Settings.scanner.skip_hidden)
            self.skip_system.setChecked(Settings.scanner.skip_system)
        except Exception:
            pass
        lay.addWidget(self.skip_hidden)
        lay.addWidget(self.skip_system)
        return card

    def _sound_card(self):
        card, lay = self._card("Sound", "Subtle, quiet feedback. Never annoying.")
        self.sound_enabled = QCheckBox("Sound effects")
        if SOUNDS:
            self.sound_enabled.setChecked(SOUNDS.enabled)
        self.sound_enabled.toggled.connect(
            lambda on: SOUNDS.set_enabled(on) if SOUNDS else None
        )
        lay.addWidget(self.sound_enabled)

        vol_row = QHBoxLayout()
        vol_lbl = QLabel("Volume")
        vol_lbl.setObjectName("daSectionSub")
        vol_row.addWidget(vol_lbl)
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(50)
        if SOUNDS and hasattr(SOUNDS, "set_volume"):
            self.volume.valueChanged.connect(SOUNDS.set_volume)
        vol_row.addWidget(self.volume, 1)
        lay.addLayout(vol_row)
        return card

    def _privacy_card(self):
        card, lay = self._card("Privacy", "Your files never leave this computer.")
        note = QLabel("Local • Private — all analysis runs on-device.")
        note.setObjectName("daProgressText")
        lay.addWidget(note)
        clear = PrimaryButton("Clear Learned Preferences")
        clear.clicked.connect(self._clear_memory)
        lay.addWidget(clear, 0, Qt.AlignLeft)
        return card

    # ── Actions ─────────────────────────────────────────────────
    def _apply_theme(self, name: str):
        from PySide6.QtWidgets import QApplication
        apply_premium_theme(QApplication.instance(), name)
        fn = getattr(self.window(), "_update_theme_button", None)
        if callable(fn):
            self.window().current_theme = name
            fn()

    def _refresh_ai_status(self):
        try:
            from infrastructure.ai.gateway import AIGateway
            provider = type(getattr(AIGateway, "_provider", None)).__name__
            if "Mock" in provider:
                self.ai_status.set_status("Mock AI (testing mode)", "warn")
            elif AIGateway.health_check():
                self.ai_status.set_status("Connected", "ok")
            else:
                self.ai_status.set_status("Local AI not reachable", "err")
        except Exception:
            self.ai_status.set_status("AI status unknown", "warn")

    def _clear_memory(self):
        answer = QMessageBox.question(
            self, "Clear preferences",
            "This removes learned folder preferences. Continue?",
        )
        if answer != QMessageBox.Yes:
            return
        try:
            from infrastructure.storage.memory_store import MemoryStore
            MemoryStore.clear_all()
            self._toast("success", "Preferences cleared", "Learning reset.")
        except Exception as exc:
            self._toast("error", "Could not clear preferences", str(exc))

    def _save(self):
        try:
            Settings.ai.model = self.model_combo.currentText()
            Settings.scanner.skip_hidden = self.skip_hidden.isChecked()
            Settings.scanner.skip_system = self.skip_system.isChecked()
            Settings.app.theme = "light" if self.radio_light.isChecked() else "dark"
            Settings.save()
            self._toast("success", "Settings saved", "Your preferences were written.")
        except Exception as exc:
            self._toast("error", "Save failed", str(exc))

    def _toast(self, kind: str, title: str, msg: str):
        toasts = getattr(self.window(), "toasts", None)
        if toasts:
            getattr(toasts, f"show_{kind}")(title, msg)