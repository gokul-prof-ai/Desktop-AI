"""
DesktopAI v2.0 — Settings View
File: src/gui/views/settings_view.py
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QComboBox, QScrollArea,
    QCheckBox, QSizePolicy,
)

from infrastructure.config.settings import Settings
from core.constants import APP_NAME, APP_VERSION


class SettingsView(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        sub = QLabel("Configure AI models, scanner behaviour, appearance, and privacy.")
        sub.setObjectName("Muted")
        layout.addWidget(sub)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        il = QVBoxLayout(inner)
        il.setContentsMargins(0, 0, 8, 0)
        il.setSpacing(12)

        il.addWidget(self._section_ai())
        il.addWidget(self._section_scanner())
        il.addWidget(self._section_appearance())
        il.addWidget(self._section_privacy())
        il.addWidget(self._section_about())
        il.addStretch()

        scroll.setWidget(inner)
        layout.addWidget(scroll, 1)

    # ── Sections ───────────────────────────────────────────────────

    def _section_ai(self) -> QFrame:
        card, body = self._card("AI & Intelligence")
        body.addWidget(self._row("AI Provider",  right=self._combo(["Ollama (Local)", "Mock AI"])))
        body.addWidget(self._sep())
        body.addWidget(self._row("Model",        right=self._combo(["llama3.2", "llama3.2:1b", "mistral", "gemma2"], Settings.ai.model)))
        body.addWidget(self._sep())
        body.addWidget(self._row("Fast Model",   right=self._combo(["llama3.2:1b", "llama3.2"], Settings.ai.model_fast)))
        body.addWidget(self._sep())
        body.addWidget(self._row("Ollama Host",  value=Settings.ai.host))
        body.addWidget(self._sep())
        body.addWidget(self._row("Timeout",      value=f"{Settings.ai.timeout}s"))
        body.addWidget(self._sep())
        body.addWidget(self._row("Max Retries",  value=str(Settings.ai.max_retries)))
        return card

    def _section_scanner(self) -> QFrame:
        card, body = self._card("Scanning")
        body.addWidget(self._row("Max Depth",       value=str(Settings.scanner.max_depth)))
        body.addWidget(self._sep())
        body.addWidget(self._row("Workers",          value=str(Settings.scanner.max_workers)))
        body.addWidget(self._sep())
        body.addWidget(self._row("Skip Hidden",      right=self._toggle(Settings.scanner.skip_hidden)))
        body.addWidget(self._sep())
        body.addWidget(self._row("Skip System",      right=self._toggle(Settings.scanner.skip_system)))
        body.addWidget(self._sep())
        body.addWidget(self._row("OCR Enabled",      right=self._toggle(Settings.ocr.enabled)))
        body.addWidget(self._sep())
        body.addWidget(self._row("OCR Engine",       value=Settings.ocr.engine))
        body.addWidget(self._sep())
        body.addWidget(self._row("Categories",       value=f"{len(Settings.categories)} rules"))
        return card

    def _section_appearance(self) -> QFrame:
        card, body = self._card("Appearance")
        body.addWidget(self._row("Theme", right=self._combo(
            ["Dark", "Light"],
            "Dark" if Settings.app.theme == "dark" else "Light"
        )))
        body.addWidget(self._sep())
        body.addWidget(self._row("Embedding Model",   value=Settings.search.embedding_model))
        body.addWidget(self._sep())
        body.addWidget(self._row("Max Search Results", value=str(Settings.search.max_results)))
        return card

    def _section_privacy(self) -> QFrame:
        card, body = self._card("Privacy & Data")
        body.addWidget(self._row(
            "Local Processing Only",
            right=self._toggle(True),
            note="All AI runs on your device. No data leaves your machine.",
        ))
        body.addWidget(self._sep())
        body.addWidget(self._row("Database", value=Settings.storage.db_filename))
        body.addWidget(self._sep())
        clear_btn = QPushButton("Clear All Data")
        clear_btn.setObjectName("DangerButton")
        clear_btn.setFixedWidth(140)
        body.addWidget(self._row("Reset", right=clear_btn))
        return card

    def _section_about(self) -> QFrame:
        card, body = self._card("About")
        body.addWidget(self._row("Application", value=APP_NAME))
        body.addWidget(self._sep())
        body.addWidget(self._row("Version",     value=f"v{APP_VERSION}"))
        body.addWidget(self._sep())
        body.addWidget(self._row("Architecture", value="4-layer clean arch"))
        body.addWidget(self._sep())
        body.addWidget(self._row("AI Stack",    value="Ollama · FAISS · PySide6"))
        body.addWidget(self._sep())
        body.addWidget(self._row("Python",      value="3.14+"))
        return card

    # ── Helpers ────────────────────────────────────────────────────

    def _card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        """Return (card_frame, body_layout)."""
        card = QFrame()
        card.setObjectName("Card")

        outer = QVBoxLayout(card)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Section header bar
        header = QWidget()
        header.setFixedHeight(42)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(18, 0, 18, 0)

        lbl = QLabel(title)
        lbl.setObjectName("SubHeading")
        h_layout.addWidget(lbl)

        outer.addWidget(header)

        # Header separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setObjectName("HRule")
        outer.addWidget(sep)

        # Body
        body_widget = QWidget()
        body_widget.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(18, 4, 18, 12)
        body_layout.setSpacing(0)

        outer.addWidget(body_widget)

        return card, body_layout

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setObjectName("HRule")
        return sep

    def _row(
        self,
        label: str,
        value: str = "",
        right: QWidget | None = None,
        note: str = "",
    ) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        row.setFixedHeight(52 if note else 44)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label column — use objectName so QSS handles color
        col = QVBoxLayout()
        col.setSpacing(1)

        lbl = QLabel(label)
        lbl.setObjectName("SettingsLabel")
        col.addWidget(lbl)

        if note:
            note_lbl = QLabel(note)
            note_lbl.setObjectName("Caption")
            col.addWidget(note_lbl)

        layout.addLayout(col)
        layout.addStretch()

        if right:
            layout.addWidget(right)
        elif value:
            val = QLabel(value)
            val.setObjectName("SettingsValue")
            layout.addWidget(val)

        return row

    def _combo(self, items: list, current: str = "") -> QComboBox:
        combo = QComboBox()
        combo.addItems(items)
        if current and current in items:
            combo.setCurrentText(current)
        combo.setFixedWidth(160)
        return combo

    def _toggle(self, checked: bool) -> QCheckBox:
        cb = QCheckBox()
        cb.setChecked(checked)
        return cb