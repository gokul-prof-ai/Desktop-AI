"""
DesktopAI v2.0 — Premium Design System
File: src/gui/theme/app_shell.py

Complete token-based theme system for DesktopAI.
Design language: Restrained premium utility app.
- Neutral surfaces dominate
- Single blue accent (#0A84FF dark / #007AFF light)
- No neon, no gradients, no clutter
- Every state has feedback
"""
from __future__ import annotations
from PySide6.QtWidgets import QApplication

THEMES = {
    "dark": {
        "bg":            "#1C1C1E",
        "sidebar":       "#161617",
        "surface":       "#2C2C2E",
        "surface_alt":   "#242426",
        "surface_hover": "#323234",
        "input":         "#242426",
        "text":          "#F5F5F7",
        "text_secondary":"#A1A1A6",
        "text_muted":    "#6C6C70",
        "border":        "#3A3A3C",
        "border_subtle": "#2C2C2E",
        "primary":       "#0A84FF",
        "primary_hover": "#2D95FF",
        "primary_muted": "#1C3A5C",
        "primary_wash":  "rgba(10,132,255,0.14)",
        "danger":        "#FF453A",
        "danger_wash":   "rgba(255,69,58,0.14)",
        "success":       "#30D158",
        "success_wash":  "rgba(48,209,88,0.14)",
        "warning":       "#FFD60A",
        "warning_wash":  "rgba(255,214,10,0.14)",
        "table_alt":     "#252527",
        "tag_bg":        "#323234",
        "scrollbar":     "#48484A",
        "nav_active_text": "#0A84FF",
        "nav_active_bg":   "rgba(10,132,255,0.14)",
        "nav_hover_bg":    "rgba(255,255,255,0.06)",
    },
    "light": {
        "bg":            "#F5F5F7",
        "sidebar":       "#EDEEF2",
        "surface":       "#FFFFFF",
        "surface_alt":   "#F1F2F4",
        "surface_hover": "#E8E9ED",
        "input":         "#FFFFFF",
        "text":          "#1D1D1F",
        "text_secondary":"#6E6E73",
        "text_muted":    "#8E8E93",
        "border":        "#D1D1D6",
        "border_subtle": "#E5E5EA",
        "primary":       "#007AFF",
        "primary_hover": "#0062CC",
        "primary_muted": "#D6E8FF",
        "primary_wash":  "rgba(0,122,255,0.10)",
        "danger":        "#FF3B30",
        "danger_wash":   "rgba(255,59,48,0.10)",
        "success":       "#34C759",
        "success_wash":  "rgba(52,199,89,0.10)",
        "warning":       "#FF9500",
        "warning_wash":  "rgba(255,149,0,0.10)",
        "table_alt":     "#F7F7F8",
        "tag_bg":        "#E5E5EA",
        "scrollbar":     "#C7C7CC",
        "nav_active_text": "#007AFF",
        "nav_active_bg":   "rgba(0,122,255,0.10)",
        "nav_hover_bg":    "rgba(0,0,0,0.04)",
    },
}

