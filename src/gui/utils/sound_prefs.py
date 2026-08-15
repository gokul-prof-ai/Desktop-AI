"""
DesktopAI v2.0 — Sound Preferences Persistence
File: src/gui/utils/sound_prefs.py
Stores sound enabled/volume in config/sound_prefs.json.
"""
from __future__ import annotations

import json
from pathlib import Path

_PATH = Path(__file__).resolve().parents[3] / "config" / "sound_prefs.json"
_DEFAULTS = {"enabled": True, "volume": 50}


def load() -> dict:
    try:
        data = json.loads(_PATH.read_text(encoding="utf-8"))
        return {**_DEFAULTS, **data}
    except Exception:
        return dict(_DEFAULTS)


def save(enabled: bool, volume: int) -> None:
    try:
        _PATH.parent.mkdir(parents=True, exist_ok=True)
        _PATH.write_text(
            json.dumps({"enabled": bool(enabled), "volume": int(volume)}),
            encoding="utf-8",
        )
    except Exception:
        pass


def apply_to(sounds) -> None:
    """Apply persisted prefs to the SOUNDS singleton at startup."""
    if sounds is None:
        return
    prefs = load()
    try:
        sounds.set_enabled(prefs["enabled"])
    except Exception:
        pass
    if hasattr(sounds, "set_volume"):
        try:
            sounds.set_volume(prefs["volume"])
        except Exception:
            pass