"""
DesktopAI v2.0 — App Shell UI Design Tokens
File: src/gui/theme/tokens.py

Implements the App Shell UI token system for PySide6.
Follows the macOS system-utility aesthetic:
  - Soft neutral canvas (not pure black)
  - Single brand accent (#007AFF / #0A84FF)
  - Light + dark themes as first-class citizens
  - Stroke icons, raised cards, 1px borders
"""
from __future__ import annotations

# ── Light Theme ────────────────────────────────────────────────────
LIGHT = {
    # Surfaces
    "bg_app":      "#F4F5F7",
    "bg_sidebar":  "#EEF0F3",
    "bg_surface":  "#FFFFFF",
    "bg_muted":    "#F7F8FA",
    "bg_hover":    "rgba(0, 0, 0, 0.04)",
    "bg_selected": "rgba(0, 122, 255, 0.12)",

    # Text
    "text_primary":   "#1C1C1E",
    "text_secondary": "#636366",
    "text_tertiary":  "#8E8E93",
    "text_success":   "#34C759",
    "text_warning":   "#FF9F0A",
    "text_danger":    "#FF3B30",

    # Brand
    "primary":             "#007AFF",
    "primary_foreground":  "#FFFFFF",

    # Borders
    "border":        "rgba(0, 0, 0, 0.08)",
    "border_strong": "rgba(0, 0, 0, 0.14)",

    # Controls
    "toggle_off":        "rgba(0, 0, 0, 0.12)",
    "seg_track":         "rgba(0, 0, 0, 0.05)",
    "secondary_btn_bg":  "rgba(0, 0, 0, 0.06)",

    # Sidebar
    "titlebar_bg": "#FAFBFC",
    "window_outer_bg": "#D8DDE6",
}

# ── Dark Theme ─────────────────────────────────────────────────────
DARK = {
    # Surfaces
    "bg_app":      "#1C1C1E",
    "bg_sidebar":  "#161617",
    "bg_surface":  "#2C2C2E",
    "bg_muted":    "#3A3A3C",
    "bg_hover":    "rgba(255, 255, 255, 0.06)",
    "bg_selected": "rgba(10, 132, 255, 0.22)",

    # Text
    "text_primary":   "#F5F5F7",
    "text_secondary": "#A1A1A6",
    "text_tertiary":  "#6C6C70",
    "text_success":   "#30D158",
    "text_warning":   "#FFD60A",
    "text_danger":    "#FF453A",

    # Brand
    "primary":             "#0A84FF",
    "primary_foreground":  "#FFFFFF",

    # Borders
    "border":        "rgba(255, 255, 255, 0.08)",
    "border_strong": "rgba(255, 255, 255, 0.14)",

    # Controls
    "toggle_off":        "rgba(255, 255, 255, 0.18)",
    "seg_track":         "rgba(255, 255, 255, 0.08)",
    "secondary_btn_bg":  "rgba(255, 255, 255, 0.10)",

    # Sidebar
    "titlebar_bg": "#2C2C2E",
    "window_outer_bg": "#0B0B0C",
}

# ── Shared (theme-independent) ─────────────────────────────────────
RADIUS = {"sm": 8, "md": 12, "lg": 16, "full": 9999}
SPACING = {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32}
SIDEBAR_WIDTH = 240
CONTENT_PADDING = 24

# Status colors for confidence pills
CONFIDENCE_HIGH = "#34C759"    # >= 80%
CONFIDENCE_MED  = "#FF9F0A"    # >= 50%
CONFIDENCE_LOW  = "#FF3B30"    # < 50%


def get_theme(name: str = "dark") -> dict:
    """Return the token dict for 'light' or 'dark'."""
    return DARK if name == "dark" else LIGHT