_QSS = """
/* ══ RESET ══════════════════════════════════════════════════════ */
* {
    font-family: "Segoe UI", "Inter", system-ui, sans-serif;
    font-size: 13px;
    outline: none;
}

/* ══ SHELL ═══════════════════════════════════════════════════════ */
QMainWindow,
QWidget#Root,
QWidget#Content {
    background: __BG__;
    color: __TEXT__;
}

/* ══ SIDEBAR ═════════════════════════════════════════════════════ */
QFrame#Sidebar {
    background: __SIDEBAR__;
    border-right: 1px solid __BORDER__;
}

QLabel#Brand {
    color: __TEXT__;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: -0.3px;
}

QLabel#BrandSubtitle {
    color: __TEXT_MUTED__;
    font-size: 11px;
    font-weight: 400;
}

QLabel#NavGroup {
    color: __TEXT_MUTED__;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.8px;
}

/* ══ NAVIGATION ══════════════════════════════════════════════════ */
QListWidget#NavList {
    background: transparent;
    border: none;
    outline: none;
}

QListWidget#NavList::item {
    color: __TEXT_SECONDARY__;
    background: transparent;
    border-radius: 7px;
    padding: 8px 12px;
    margin: 1px 6px;
    font-size: 13px;
    font-weight: 400;
}

QListWidget#NavList::item:hover {
    color: __TEXT__;
    background: __NAV_HOVER_BG__;
}

QListWidget#NavList::item:selected {
    color: __NAV_ACTIVE_TEXT__;
    background: __NAV_ACTIVE_BG__;
    font-weight: 600;
}

/* ══ PAGE HEADER ═════════════════════════════════════════════════ */
QLabel#PageTitle {
    color: __TEXT__;
    font-size: 21px;
    font-weight: 700;
    letter-spacing: -0.4px;
}

QLabel#PageSubtitle {
    color: __TEXT_SECONDARY__;
    font-size: 13px;
    font-weight: 400;
}

/* ══ CARDS ═══════════════════════════════════════════════════════ */
QFrame#Card {
    background: __SURFACE__;
    border: 1px solid __BORDER__;
    border-radius: 10px;
}

QFrame#StatCard {
    background: __SURFACE__;
    border: 1px solid __BORDER__;
    border-radius: 10px;
}

QLabel#StatValue {
    color: __TEXT__;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -0.5px;
}

QLabel#StatLabel {
    color: __TEXT_MUTED__;
    font-size: 11px;
    font-weight: 500;
}

/* ══ TYPOGRAPHY ══════════════════════════════════════════════════ */
QLabel#Heading {
    color: __TEXT__;
    font-size: 15px;
    font-weight: 600;
}

QLabel#SubHeading {
    color: __TEXT__;
    font-size: 13px;
    font-weight: 600;
}

QLabel#Muted {
    color: __TEXT_SECONDARY__;
    font-size: 12px;
}

QLabel#Caption {
    color: __TEXT_MUTED__;
    font-size: 11px;
}

/* ══ BUTTONS ═════════════════════════════════════════════════════ */
QPushButton {
    min-height: 32px;
    padding: 0 14px;
    border-radius: 7px;
    border: 1px solid __BORDER__;
    background: __SURFACE_ALT__;
    color: __TEXT__;
    font-size: 13px;
    font-weight: 400;
}

QPushButton:hover {
    background: __SURFACE_HOVER__;
}

QPushButton:pressed {
    background: __SURFACE_ALT__;
}

QPushButton:disabled {
    color: __TEXT_MUTED__;
    border-color: __BORDER_SUBTLE__;
    background: __SURFACE_ALT__;
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

QPushButton#PrimaryButton:disabled {
    background: __PRIMARY_MUTED__;
    border-color: __PRIMARY_MUTED__;
    color: rgba(255,255,255,0.4);
}

QPushButton#DangerButton {
    background: __DANGER_WASH__;
    border-color: __DANGER__;
    color: __DANGER__;
    font-weight: 600;
}

QPushButton#DangerButton:hover {
    background: __DANGER__;
    color: white;
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

QPushButton#GhostButton {
    background: transparent;
    border: none;
    color: __TEXT_SECONDARY__;
    padding: 0 10px;
}

QPushButton#GhostButton:hover {
    color: __PRIMARY__;
    background: __PRIMARY_WASH__;
    border-radius: 7px;
}

QPushButton#ThemeButton {
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    padding: 0;
    border-radius: 16px;
    background: __SURFACE_ALT__;
    border: 1px solid __BORDER__;
    font-size: 15px;
}

QPushButton#IconButton {
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    padding: 0;
    border-radius: 7px;
    background: transparent;
    border: none;
    color: __TEXT_SECONDARY__;
    font-size: 14px;
}

QPushButton#IconButton:hover {
    background: __SURFACE_HOVER__;
    color: __TEXT__;
}

/* ══ INPUTS ══════════════════════════════════════════════════════ */
QLineEdit,
QTextEdit,
QTextBrowser {
    background: __INPUT__;
    color: __TEXT__;
    border: 1px solid __BORDER__;
    border-radius: 8px;
    padding: 8px 12px;
    selection-background-color: __PRIMARY__;
    selection-color: white;
    font-size: 13px;
}

QLineEdit:focus,
QTextEdit:focus {
    border: 1.5px solid __PRIMARY__;
}

QLineEdit::placeholder {
    color: __TEXT_MUTED__;
}

/* ══ TABLES ══════════════════════════════════════════════════════ */
QTableWidget {
    background: __SURFACE__;
    alternate-background-color: __TABLE_ALT__;
    color: __TEXT__;
    border: 1px solid __BORDER__;
    border-radius: 10px;
    gridline-color: transparent;
    outline: none;
    font-size: 13px;
}

QTableWidget::item {
    padding: 9px 12px;
    border-bottom: 1px solid __BORDER_SUBTLE__;
}

QTableWidget::item:selected {
    background: __PRIMARY_WASH__;
    color: __TEXT__;
}

QTableWidget::item:hover {
    background: __SURFACE_HOVER__;
}

QHeaderView {
    background: __SURFACE__;
}

QHeaderView::section {
    background: __SURFACE_ALT__;
    color: __TEXT_MUTED__;
    border: none;
    border-bottom: 1px solid __BORDER__;
    padding: 8px 12px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.3px;
}

/* ══ TAGS / BADGES ═══════════════════════════════════════════════ */
QLabel#TagPrimary {
    color: __PRIMARY__;
    background: __PRIMARY_WASH__;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#TagSuccess {
    color: __SUCCESS__;
    background: __SUCCESS_WASH__;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#TagWarning {
    color: __WARNING__;
    background: __WARNING_WASH__;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#TagDanger {
    color: __DANGER__;
    background: __DANGER_WASH__;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#TagNeutral {
    color: __TEXT_SECONDARY__;
    background: __TAG_BG__;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 500;
}

/* ══ PROGRESS ════════════════════════════════════════════════════ */
QProgressBar {
    background: __SURFACE_ALT__;
    border: none;
    border-radius: 4px;
    max-height: 6px;
    text-align: center;
    font-size: 1px;
}

QProgressBar::chunk {
    background: __PRIMARY__;
    border-radius: 4px;
}

/* ══ COMBO ════════════════════════════════════════════════════════ */
QComboBox {
    background: __INPUT__;
    color: __TEXT__;
    border: 1px solid __BORDER__;
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 32px;
}

QComboBox:focus {
    border: 1.5px solid __PRIMARY__;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background: __SURFACE__;
    color: __TEXT__;
    border: 1px solid __BORDER__;
    border-radius: 8px;
    selection-background-color: __PRIMARY_WASH__;
    selection-color: __TEXT__;
    padding: 4px;
    outline: none;
}

/* ══ CHECKBOXES ══════════════════════════════════════════════════ */
QCheckBox {
    color: __TEXT__;
    spacing: 8px;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid __BORDER__;
    border-radius: 4px;
    background: __SURFACE_ALT__;
}

QCheckBox::indicator:checked {
    background: __PRIMARY__;
    border-color: __PRIMARY__;
}

/* ══ SCROLLBARS ══════════════════════════════════════════════════ */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: __SCROLLBAR__;
    border-radius: 3px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: __TEXT_MUTED__;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: transparent;
    height: 6px;
}

QScrollBar::handle:horizontal {
    background: __SCROLLBAR__;
    border-radius: 3px;
    min-width: 24px;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal { width: 0; }

/* ══ TOOLTIPS ════════════════════════════════════════════════════ */
QToolTip {
    background: __SURFACE__;
    color: __TEXT__;
    border: 1px solid __BORDER__;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 12px;
}

/* ══ DIALOGS ═════════════════════════════════════════════════════ */
QMessageBox {
    background: __SURFACE__;
    color: __TEXT__;
}

QMessageBox QLabel {
    color: __TEXT__;
    font-size: 13px;
}

/* ══ SEPARATORS ══════════════════════════════════════════════════ */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: __BORDER__;
    max-height: 1px;
    border: none;
}

/* ══ SPLITTER ════════════════════════════════════════════════════ */
QSplitter::handle {
    background: __BORDER__;
}
"""


