"""
DesktopAI v2.0
App Shell UI theme system.

Inspired by the app-shell-ui design rules:

    - Desktop utility shell
    - Soft light/dark surfaces
    - One primary accent
    - Restrained borders
    - No rainbow gradients
    - No emoji-heavy navigation
    - Theme switch persistence
"""

from __future__ import annotations

from PySide6.QtWidgets import QApplication


THEMES = {
    "dark": {
        "bg": "#1C1C1E",
        "sidebar": "#161617",
        "surface": "#2C2C2E",
        "surface_alt": "#242426",
        "input": "#242426",
        "text": "#F5F5F7",
        "text_secondary": "#A1A1A6",
        "text_muted": "#6C6C70",
        "border": "#3A3A3C",
        "primary": "#0A84FF",
        "primary_hover": "#2D95FF",
        "primary_wash": "rgba(10,132,255,0.18)",
        "danger": "#FF453A",
        "success": "#30D158",
        "warning": "#FFD60A",
        "table_alt": "#29292B",
    },
    "light": {
        "bg": "#F5F5F7",
        "sidebar": "#EDEEF2",
        "surface": "#FFFFFF",
        "surface_alt": "#F1F2F4",
        "input": "#FFFFFF",
        "text": "#1D1D1F",
        "text_secondary": "#6E6E73",
        "text_muted": "#8E8E93",
        "border": "#D9D9DE",
        "primary": "#007AFF",
        "primary_hover": "#006FE6",
        "primary_wash": "rgba(0,122,255,0.12)",
        "danger": "#FF3B30",
        "success": "#34C759",
        "warning": "#FF9500",
        "table_alt": "#F7F7F8",
    },
}


