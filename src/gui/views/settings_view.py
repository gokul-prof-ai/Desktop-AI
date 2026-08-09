"""
DesktopAI v2.0 — Settings View (App Shell UI)
File: src/gui/views/settings_view.py

Settings-type layout:
  - AI Configuration section
  - Scanner section
  - About section
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QComboBox, QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from infrastructure.config.settings import Settings

_PAD = 24


class SettingsView(QWidget):
    """Application settings screen."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(_PAD, _PAD, _PAD, _PAD)
        root.setSpacing(16)

        # Sub-header
        sub = QLabel("Configure AI models, scanner behaviour, and preferences.")
        sub.setStyleSheet("color: #A1A1A6; font-size: 13px;")
        root.addWidget(sub)

        # Scrollable settings area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(12)

        inner_layout.addWidget(self._build_ai_section())
        inner_layout.addWidget(self._build_scanner_section())
        inner_layout.addWidget(self._build_about_section())
        inner_layout.addStretch()

        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

    # ── Sections ───────────────────────────────────────────────────

    def _build_ai_section(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(0)

        layout.addWidget(self._section_title("AI Configuration"))
        layout.addSpacing(12)
        layout.addWidget(self._separator())
        layout.addSpacing(12)

        layout.addWidget(
            self._row("Model", Settings.ai.model,
                      right=self._model_combo())
        )
        layout.addWidget(self._separator())
        layout.addWidget(
            self._row("Fast Model", Settings.ai.model_fast)
        )
        layout.addWidget(self._separator())
        layout.addWidget(
            self._row("Ollama Host", Settings.ai.host)
        )

        return card

    def _build_scanner_section(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(0)

        layout.addWidget(self._section_title("Scanner"))
        layout.addSpacing(12)
        layout.addWidget(self._separator())
        layout.addSpacing(12)

        layout.addWidget(
            self._row("Max Depth", str(Settings.scanner.max_depth))
        )
        layout.addWidget(self._separator())
        layout.addWidget(
            self._row("Max Workers", str(Settings.scanner.max_workers))
        )
        layout.addWidget(self._separator())
        layout.addWidget(
            self._row("Skip Hidden Files",
                      "Yes" if Settings.scanner.skip_hidden else "No")
        )
        layout.addWidget(self._separator())
        layout.addWidget(
            self._row("OCR Enabled",
                      "Yes" if Settings.ocr.enabled else "No")
        )

        return card

    def _build_about_section(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(0)

        layout.addWidget(self._section_title("About"))
        layout.addSpacing(12)
        layout.addWidget(self._separator())
        layout.addSpacing(12)

        from core.constants import APP_VERSION
        layout.addWidget(self._row("Version", f"v{APP_VERSION}"))
        layout.addWidget(self._separator())
        layout.addWidget(self._row("Architecture", "4-layer clean arch (V2)"))
        layout.addWidget(self._separator())
        layout.addWidget(self._row("Categories", f"{len(Settings.categories)} rules loaded"))

        return card

    # ── Helpers ────────────────────────────────────────────────────

    def _section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color: #F5F5F7; font-size: 13px; font-weight: 600;"
        )
        return lbl

    def _separator(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(
            "background: rgba(255,255,255,0.08); border: none;"
        )
        return sep

    def _row(
        self,
        label: str,
        value: str = "",
        right: QWidget | None = None,
    ) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        row.setFixedHeight(44)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #F5F5F7; font-size: 13px;")
        layout.addWidget(lbl)

        layout.addStretch()

        if right:
            layout.addWidget(right)
        else:
            val = QLabel(value)
            val.setStyleSheet("color: #6C6C70; font-size: 13px;")
            layout.addWidget(val)

        return row

    def _model_combo(self) -> QComboBox:
        combo = QComboBox()
        combo.addItems([
            "llama3.2",
            "llama3.2:1b",
            "mistral",
            "gemma2",
        ])
        combo.setCurrentText(Settings.ai.model)
        combo.setFixedWidth(140)
        return combo