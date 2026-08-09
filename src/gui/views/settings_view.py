"""
DesktopAI v2.0 — Settings View (Professional Configuration Center)
File: src/gui/views/settings_view.py
"""
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QComboBox, QScrollArea,
    QCheckBox, QSlider, QSizePolicy,
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
        scroll.setStyleSheet("background: transparent;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 8, 0)
        inner_layout.setSpacing(12)

        inner_layout.addWidget(self._section_ai())
        inner_layout.addWidget(self._section_scanner())
        inner_layout.addWidget(self._section_appearance())
        inner_layout.addWidget(self._section_privacy())
        inner_layout.addWidget(self._section_about())
        inner_layout.addStretch()

        scroll.setWidget(inner)
        layout.addWidget(scroll, 1)

    # ── Sections ───────────────────────────────────────────────────

    def _section_ai(self) -> QFrame:
        card = self._card("AI & Intelligence")
        layout = self._card_body(card)

        layout.addWidget(self._row("AI Provider", right=self._combo(["Ollama (Local)", "Mock AI"])))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("Model", right=self._combo(
            ["llama3.2", "llama3.2:1b", "mistral", "gemma2"],
            current=Settings.ai.model,
        )))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("Fast Model", right=self._combo(
            ["llama3.2:1b", "llama3.2"],
            current=Settings.ai.model_fast,
        )))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("Ollama Host", value=Settings.ai.host))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("Request Timeout", value=f"{Settings.ai.timeout}s"))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("Max Retries", value=str(Settings.ai.max_retries)))

        return card

    def _section_scanner(self) -> QFrame:
        card = self._card("Scanning")
        layout = self._card_body(card)

        layout.addWidget(self._row("Max Scan Depth", value=str(Settings.scanner.max_depth)))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("Parallel Workers", value=str(Settings.scanner.max_workers)))
        layout.addWidget(self._sep())
        layout.addWidget(self._row(
            "Skip Hidden Files",
            right=self._toggle(Settings.scanner.skip_hidden),
        ))
        layout.addWidget(self._sep())
        layout.addWidget(self._row(
            "Skip System Folders",
            right=self._toggle(Settings.scanner.skip_system),
        ))
        layout.addWidget(self._sep())
        layout.addWidget(self._row(
            "OCR Enabled",
            right=self._toggle(Settings.ocr.enabled),
        ))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("OCR Engine", value=Settings.ocr.engine))
        layout.addWidget(self._sep())
        layout.addWidget(self._row(
            "Categories Loaded",
            value=f"{len(Settings.categories)} rules",
        ))

        return card

    def _section_appearance(self) -> QFrame:
        card = self._card("Appearance")
        layout = self._card_body(card)

        layout.addWidget(self._row("Theme", right=self._combo(
            ["Dark", "Light"],
            current="Dark" if Settings.app.theme == "dark" else "Light",
        )))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("Embedding Model", value=Settings.search.embedding_model))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("Max Search Results", value=str(Settings.search.max_results)))

        return card

    def _section_privacy(self) -> QFrame:
        card = self._card("Privacy & Data")
        layout = self._card_body(card)

        layout.addWidget(self._row(
            "Local Processing Only",
            right=self._toggle(True),
            note="All AI runs on your device. No data leaves your machine.",
        ))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("Database", value=Settings.storage.db_filename))
        layout.addWidget(self._sep())

        clear_btn = QPushButton("Clear All Data")
        clear_btn.setObjectName("DangerButton")
        clear_btn.setFixedWidth(140)
        layout.addWidget(self._row("Reset DesktopAI", right=clear_btn))

        return card

    def _section_about(self) -> QFrame:
        card = self._card("About")
        layout = self._card_body(card)

        layout.addWidget(self._row("Application", value=APP_NAME))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("Version", value=f"v{APP_VERSION}"))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("Architecture", value="4-layer clean arch"))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("AI Stack", value="Ollama · FAISS · PySide6"))
        layout.addWidget(self._sep())
        layout.addWidget(self._row("Python", value="3.14+"))

        return card

    # ── Helpers ────────────────────────────────────────────────────

    def _card(self, title: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        # Title header inside card
        header = QWidget()
        header.setFixedHeight(44)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(18, 0, 18, 0)
        lbl = QLabel(title)
        lbl.setObjectName("SubHeading")
        h_layout.addWidget(lbl)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #3A3A3C; border: none;")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(header)
        outer.addWidget(sep)
        card._body_layout = outer
        return card

    def _card_body(self, card: QFrame) -> QVBoxLayout:
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(18, 4, 18, 12)
        layout.setSpacing(0)
        card._body_layout.addWidget(body)
        return layout

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.06); border: none;")
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
        row.setFixedHeight(44 if not note else 56)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        col = QVBoxLayout()
        col.setSpacing(1)
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #F5F5F7; font-size: 13px;")
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
            val.setStyleSheet("color: #6C6C70; font-size: 13px;")
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