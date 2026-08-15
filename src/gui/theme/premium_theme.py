"""
DesktopAI v2.0 — Premium Theme Engine
File: src/gui/theme/premium_theme.py

Builds the complete application stylesheet from design tokens.
Establishes the layering: APP BG -> SIDEBAR -> SURFACE -> CARD -> COMPONENT.
"""
from __future__ import annotations
from string import Template

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication

from gui.theme.design_tokens import tokens_for, FONT, MONO, RADIUS

_QSS = Template("""
/* ── Base layering ─────────────────────────────────────────── */
QWidget { background-color: $app_bg; color: $text; font-family: $font; font-size: 14px; }
QMainWindow { background-color: $app_bg; }
QStackedWidget { background: transparent; }
QFrame#Root { background-color: $app_bg; }
QFrame#Sidebar { background-color: $sidebar_bg; border-right: 1px solid $border_subtle; }
QWidget#TopHeader { background-color: $app_bg; border-bottom: 1px solid $border_subtle; }
QWidget#Content { background-color: $app_bg; }

/* ── Brand / header text ───────────────────────────────────── */
QLabel#BrandName { color: $text; font-size: 15px; font-weight: 700; background: transparent; }
QLabel#BrandSub { color: $muted; font-size: 11px; background: transparent; }
QLabel#NavGroup { color: $muted; font-size: 10px; font-weight: 700; letter-spacing: 1px; background: transparent; }
QLabel#PageTitle { color: $text; font-size: 20px; font-weight: 700; background: transparent; }
QLabel#PageContext { color: $text_2; font-size: 12px; background: transparent; }
QLabel#Caption { color: $muted; font-size: 11px; background: transparent; }

/* ── Sidebar navigation ────────────────────────────────────── */
QListWidget#NavList { background: transparent; border: none; outline: none; }
QListWidget#NavList::item {
    color: $text_2; background: transparent; border-radius: $r_md px;
    padding: 9px 12px; margin: 2px 10px; border: 1px solid transparent;
}
QListWidget#NavList::item:hover { background-color: $nav_hover; color: $text; }
QListWidget#NavList::item:selected {
    background-color: $nav_active_bg; color: $nav_active_text;
    border: 1px solid $primary_soft; font-weight: 600;
}
QPushButton#ThemeButton {
    background: $surface; color: $text_2; border: 1px solid $border;
    border-radius: $r_md px; padding: 6px 10px;
}
QPushButton#ThemeButton:hover { color: $primary; border-color: $primary; }

/* ── Buttons (full state coverage) ─────────────────────────── */
QPushButton#daPrimary {
    background-color: $primary; color: #FFFFFF; border: none;
    border-radius: $r_md px; padding: 9px 18px; font-weight: 600;
}
QPushButton#daPrimary:hover { background-color: $primary_hover; }
QPushButton#daPrimary:pressed { background-color: $primary_pressed; }
QPushButton#daPrimary:focus { border: 2px solid $primary_hover; }
QPushButton#daPrimary:disabled { background-color: $border_subtle; color: $disabled; }
QPushButton#daSecondary {
    background-color: $surface; color: $text; border: 1px solid $border;
    border-radius: $r_md px; padding: 9px 18px; font-weight: 500;
}
QPushButton#daSecondary:hover { border-color: $primary; color: $primary; background-color: $primary_surface; }
QPushButton#daSecondary:pressed { background-color: $primary_soft; }
QPushButton#daSecondary:disabled { color: $disabled; border-color: $border_subtle; background: $surface_2; }
QPushButton#daGhost { background: transparent; color: $text_2; border: none; border-radius: $r_sm px; padding: 8px 12px; }
QPushButton#daGhost:hover { color: $primary; background-color: $primary_surface; }
QPushButton#daGhost:disabled { color: $disabled; }
QPushButton#daIcon { background: transparent; color: $text_2; border: 1px solid transparent; border-radius: $r_sm px; padding: 6px; }
QPushButton#daIcon:hover { background-color: $nav_hover; color: $text; border-color: $border_subtle; }

/* ── Cards & stats ─────────────────────────────────────────── */
QFrame#daCard, QFrame#daStatCard, QFrame#daProgressCard {
    background-color: $surface; border: 1px solid $border_subtle; border-radius: $r_lg px;
}
QFrame#daStatCard:hover, QFrame#daCard:hover { border-color: $border; }
QLabel#daStatIcon { color: $primary; font-size: 16px; background: transparent; }
QLabel#daStatValue { color: $text; font-size: 22px; font-weight: 700; background: transparent; }
QLabel#daStatLabel { color: $text_2; font-size: 12px; background: transparent; }
QLabel#daStatTrendOk { color: $success; font-size: 11px; background: transparent; }
QLabel#daStatTrendWarn { color: $warning; font-size: 11px; background: transparent; }
QLabel#daSectionTitle { color: $text; font-size: 15px; font-weight: 600; background: transparent; }
QLabel#daSectionSub { color: $text_2; font-size: 12px; background: transparent; }

/* ── States (empty / error / success) ──────────────────────── */
QFrame#daState { background-color: $surface_2; border: 1px dashed $border; border-radius: $r_hero px; }
QLabel#daStateIcon { font-size: 28px; background: transparent; }
QLabel#daStateIconOk { color: $success; }
QLabel#daStateIconErr { color: $error; }
QLabel#daStateIconInfo { color: $primary; }
QLabel#daStateTitle { color: $text; font-size: 15px; font-weight: 600; background: transparent; }
QLabel#daStateDesc { color: $text_2; font-size: 12px; background: transparent; }

/* ── Badges ────────────────────────────────────────────────── */
QLabel#daBadgeOk, QLabel#daBadgeWarn, QLabel#daBadgeErr, QLabel#daBadgeInfo, QLabel#daBadgeNeutral {
    border-radius: $r_sm px; padding: 3px 10px; font-size: 11px; font-weight: 600;
}
QLabel#daBadgeOk { background-color: $primary_soft; color: $success; }
QLabel#daBadgeWarn { background-color: $primary_soft; color: $warning; }
QLabel#daBadgeErr { background-color: $primary_soft; color: $error; }
QLabel#daBadgeInfo { background-color: $primary_soft; color: $info; }
QLabel#daBadgeNeutral { background-color: $surface_2; color: $text_2; border: 1px solid $border_subtle; }

/* ── Progress ─────────────────────────────────────────────── */
QProgressBar#daBar { background: $surface_2; border: 1px solid $border_subtle; border-radius: 5px; }
QProgressBar#daBar::chunk { background-color: $primary; border-radius: 5px; }
QLabel#daProgressText { color: $text_2; font-size: 12px; background: transparent; }

/* ── Tables ────────────────────────────────────────────────── */
QTableWidget#daTable {
    background-color: $surface; border: 1px solid $border_subtle; border-radius: $r_lg px;
    gridline-color: $border_subtle; color: $text; selection-background-color: $primary_soft;
}
QTableWidget#daTable::item { padding: 8px 10px; border-bottom: 1px solid $border_subtle; }
QTableWidget#daTable::item:hover { background-color: $row_hover; }
QHeaderView::section {
    background-color: $surface_2; color: $text_2; border: none;
    border-bottom: 1px solid $border; padding: 9px 10px; font-weight: 600; font-size: 11px;
}

/* ── Inputs ────────────────────────────────────────────────── */
QLineEdit, QTextEdit {
    background-color: $surface; color: $text; border: 1px solid $border;
    border-radius: $r_md px; padding: 9px 12px; selection-background-color: $primary;
}
QLineEdit:focus, QTextEdit:focus { border-color: $primary; }
QLineEdit::placeholder { color: $muted; }
QComboBox { background: $surface; color: $text; border: 1px solid $border; border-radius: $r_sm px; padding: 7px 10px; }
QComboBox:hover { border-color: $primary; }
QComboBox QAbstractItemView { background: $elevated; color: $text; border: 1px solid $border; }

/* ── Scrollbars ────────────────────────────────────────────── */
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: $border; border-radius: 5px; min-height: 32px; }
QScrollBar::handle:vertical:hover { background: $border_strong; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; }
QScrollBar::handle:horizontal { background: $border; border-radius: 5px; min-width: 32px; }

/* ── Toasts ────────────────────────────────────────────────── */
QFrame#daToast { background-color: $elevated; border: 1px solid $border; border-radius: $r_lg px; }
QLabel#daToastTitle { color: $text; font-weight: 600; font-size: 13px; background: transparent; }
QLabel#daToastMsg { color: $text_2; font-size: 12px; background: transparent; }
QLabel#daToastIconOk { color: $success; font-size: 15px; background: transparent; }
QLabel#daToastIconErr { color: $error; font-size: 15px; background: transparent; }
QLabel#daToastIconWarn { color: $warning; font-size: 15px; background: transparent; }
QLabel#daToastIconInfo { color: $info; font-size: 15px; background: transparent; }

QToolTip { background: $elevated; color: $text; border: 1px solid $border; border-radius: $r_sm px; padding: 6px 10px; }
""")


