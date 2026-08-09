"""
DesktopAI v2.0 — Theme Manager
File: src/gui/theme/theme_manager.py

Single source of truth for colors. Generates the full QSS from a token
dict so dark AND light themes restyle every objectName-styled widget.
"""
from __future__ import annotations
from string import Template

from PySide6.QtWidgets import QApplication
from core.logger import get_logger

logger = get_logger(__name__)

DARK = {
    "bg": "#050508", "surface": "#0A0A0F", "elevated": "#1A1A24",
    "border": "#1A1A24", "border_strong": "#2A2A35",
    "text": "#E4E4E7", "muted": "#A1A1AA", "faint": "#71717A",
    "accent": "#8B5CF6", "accent2": "#3B82F6",
    "input_bg": "#0A0A0F", "hover": "rgba(255,255,255,0.05)",
    "success": "#10B981", "warning": "#F59E0B", "danger": "#EF4444",
    "on_accent": "#FFFFFF",
}

LIGHT = {
    "bg": "#F5F5F7", "surface": "#FFFFFF", "elevated": "#FFFFFF",
    "border": "#E4E4E7", "border_strong": "#D4D4D8",
    "text": "#18181B", "muted": "#52525B", "faint": "#71717A",
    "accent": "#7C3AED", "accent2": "#2563EB",
    "input_bg": "#FFFFFF", "hover": "rgba(0,0,0,0.04)",
    "success": "#059669", "warning": "#D97706", "danger": "#DC2626",
    "on_accent": "#FFFFFF",
}

_current = "dark"

_CSS = Template("""
QWidget { background-color: $bg; color: $text; font-family: 'Segoe UI', sans-serif; }
QMainWindow { background-color: $bg; }
QFrame#TopBar { background-color: $surface; border-bottom: 1px solid $border; }
QLabel#Logo { color: $text; font-size: 20px; font-weight: 700; }
QLabel#PageTitle { color: $text; font-size: 28px; font-weight: 700; }
QLabel#PageSubtitle { color: $muted; font-size: 14px; }
QLabel#StatusLabel { color: $faint; font-size: 14px; }
QLabel#AccentLabel { color: $accent; font-weight: 600; }
QListWidget#Sidebar { background-color: $surface; border: none; border-right: 1px solid $border; outline: none; }
QListWidget#Sidebar::item { padding: 12px 24px; margin: 4px 12px; border-radius: 8px; color: $muted; font-size: 14px; }
QListWidget#Sidebar::item:hover { background-color: $hover; color: $text; }
QListWidget#Sidebar::item:selected { background-color: $hover; color: $text; border-left: 3px solid $accent; font-weight: 600; }
QFrame#Card { background-color: $surface; border: 1px solid $border; border-radius: 12px; }
QPushButton#PrimaryButton { background-color: $accent; color: $on_accent; border: none; border-radius: 8px; font-weight: 600; padding: 10px 20px; }
QPushButton#PrimaryButton:hover { background-color: $accent2; }
QPushButton#PrimaryButton:disabled { background-color: $border_strong; color: $faint; }
QPushButton#SecondaryButton { background-color: transparent; color: $muted; border: 1px solid $border_strong; border-radius: 8px; font-weight: 600; padding: 10px 20px; }
QPushButton#SecondaryButton:hover { color: $text; border-color: $accent; }
QPushButton#SecondaryButton:disabled { color: $faint; border-color: $border; }
QPushButton#DangerButton { background-color: transparent; color: $danger; border: 1px solid $danger; border-radius: 8px; font-weight: 600; padding: 10px 20px; }
QPushButton#DangerButton:hover { background-color: $hover; }
QPushButton#DangerButton:disabled { color: $faint; border-color: $faint; }
QPushButton#IconButton { background-color: transparent; border: 1px solid transparent; border-radius: 8px; font-size: 16px; }
QPushButton#IconButton:hover { background-color: $hover; border-color: $border_strong; }
QLineEdit#Input, QTextEdit#Input { background-color: $input_bg; color: $text; border: 1px solid $border_strong; border-radius: 8px; padding: 10px 14px; }
QLineEdit#Input:focus, QTextEdit#Input:focus { border-color: $accent; }
QTableWidget#Table { background-color: $surface; border: 1px solid $border; border-radius: 12px; gridline-color: $border; color: $text; font-size: 13px; }
QTableWidget#Table::item { padding: 10px 14px; border-bottom: 1px solid $border; }
QHeaderView::section { background-color: $surface; color: $faint; padding: 12px 14px; border: none; border-bottom: 2px solid $border_strong; font-weight: 600; text-transform: uppercase; font-size: 11px; }
QLabel#UserBubble { background-color: $accent; color: $on_accent; padding: 12px 16px; border-radius: 12px; }
QLabel#BotBubble { background-color: $elevated; color: $text; padding: 12px 16px; border-radius: 12px; border: 1px solid $border; }
QScrollArea#ChatScroll { background-color: $surface; border: 1px solid $border; border-radius: 12px; }
QScrollBar:vertical { background: $surface; width: 8px; }
QScrollBar::handle:vertical { background: $border_strong; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QComboBox#Combo { background-color: $input_bg; color: $text; border: 1px solid $border_strong; border-radius: 8px; padding: 8px 12px; min-width: 140px; }
QComboBox#Combo:hover { border-color: $accent; }
QComboBox#Combo QAbstractItemView { background-color: $elevated; color: $text; border: 1px solid $border_strong; }
QCheckBox { color: $text; spacing: 8px; }
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