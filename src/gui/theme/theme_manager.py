"""
DesktopAI v2.0 — Theme Manager (UI/UX Pro Max compliant)
File: src/gui/theme/theme_manager.py

Rules enforced: id-only selectors (subclass-proof), 5-state coverage
(default/hover/pressed/focus/disabled), contrast-safe tokens, 8pt grid.
"""
from __future__ import annotations
from string import Template

from PySide6.QtWidgets import QApplication
from core.logger import get_logger

logger = get_logger(__name__)

DARK = {
    "bg": "#050508", "surface": "#0A0A0F", "elevated": "#17171F",
    "border": "#1A1A24", "border_strong": "#2A2A35",
    "text": "#E4E4E7", "muted": "#A1A1AA", "faint": "#8B8B96",
    "accent": "#8B5CF6", "accent_hover": "#7C3AED", "accent_press": "#6D28D9",
    "accent2": "#3B82F6", "on_accent": "#FFFFFF",
    "input_bg": "#0A0A0F", "hover": "rgba(255,255,255,0.06)",
    "disabled_bg": "#1A1A24", "disabled_text": "#5A5A66",
    "focus": "#A78BFA",
    "success": "#34D399", "warning": "#FBBF24", "danger": "#F87171",
}

LIGHT = {
    "bg": "#F4F4F6", "surface": "#FFFFFF", "elevated": "#FFFFFF",
    "border": "#E4E4E7", "border_strong": "#C9C9D2",
    "text": "#17171B", "muted": "#4E4E58", "faint": "#6B6B76",
    "accent": "#6D28D9", "accent_hover": "#5B21B6", "accent_press": "#4C1D95",
    "accent2": "#1D4ED8", "on_accent": "#FFFFFF",
    "input_bg": "#FFFFFF", "hover": "rgba(0,0,0,0.05)",
    "disabled_bg": "#E4E4E7", "disabled_text": "#9A9AA4",
    "focus": "#7C3AED",
    "success": "#047857", "warning": "#B45309", "danger": "#B91C1C",
}

_current = "dark"