def build_qss(theme: str) -> str:
    t = tokens_for(theme)
    return _QSS.safe_substitute(
        font=FONT,
        r_sm=f"{RADIUS['sm']}", r_md=f"{RADIUS['md']}",
        r_lg=f"{RADIUS['lg']}", r_hero=f"{RADIUS['hero']}",
        **t,
    )


def apply_premium_theme(app: QApplication, theme: str) -> str:
    """Apply QSS + matching QPalette so default widgets follow too."""
    t = tokens_for(theme)
    app.setStyleSheet(build_qss(theme))

    p = QPalette()
    p.setColor(QPalette.Window, QColor(t["app_bg"]))
    p.setColor(QPalette.WindowText, QColor(t["text"]))
    p.setColor(QPalette.Base, QColor(t["surface"]))
    p.setColor(QPalette.AlternateBase, QColor(t["surface_2"]))
    p.setColor(QPalette.Text, QColor(t["text"]))
    p.setColor(QPalette.Button, QColor(t["surface"]))
    p.setColor(QPalette.ButtonText, QColor(t["text"]))
    p.setColor(QPalette.Highlight, QColor(t["primary"]))
    p.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    p.setColor(QPalette.PlaceholderText, QColor(t["muted"]))
    p.setColor(QPalette.Mid, QColor(t["border"]))
    p.setColor(QPalette.Midlight, QColor(t["border_subtle"]))
    p.setColor(QPalette.Dark, QColor(t["text_2"]))
    p.setColor(QPalette.Disabled, QPalette.Text, QColor(t["disabled"]))
    app.setPalette(p)
    return theme