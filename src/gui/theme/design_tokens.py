"""
DesktopAI v2.0 — Central Design Tokens
File: src/gui/theme/design_tokens.py

Semantic tokens for Light + Dark themes, spacing, radius,
typography and animation scales. Consumed by premium_theme.py
and all reusable components. No widget ever hardcodes hexes.
"""
from __future__ import annotations

LIGHT = {
    "app_bg": "#F3F4F7", "sidebar_bg": "#ECEEF2",
    "surface": "#FFFFFF", "surface_2": "#F8F9FB", "elevated": "#FFFFFF",
    "border": "#D9DDE5", "border_strong": "#C7CBD4", "border_subtle": "#E5E7EB",
    "text": "#171923", "text_2": "#5F6675", "muted": "#858C99", "disabled": "#A5ABB5",
    "primary": "#7C3AED", "primary_hover": "#6D28D9", "primary_pressed": "#5B21B6",
    "primary_soft": "#EDE9FE", "primary_surface": "#F5F3FF",
    "success": "#16A34A", "warning": "#D97706", "error": "#DC2626", "info": "#2563EB",
    "nav_active_bg": "#EDE7FF", "nav_active_text": "#6D28D9", "nav_hover": "#F3F1F7",
    "row_hover": "#F7F5FF",
}

DARK = {
    "app_bg": "#0D0D12", "sidebar_bg": "#101017",
    "surface": "#13131A", "surface_2": "#16161F", "elevated": "#1A1A24",
    "border": "#262637", "border_strong": "#32324A", "border_subtle": "#1E1E2C",
    "text": "#E8E8F0", "text_2": "#A0A3BD", "muted": "#6B6E8A", "disabled": "#4B4E66",
    "primary": "#8B5CF6", "primary_hover": "#9D78FF", "primary_pressed": "#7C3AED",
    "primary_soft": "rgba(139,92,246,0.16)", "primary_surface": "#171429",
    "success": "#34D399", "warning": "#FBBF24", "error": "#F87171", "info": "#60A5FA",
    "nav_active_bg": "rgba(139,92,246,0.16)", "nav_active_text": "#C4B5FD",
    "nav_hover": "rgba(255,255,255,0.04)", "row_hover": "rgba(139,92,246,0.08)",
}

SPACING = {"xs": 4, "sm": 8, "md": 12, "base": 16, "lg": 20, "xl": 24, "xxl": 32, "xxxl": 40}
RADIUS = {"sm": 6, "md": 10, "lg": 14, "hero": 18}
FONT = "'Segoe UI', 'Inter', sans-serif"
MONO = "'Cascadia Mono', 'JetBrains Mono', monospace"
ANIM = {"fast": 120, "normal": 180, "slow": 250}


def tokens_for(theme: str) -> dict:
    return LIGHT if theme == "light" else DARK