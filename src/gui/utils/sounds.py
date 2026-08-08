"""
DesktopAI v2.0 — Sound Manager
File: src/gui/utils/sounds.py

Generates subtle UI sounds programmatically.
No external files required — sounds are created in memory.
"""
from __future__ import annotations
import struct
import wave
import io
import math
from pathlib import Path
from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QSoundEffect
from core.logger import get_logger

logger = get_logger(__name__)


def _generate_tone(
    frequency: float,
    duration_ms: int,
    volume: float = 0.3,
    waveform: str = "sine",
    fade_out: bool = True,
) -> bytes:
    """Generate a WAV file in memory with the specified tone."""
    sample_rate = 44100
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    
    for i in range(num_samples):
        t = i / sample_rate
        
        # Generate waveform
        if waveform == "sine":
            value = math.sin(2 * math.pi * frequency * t)
        elif waveform == "square":
            value = 1.0 if math.sin(2 * math.pi * frequency * t) > 0 else -1.0
        elif waveform == "triangle":
            value = 2.0 * abs(2 * (t * frequency - math.floor(t * frequency + 0.5))) - 1.0
        else:
            value = math.sin(2 * math.pi * frequency * t)
        
        # Apply envelope
        if fade_out:
            progress = i / num_samples
            if progress > 0.7:
                envelope = 1.0 - ((progress - 0.7) / 0.3)
            else:
                envelope = 1.0
        else:
            envelope = 1.0
        
        samples.append(int(value * volume * envelope * 32767))
    
    # Write to WAV buffer
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))
    
    return buf.getvalue()


def _generate_click() -> bytes:
    """Generate a crisp, subtle click sound."""
    sample_rate = 44100
    duration_ms = 30
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    
    for i in range(num_samples):
        t = i / sample_rate
        # Quick attack, fast decay
        envelope = math.exp(-t * 100)
        value = math.sin(2 * math.pi * 1200 * t) * envelope * 0.4
        samples.append(int(value * 32767))
    
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))
    return buf.getvalue()


def _generate_success() -> bytes:
    """Generate a pleasant success chime (two-tone ascending)."""
    sample_rate = 44100
    duration_ms = 200
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    
    for i in range(num_samples):
        t = i / sample_rate
        progress = i / num_samples
        
        # Two tones: 523 Hz (C5) then 659 Hz (E5)
        if progress < 0.5:
            freq = 523
            local_progress = progress * 2
        else:
            freq = 659
            local_progress = (progress - 0.5) * 2
        
        envelope = math.exp(-local_progress * 3) * 0.3
        value = math.sin(2 * math.pi * freq * t) * envelope
        samples.append(int(value * 32767))
    
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))
    return buf.getvalue()


def _generate_boot() -> bytes:
    """Generate a smooth boot-up sound (rising sweep)."""
    sample_rate = 44100
    duration_ms = 800
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    
    for i in range(num_samples):
        t = i / sample_rate
        progress = i / num_samples
        
        # Frequency sweep from 200 Hz to 800 Hz
        freq = 200 + (800 - 200) * progress
        envelope = math.sin(progress * math.pi) * 0.25
        value = math.sin(2 * math.pi * freq * t) * envelope
        samples.append(int(value * 32767))
    
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))
    return buf.getvalue()


class SoundManager(QObject):
    """
    Singleton sound manager for UI feedback.
    All sounds are generated in memory — no external files needed.
    """
    _instance = None
    
    def __init__(self):
        super().__init__()
        self._effects = {}
        self._enabled = True
        self._temp_dir = None
        self._init_sounds()
    
    @classmethod
    def get(cls) -> "SoundManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _init_sounds(self):
        """Generate and load all UI sounds."""
        import tempfile
        import os
        
        self._temp_dir = tempfile.mkdtemp(prefix="desktopai_sounds_")
        
        sounds = {
            "click": _generate_click(),
            "success": _generate_success(),
            "boot": _generate_boot(),
        }
        
        for name, wav_data in sounds.items():
            try:
                path = os.path.join(self._temp_dir, f"{name}.wav")
                with open(path, "wb") as f:
                    f.write(wav_data)
                
                effect = QSoundEffect(self)
                effect.setSource(QUrl.fromLocalFile(path))
                effect.setVolume(0.4)
                self._effects[name] = effect
                
                logger.debug(f"Loaded sound: {name}")
            except Exception as e:
                logger.warning(f"Failed to load sound {name}: {e}")
    
    def play(self, name: str):
        """Play a sound by name."""
        if not self._enabled or name not in self._effects:
            return
        
        effect = self._effects[name]
        try:
            effect.stop()
            effect.play()
        except Exception as e:
            logger.debug(f"Sound play failed: {e}")
    
    def play_click(self):
        self.play("click")
    
    def play_success(self):
        self.play("success")
    
    def play_boot(self):
        self.play("boot")
    
    def toggle(self):
        self._enabled = not self._enabled
    
    @property
    def is_enabled(self) -> bool:
        return self._enabled


# Global singleton
SOUNDS = SoundManager.get()