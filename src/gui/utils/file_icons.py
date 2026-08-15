"""
DesktopAI v2.0 — Centralized file-type icon mapping.

Single source of truth for extension -> icon. Views must call
icon_for(filename) instead of duplicating their own mappings.
"""
from __future__ import annotations

from pathlib import Path

_ICON_MAP = {
    # Documents
    ".pdf": "📕",
    ".doc": "📘", ".docx": "📘",
    ".txt": "📄", ".md": "📄", ".rtf": "📄",
    # Spreadsheets / data
    ".xls": "📊", ".xlsx": "📊", ".csv": "📊",
    # Presentations
    ".ppt": "📙", ".pptx": "📙",
    # Images
    ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️",
    ".gif": "🖼️", ".bmp": "🖼️", ".heic": "🖼️", ".svg": "🖼️",
    # Video / audio
    ".mp4": "🎬", ".mov": "🎬", ".mkv": "🎬", ".avi": "🎬",
    ".mp3": "🎵", ".wav": "🎵", ".flac": "🎵", ".m4a": "🎵",
    # Archives
    ".zip": "📦", ".rar": "📦", ".7z": "📦", ".tar": "📦", ".gz": "📦",
    # Code
    ".py": "🐍",
    ".js": "💻", ".ts": "💻", ".java": "💻", ".c": "💻", ".cpp": "💻",
    ".html": "💻", ".css": "💻", ".json": "💻",
}

DEFAULT_ICON = "📄"


def icon_for(filename: str | Path) -> str:
    """Return the icon for a filename/path based on its extension."""
    ext = Path(filename).suffix.lower()
    return _ICON_MAP.get(ext, DEFAULT_ICON)