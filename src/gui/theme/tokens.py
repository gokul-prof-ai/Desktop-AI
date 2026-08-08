"""
DesktopAI v2.0 — UI Theme Tokens
File: src/gui/theme/tokens.py

The single source of truth for the application's visual design.
Implements the "Spatial Glass Neomorphism" aesthetic.
"""
from __future__ import annotations

# ── Color Palette ──────────────────────────────────────────────────
PALETTE = {
    # Backgrounds
    "bg_base": "#0D0D12",       # App background (near-black)
    "bg_surface": "#13131A",    # Cards, panels
    "bg_elevated": "#1A1A24",   # Modals, dropdowns, sidebar
    "bg_input": "#0F0F17",      # Input fields
    
    # Neomorphic Shadows (simulated via borders in QSS)
    "shadow_dark": "#08080D",   # Bottom-right inner shadow
    "shadow_light": "#1F1F2E",  # Top-left inner highlight
    
    # Accent (AI Blue → shifts during processing)
    "accent_idle": "#4F8EF7",   # Primary blue
    "accent_think": "#00C4FF",  # Cyan — AI is working
    "accent_done": "#34D399",   # Green — complete
    "accent_warn": "#FBBF24",   # Amber — warning
    "accent_error": "#F87171",  # Red — error
    
    # Text Hierarchy
    "text_primary": "#E8E8F0",
    "text_secondary": "#8B8BA8",
    "text_muted": "#4B4B6B",
    "text_on_accent": "#0D0D12",
}

# ── Spacing Scale ──────────────────────────────────────────────────
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 40,
    "2xl": 64,
}

# ── Border Radius ──────────────────────────────────────────────────
RADIUS = {
    "sm": 6,
    "md": 12,
    "lg": 20,
    "full": 9999,
}

# ── Typography ─────────────────────────────────────────────────────
TYPOGRAPHY = {
    "font_family": "'Inter', 'Segoe UI', sans-serif",
    "mono_family": "'JetBrains Mono', 'Consolas', monospace",
    "size_xs": 10,
    "size_sm": 12,
    "size_md": 14,
    "size_lg": 16,
    "size_xl": 20,
    "size_2xl": 28,
}