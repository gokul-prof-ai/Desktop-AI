"""
DesktopAI v2.0 — Modern Dashboard Theme Tokens
File: src/gui/theme/tokens.py

Modern investment-dashboard inspired aesthetic:
- Dark surfaces with purple/pink gradient accents
- Glassmorphism effects
- Sleek, professional appearance
"""
from __future__ import annotations

# ── Color Palette ──────────────────────────────────────────────────
PALETTE = {
    # Deep backgrounds
    "bg_primary":     "#0D0D0F",      # Main background (near black)
    "bg_secondary":   "#151518",      # Secondary surfaces
    "bg_card":        "#1A1A1E",      # Card backgrounds
    "bg_elevated":    "#1E1E23",      # Elevated elements
    "bg_input":       "#121215",      # Input fields
    
    # Gradient accents (purple → pink)
    "accent_primary":   "#8B5CF6",    # Primary purple
    "accent_secondary": "#D946EF",    # Secondary pink/magenta
    "accent_glow":      "#A78BFA",    # Glow effects
    "accent_soft":      "#C4B5FD",    # Soft accent
    
    # Gradient stops for buttons/cards
    "gradient_start": "#8B5CF6",
    "gradient_mid":   "#A855F7",
    "gradient_end":   "#D946EF",
    
    # Status colors
    "status_success": "#10B981",      # Green
    "status_warning": "#F59E0B",      # Amber
    "status_error":   "#EF4444",      # Red
    "status_info":    "#3B82F6",      # Blue
    
    # Text hierarchy
    "text_primary":   "#FFFFFF",
    "text_secondary": "#A1A1AA",      # Muted gray
    "text_muted":     "#71717A",      # More muted
    "text_on_accent": "#FFFFFF",
    
    # Borders and dividers
    "border_subtle":  "#27272A",
    "border_default": "#3F3F46",
    "border_glow":    "rgba(139, 92, 246, 0.3)",
    
    # Shadows
    "shadow_dark":    "rgba(0, 0, 0, 0.5)",
    "shadow_glow":    "rgba(139, 92, 246, 0.15)",
}

# ── Spacing Scale ──────────────────────────────────────────────────
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
    "2xl": 48,
}

# ── Border Radius ──────────────────────────────────────────────────
RADIUS = {
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 20,
    "full": 9999,
}

# ── Typography ─────────────────────────────────────────────────────
TYPOGRAPHY = {
    "display_family": "'Inter', 'SF Pro Display', sans-serif",
    "body_family":    "'Inter', 'SF Pro Text', sans-serif",
    "mono_family":    "'JetBrains Mono', 'Fira Code', monospace",
    
    "size_xs": 11,
    "size_sm": 13,
    "size_md": 14,
    "size_lg": 16,
    "size_xl": 20,
    "size_2xl": 28,
    "size_3xl": 36,
    
    "weight_light":   300,
    "weight_regular": 400,
    "weight_medium":  500,
    "weight_semibold": 600,
    "weight_bold":    700,
}