def build_stylesheet(theme: str) -> str:
    t = THEMES.get(theme, THEMES["dark"])
    css = _QSS
    replacements = {
        "__BG__":             t["bg"],
        "__SIDEBAR__":        t["sidebar"],
        "__SURFACE__":        t["surface"],
        "__SURFACE_ALT__":    t["surface_alt"],
        "__SURFACE_HOVER__":  t["surface_hover"],
        "__INPUT__":          t["input"],
        "__TEXT__":           t["text"],
        "__TEXT_SECONDARY__": t["text_secondary"],
        "__TEXT_MUTED__":     t["text_muted"],
        "__BORDER__":         t["border"],
        "__BORDER_SUBTLE__":  t["border_subtle"],
        "__PRIMARY__":        t["primary"],
        "__PRIMARY_HOVER__":  t["primary_hover"],
        "__PRIMARY_MUTED__":  t["primary_muted"],
        "__PRIMARY_WASH__":   t["primary_wash"],
        "__DANGER__":         t["danger"],
        "__DANGER_WASH__":    t["danger_wash"],
        "__SUCCESS__":        t["success"],
        "__SUCCESS_WASH__":   t["success_wash"],
        "__WARNING__":        t["warning"],
        "__WARNING_WASH__":   t["warning_wash"],
        "__TABLE_ALT__":      t["table_alt"],
        "__TAG_BG__":         t["tag_bg"],
        "__SCROLLBAR__":      t["scrollbar"],
        "__NAV_ACTIVE_TEXT__":t["nav_active_text"],
        "__NAV_ACTIVE_BG__":  t["nav_active_bg"],
        "__NAV_HOVER_BG__":   t["nav_hover_bg"],
    }
    for k, v in replacements.items():
        css = css.replace(k, v)
    return css


def apply_theme(app: QApplication, theme: str) -> None:
    app.setStyleSheet(build_stylesheet(theme))
    for w in app.allWidgets():
        w.update()
