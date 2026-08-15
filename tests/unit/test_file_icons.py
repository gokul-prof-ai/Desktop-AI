"""Tests for the centralized file-type icon mapping."""
from __future__ import annotations

from gui.utils.file_icons import DEFAULT_ICON, icon_for


def test_known_extensions():
    assert icon_for("report.pdf") == "📕"
    assert icon_for("notes.docx") == "📘"
    assert icon_for("budget.xlsx") == "📊"
    assert icon_for("script.py") == "🐍"
    assert icon_for("archive.zip") == "📦"


def test_case_insensitive():
    assert icon_for("PHOTO.JPG") == "🖼️"
    assert icon_for("Song.MP3") == "🎵"


def test_unknown_extension_falls_back():
    assert icon_for("data.xyz") == DEFAULT_ICON
    assert icon_for("noext") == DEFAULT_ICON