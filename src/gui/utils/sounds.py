"""
DesktopAI v2.0 — Sound Manager (lazy init)
File: src/gui/utils/sounds.py
Generates UI sounds in memory; loads ONLY after QApplication exists.
"""
from __future__ import annotations
import io
import math
import struct
import wave
from PySide6.QtCore import QObject, QUrl
from PySide6.QtWidgets import QApplication

try:
    from PySide6.QtMultimedia import QSoundEffect
except Exception:  # multimedia optional
    QSoundEffect = None


def _write_wav(samples: list[int], sample_rate: int = 44100) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return buf.getvalue()


def _gen_click() -> bytes:
    sr = 44100
    n = int(sr * 0.04)
    return _write_wav([
        int(math.sin(2 * math.pi * 1200 * i / sr) * math.exp(-i / n * 6) * 0.35 * 32767)
        for i in range(n)
    ])


def _gen_hover() -> bytes:
    sr = 44100
    n = int(sr * 0.05)
    return _write_wav([
        int(math.sin(2 * math.pi * (700 + 300 * i / n) * i / sr) * 0.12 * 32767)
        for i in range(n)
    ])


def _gen_success() -> bytes:
    sr = 44100
    n = int(sr * 0.25)
    out = []
    for i in range(n):
        t = i / sr
        f = 523 if i < n // 2 else 784
        env = math.exp(-((i % (n // 2)) / (n // 2)) * 4)
        out.append(int(math.sin(2 * math.pi * f * t) * env * 0.25 * 32767))
    return _write_wav(out)


class _SoundManager(QObject):
    _instance = None

    def __init__(self):
        super().__init__()
        self._effects = {}
        self._enabled = True
        self._temp_dir = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = _SoundManager()
        return cls._instance

    def _ensure_loaded(self):
        if self._effects or QSoundEffect is None:
            return
        if QApplication.instance() is None:
            return  # never touch QtMultimedia before QApplication
        import os
        import tempfile
        self._temp_dir = tempfile.mkdtemp(prefix="dai_sounds_")
        for name, data in (("click", _gen_click()), ("hover", _gen_hover()), ("success", _gen_success())):
            path = os.path.join(self._temp_dir, f"{name}.wav")
            with open(path, "wb") as f:
                f.write(data)
            fx = QSoundEffect(self)
            fx.setSource(QUrl.fromLocalFile(path))
            fx.setVolume(0.5)
            self._effects[name] = fx

    def play(self, name: str):
        if not self._enabled:
            return
        self._ensure_loaded()
        fx = self._effects.get(name)
        if fx is None:
            return
        try:
            fx.stop()
            fx.play()
        except Exception:
            pass

    def play_click(self): self.play("click")
    def play_hover(self): self.play("hover")
    def play_success(self): self.play("success")

    def set_enabled(self, on: bool):
        self._enabled = on

    @property
    def enabled(self) -> bool:
        return self._enabled


SOUNDS = _SoundManager.get()