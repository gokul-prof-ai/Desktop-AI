"""
DesktopAI
Tests for the SCAN_FOLDER configuration setting.
"""

import importlib

import core.config as config


def test_scan_folder_defaults_to_data_dir():
    """With no override, SCAN_FOLDER should be PROJECT_ROOT/data."""
    importlib.reload(config)
    assert config.SCAN_FOLDER == config.PROJECT_ROOT / "data"


def test_scan_folder_env_override(monkeypatch, tmp_path):
    """DESKTOPAI_SCAN_FOLDER should override the default."""
    monkeypatch.setenv("DESKTOPAI_SCAN_FOLDER", str(tmp_path))
    importlib.reload(config)
    assert config.SCAN_FOLDER == tmp_path

    # Reload again with the env var cleared so later tests (and other
    # modules that already imported config) aren't left pointed at
    # tmp_path once this test's monkeypatch is undone.
    monkeypatch.delenv("DESKTOPAI_SCAN_FOLDER")
    importlib.reload(config)