_BASE_QSS = """
* {
    font-family: "Segoe UI", "Inter", sans-serif;
}

QMainWindow,
QWidget#Root,
QWidget#Content {
    background: __BG__;
    color: __TEXT__;
}

QFrame#Sidebar {
    background: __SIDEBAR__;
    border-right: 1px solid __BORDER__;
}

QLabel#Brand {
    color: __TEXT__;
    font-size: 19px;
    font-weight: 700;
}

QLabel#BrandSubtitle {
    color: __TEXT_MUTED__;
    font-size: 11px;
}

QLabel#PageTitle {
    color: __TEXT__;
    font-size: 25px;
    font-weight: 700;
}

QLabel#PageSubtitle {
    color: __TEXT_SECONDARY__;
    font-size: 13px;
}

QListWidget#NavList {
    background: transparent;
    border: none;
    outline: none;
}

QListWidget#NavList::item {
    color: __TEXT_SECONDARY__;
    background: transparent;
    border-radius: 8px;
    padding: 10px 12px;
    margin: 2px 8px;
    font-size: 13px;
}

QListWidget#NavList::item:hover {
    color: __TEXT__;
    background: __SURFACE_ALT__;
}

QListWidget#NavList::item:selected {
    color: __PRIMARY__;
    background: __PRIMARY_WASH__;
}

QFrame#Card {
    background: __SURFACE__;
    border: 1px solid __BORDER__;
    border-radius: 12px;
}

QFrame#StatCard {
    background: __SURFACE__;
    border: 1px solid __BORDER__;
    border-radius: 12px;
}

QLabel#StatValue {
    color: __TEXT__;
    font-size: 25px;
    font-weight: 700;
}

QLabel#StatLabel {
    color: __TEXT_MUTED__;
    font-size: 12px;
}

QLabel#Heading {
    color: __TEXT__;
    font-size: 16px;
    font-weight: 600;
}

QLabel#Muted {
    color: __TEXT_SECONDARY__;
    font-size: 12px;
}

QPushButton {
    min-height: 36px;
    padding: 0 16px;
    border-radius: 8px;
    border: 1px solid __BORDER__;
    background: __SURFACE_ALT__;
    color: __TEXT__;
    font-size: 13px;
}

QPushButton:hover {
    border-color: __PRIMARY__;
}

QPushButton#PrimaryButton {
    background: __PRIMARY__;
    border-color: __PRIMARY__;
    color: white;
    font-weight: 600;
}

QPushButton#PrimaryButton:hover {
    background: __PRIMARY_HOVER__;
    border-color: __PRIMARY_HOVER__;
}

QPushButton#SecondaryButton {
    background: transparent;
    border: 1px solid __BORDER__;
    color: __TEXT_SECONDARY__;
}

QPushButton#SecondaryButton:hover {
    background: __PRIMARY_WASH__;
    color: __PRIMARY__;
    border-color: __PRIMARY__;
}

QPushButton#ThemeButton {
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
    padding: 0;
    border-radius: 18px;
    background: __SURFACE_ALT__;
    border: 1px solid __BORDER__;
    font-size: 17px;
}

QLineEdit,
QTextEdit,
QTextBrowser {
    background: __INPUT__;
    color: __TEXT__;
    border: 1px solid __BORDER__;
    border-radius: 10px;
    padding: 10px;
    selection-background-color: __PRIMARY__;
    selection-color: white;
}

QLineEdit:focus,
QTextEdit:focus,
QTextBrowser:focus {
    border: 1px solid __PRIMARY__;
}

QTableWidget {
    background: __SURFACE__;
    alternate-background-color: __TABLE_ALT__;
    color: __TEXT__;
    border: 1px solid __BORDER__;
    border-radius: 10px;
    gridline-color: transparent;
    outline: none;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid __BORDER__;
}

QTableWidget::item:selected {
    background: __PRIMARY_WASH__;
    color: __TEXT__;
}

QHeaderView::section {
    background: __SURFACE_ALT__;
    color: __TEXT_SECONDARY__;
    border: none;
    border-bottom: 1px solid __BORDER__;
    padding: 9px;
    font-size: 11px;
    font-weight: 600;
}

QCheckBox {
    color: __TEXT__;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid __BORDER__;
    border-radius: 5px;
    background: __SURFACE_ALT__;
}

QCheckBox::indicator:checked {
    background: __PRIMARY__;
    border-color: __PRIMARY__;
}

QProgressBar {
    background: __SURFACE_ALT__;
    border: none;
    border-radius: 5px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: __PRIMARY__;
    border-radius: 5px;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
}

QScrollBar::handle:vertical {
    background: __BORDER__;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QMessageBox {
    background: __SURFACE__;
    color: __TEXT__;
}

QToolTip {
    background: __SURFACE__;
    color: __TEXT__;
    border: 1px solid __BORDER__;
    padding: 6px 8px;
}
"""


def build_stylesheet(theme: str) -> str:
    """Build the complete QSS for a theme."""

    theme = theme if theme in THEMES else "dark"

    values = THEMES[theme]

    stylesheet = _BASE_QSS

    replacements = {
        "__BG__": values["bg"],
        "__SIDEBAR__": values["sidebar"],
        "__SURFACE__": values["surface"],
        "__SURFACE_ALT__": values["surface_alt"],
        "__INPUT__": values["input"],
        "__TEXT__": values["text"],
        "__TEXT_SECONDARY__": values["text_secondary"],
        "__TEXT_MUTED__": values["text_muted"],
        "__BORDER__": values["border"],
        "__PRIMARY__": values["primary"],
        "__PRIMARY_HOVER__": values["primary_hover"],
        "__PRIMARY_WASH__": values["primary_wash"],
        "__TABLE_ALT__": values["table_alt"],
    }

    for key, value in replacements.items():
        stylesheet = stylesheet.replace(key, value)

    return stylesheet


def apply_theme(
    app: QApplication,
    theme: str,
) -> None:
    """Apply a theme to the entire application."""

    app.setStyleSheet(
        build_stylesheet(theme)
    )

    for widget in app.allWidgets():
        widget.update()