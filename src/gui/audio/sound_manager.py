"""
DesktopAI v2.0 — Jarvis Sound Manager
File: src/gui/audio/sound_manager.py

Centralized audio system for UI feedback sounds.
Uses QtMultimedia for cross-platform playback.
"""
from __future__ import annotations
from pathlib import Path
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl, QObject
from core.logger import get_logger

logger = get_logger(__name__)

# Path to sound assets
_SOUNDS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "sounds"


class _SoundManager(QObject):
    """
    Singleton sound manager for the application.
    
    Usage:
        from gui.audio.sound_manager import Sounds
        Sounds.play("click")
        Sounds.play("success")
        Sounds.set_volume(0.5)  # 0.0 to 1.0
        Sounds.mute()
    """
    
    def __init__(self) -> None:
        super().__init__()
        self._effects: dict[str, QSoundEffect] = {}
        self._volume = 0.4
        self._muted = False
        self._enabled = True
        
        self._load_sounds()
    
    def _load_sounds(self) -> None:
        """Load all sound effects from assets/sounds/."""
        if not _SOUNDS_DIR.exists():
            logger.warning("Sounds directory not found: %s", _SOUNDS_DIR)
            return
        
        sound_files = {
            "boot":      "boot.wav",
            "click":     "click.wav",
            "hover":     "hover.wav",
            "success":   "success.wav",
            "error":     "error.wav",
            "thinking":  "thinking.wav",
            "notify":    "notify.wav",
        }
        
        for name, filename in sound_files.items():
            path = _SOUNDS_DIR / filename
            if not path.exists():
                logger.debug("Sound file missing: %s", path)
                continue
            
            effect = QSoundEffect(self)
            effect.setSource(QUrl.fromLocalFile(str(path)))
            effect.setVolume(self._volume)
            effect.setLoopCount(1)
            self._effects[name] = effect
        
        logger.info("Loaded %d sound effects", len(self._effects))
    
    def play(self, name: str) -> None:
        """Play a sound by name."""
        if self._muted or not self._enabled:
            return
        
        effect = self._effects.get(name)
        if effect is None:
            logger.debug("Sound not found: %s", name)
            return
        
        if effect.isPlaying():
            effect.stop()
        effect.play()
    
    def set_volume(self, volume: float) -> None:
        """Set master volume (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, volume))
        for effect in self._effects.values():
            effect.setVolume(self._volume)
    
    def mute(self) -> None:
        """Mute all sounds."""
        self._muted = True
    
    def unmute(self) -> None:
        """Unmute all sounds."""
        self._muted = False
    
    def toggle_mute(self) -> None:
        """Toggle mute state."""
        self._muted = not self._muted
    
    def enable(self, enabled: bool) -> None:
        """Enable or disable the sound system entirely."""
        self._enabled = enabled
    
    @property
    def is_muted(self) -> bool:
        return self._muted
    
    @property
    def available_sounds(self) -> list[str]:
        return list(self._effects.keys())


# Singleton instance
Sounds = _SoundManager()