# src/gui/design_system/tokens.py
"""
Complete design token system for DesktopAI Premium UI.
All colors, spacing, typography, and effects defined here.
"""

class Tokens:
    """Centralized design tokens - single source of truth."""
    
    # Color Palette - Dark Theme
    DARK = {
        # Backgrounds
        'bg_base': '#0A0A0B',
        'bg_surface': '#13131A',
        'bg_elevated': '#1A1A24',
        'bg_input': '#1E1E28',
        'bg_hover': 'rgba(255,255,255,0.04)',
        'bg_active': 'rgba(139,92,246,0.12)',
        
        # Borders
        'border_subtle': 'rgba(255,255,255,0.08)',
        'border_default': 'rgba(255,255,255,0.12)',
        'border_strong': 'rgba(255,255,255,0.20)',
        
        # Text
        'text_primary': '#E4E4E7',
        'text_secondary': '#A1A1AA',
        'text_muted': '#71717A',
        'text_inverted': '#0A0A0B',
        
        # Accent (Purple)
        'accent': '#8B5CF6',
        'accent_hover': '#7C3AED',
        'accent_active': '#6D28D9',
        'accent_subtle': 'rgba(139,92,246,0.12)',
        'accent_text': '#FFFFFF',
        
        # Semantic
        'success': '#10B981',
        'success_bg': 'rgba(16,185,129,0.12)',
        'warning': '#F59E0B',
        'warning_bg': 'rgba(245,158,11,0.12)',
        'error': '#EF4444',
        'error_bg': 'rgba(239,68,68,0.12)',
        'info': '#3B82F6',
        'info_bg': 'rgba(59,130,246,0.12)',
    }
    
    # Color Palette - Light Theme
    LIGHT = {
        # Backgrounds
        'bg_base': '#FFFFFF',
        'bg_surface': '#F9FAFB',
        'bg_elevated': '#FFFFFF',
        'bg_input': '#F3F4F6',
        'bg_hover': 'rgba(0,0,0,0.04)',
        'bg_active': 'rgba(124,58,237,0.08)',
        
        # Borders
        'border_subtle': 'rgba(0,0,0,0.08)',
        'border_default': 'rgba(0,0,0,0.12)',
        'border_strong': 'rgba(0,0,0,0.20)',
        
        # Text
        'text_primary': '#111827',
        'text_secondary': '#6B7280',
        'text_muted': '#9CA3AF',
        'text_inverted': '#FFFFFF',
        
        # Accent (Purple - darker for light mode)
        'accent': '#7C3AED',
        'accent_hover': '#6D28D9',
        'accent_active': '#5B21B6',
        'accent_subtle': 'rgba(124,58,237,0.08)',
        'accent_text': '#FFFFFF',
        
        # Semantic
        'success': '#059669',
        'success_bg': 'rgba(5,150,105,0.08)',
        'warning': '#D97706',
        'warning_bg': 'rgba(217,119,6,0.08)',
        'error': '#DC2626',
        'error_bg': 'rgba(220,38,38,0.08)',
        'info': '#2563EB',
        'info_bg': 'rgba(37,99,235,0.08)',
    }
    
    # Spacing (8px grid)
    SPACING = {
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '5': '20px',
        '6': '24px',
        '8': '32px',
        '10': '40px',
        '12': '48px',
        '16': '64px',
    }
    
    # Typography
    TYPOGRAPHY = {
        'font_family': "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        'font_mono': "'JetBrains Mono', 'Fira Code', monospace",
        'text_xs': '11px',
        'text_sm': '13px',
        'text_base': '14px',
        'text_md': '15px',
        'text_lg': '16px',
        'text_xl': '18px',
        'text_2xl': '24px',
        'text_3xl': '30px',
        'weight_regular': '400',
        'weight_medium': '500',
        'weight_semibold': '600',
        'weight_bold': '700',
    }
    
    # Border Radius
    RADIUS = {
        'sm': '6px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        'full': '9999px',
    }
    
    # Elevation (Shadows)
    SHADOWS = {
        'xs': '0 1px 2px rgba(0,0,0,0.05)',
        'sm': '0 2px 4px rgba(0,0,0,0.08)',
        'md': '0 4px 8px rgba(0,0,0,0.12)',
        'lg': '0 8px 16px rgba(0,0,0,0.16)',
        'xl': '0 16px 32px rgba(0,0,0,0.20)',
    }
    
    # Animation
    ANIMATION = {
        'duration_fast': '100ms',
        'duration_normal': '200ms',
        'duration_slow': '300ms',
        'easing_out': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'easing_in': 'cubic-bezier(0.7, 0, 0.84, 0)',
        'easing_in_out': 'cubic-bezier(0.65, 0, 0.35, 1)',
    }