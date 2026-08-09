"""
DesktopAI v2.0 — Unit tests for the Settings service
File: tests/unit/test_settings_service.py
"""
from __future__ import annotations

from infrastructure.config.settings import Settings


def test_settings_load():
    Settings.load()
    assert Settings.is_loaded()
    assert Settings.ai.model
    assert Settings.ai.host.startswith("http")


def test_category_rules_loaded():
    Settings.load()
    assert len(Settings.categories) >= 5


def test_find_category_for_extension():
    Settings.load()
    assert Settings.find_category_for_extension(".pdf") == "PDFs"
    assert Settings.find_category_for_extension(".nope-nothing") is None