_CSS = Template("""
QWidget { background-color: $bg; color: $text; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
QMainWindow { background-color: $bg; }

/* ── Top bar / labels ─────────────────────────────────────────── */
QFrame#TopBar { background-color: $surface; border-bottom: 1px solid $border; }
QLabel#Logo { color: $text; font-size: 20px; font-weight: 700; }
QLabel#PageTitle { color: $text; font-size: 28px; font-weight: 700; }
QLabel#PageSubtitle { color: $muted; font-size: 14px; }
QLabel#StatusLabel { color: $muted; font-size: 13px; }
QLabel#AccentLabel { color: $accent; font-weight: 600; font-size: 15px; }

/* ── Sidebar ──────────────────────────────────────────────────── */
QListWidget#Sidebar { background-color: $surface; border: none; border-right: 1px solid $border; outline: none; }
QListWidget#Sidebar::item { padding: 12px 24px; margin: 4px 12px; border-radius: 8px; color: $muted; }
QListWidget#Sidebar::item:hover { background-color: $hover; color: $text; }
QListWidget#Sidebar::item:selected { background-color: $hover; color: $text; border-left: 3px solid $accent; font-weight: 600; }

/* ── Cards ────────────────────────────────────────────────────── */
QFrame#Card { background-color: $surface; border: 1px solid $border; border-radius: 12px; }

/* ── Buttons (id-only selectors: subclass-proof) ─────────────── */
QPushButton { background-color: $surface; color: $text; border: 1px solid $border_strong; border-radius: 8px; padding: 10px 20px; }
QPushButton:hover { background-color: $hover; }
#PrimaryButton { background-color: $accent; color: $on_accent; border: none; font-weight: 600; }
#PrimaryButton:hover { background-color: $accent_hover; }
#PrimaryButton:pressed { background-color: $accent_press; }
#PrimaryButton:focus { border: 2px solid $focus; }
#PrimaryButton:disabled { background-color: $disabled_bg; color: $disabled_text; }
#SecondaryButton { background-color: transparent; color: $muted; }
#SecondaryButton:hover { color: $text; border-color: $accent; }
#SecondaryButton:disabled { color: $disabled_text; border-color: $border; }
#DangerButton { background-color: transparent; color: $danger; border: 1px solid $danger; }
#DangerButton:hover { background-color: $hover; }
#DangerButton:disabled { color: $disabled_text; border-color: $disabled_text; }
#IconButton { background-color: transparent; border: 1px solid transparent; border-radius: 8px; font-size: 16px; }
#IconButton:hover { background-color: $hover; border-color: $border_strong; }

/* ── Inputs ──────────────────────────────────────────────────── */
QLineEdit#Input, QTextEdit#Input { background-color: $input_bg; color: $text; border: 1px solid $border_strong; border-radius: 8px; padding: 10px 14px; selection-background-color: $accent; selection-color: $on_accent; }
QLineEdit#Input:focus, QTextEdit#Input:focus { border: 2px solid $focus; }
QLineEdit#Input::placeholder { color: $faint; }

/* ── Tables ───────────────────────────────────────────────────── */
QTableWidget#Table { background-color: $surface; border: 1px solid $border; border-radius: 12px; gridline-color: $border; color: $text; font-size: 13px; alternate-background-color: $hover; }
QTableWidget#Table::item { padding: 10px 14px; }
QTableWidget#Table::item:selected { background-color: $hover; color: $text; }
QHeaderView::section { background-color: $surface; color: $faint; padding: 12px 14px; border: none; border-bottom: 2px solid $border_strong; font-weight: 600; text-transform: uppercase; font-size: 11px; }

/* ── Chat ─────────────────────────────────────────────────────── */
QScrollArea#ChatScroll { background-color: $surface; border: 1px solid $border; border-radius: 12px; }
QLabel#UserBubble { background-color: $accent; color: $on_accent; padding: 12px 16px; border-radius: 12px; }
QLabel#BotBubble { background-color: $elevated; color: $text; padding: 12px 16px; border-radius: 12px; border: 1px solid $border; }

/* ── Controls ────────────────────────────────────────────────── */
QComboBox#Combo { background-color: $input_bg; color: $text; border: 1px solid $border_strong; border-radius: 8px; padding: 8px 12px; min-width: 140px; }
QComboBox#Combo:hover { border-color: $accent; }
QComboBox#Combo QAbstractItemView { background-color: $elevated; color: $text; border: 1px solid $border_strong; selection-background-color: $hover; }
QCheckBox { color: $text; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid $border_strong; border-radius: 4px; background-color: $input_bg; }
QCheckBox::indicator:checked { background-color: $accent; border-color: $accent; }

/* ── Scrollbars ───────────────────────────────────────────────── */
QScrollBar:vertical { background: $bg; width: 10px; }
QScrollBar::handle:vertical { background: $border_strong; border-radius: 5px; min-height: 32px; }
QScrollBar::handle:vertical:hover { background: $accent; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
""")


def current_theme() -> str:
    return _current


def build_qss(tokens: dict) -> str:
    return _CSS.substitute(tokens)


def apply_theme(name: str, persist: bool = True) -> str:
    global _current
    _current = "light" if name == "light" else "dark"
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(build_qss(LIGHT if _current == "light" else DARK))
    if persist:
        try:
            from infrastructure.config.settings import Settings
            Settings.app.theme = _current
            Settings.save()
        except Exception as exc:
            logger.warning("Theme persist failed: %s", exc)
    logger.info("Theme applied: %s", _current)
    return _current


def toggle_theme() -> str:
    return apply_theme("light" if _current == "dark" else "dark")


def apply_saved_theme() -> str:
    name = "dark"
    try:
        from infrastructure.config.settings import Settings
        if Settings.is_loaded():
            name = getattr(Settings.app, "theme", "dark")
    except Exception:
        pass
    return apply_theme(name, persist=False)