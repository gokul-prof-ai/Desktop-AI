"""
DesktopAI v2.0 — Asset Setup Script
File: scripts/setup_assets.py

Downloads futuristic fonts and generates Jarvis-style sound effects.
Run ONCE from the repo root:
    python scripts/setup_assets.py
"""
from __future__ import annotations
import math
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "assets" / "fonts"
SOUNDS_DIR = ROOT / "assets" / "sounds"

# ── Font URLs (Google Fonts — free for commercial use) ─────────────
FONTS = {
    "Orbitron-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/orbitron/Orbitron%5Bwght%5D.ttf",
    "Rajdhani-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/rajdhani/Rajdhani%5Bwght%5D.ttf",
    "JetBrainsMono-Regular.ttf": "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Regular.ttf",
}


def setup_fonts() -> None:
    """Download futuristic fonts into assets/fonts/."""
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        import urllib.request
    except ImportError:
        print("  ⚠ urllib not available — skipping font download")
        return
    
    print("\n[1/2] Downloading futuristic fonts...")
    for filename, url in FONTS.items():
        target = FONTS_DIR / filename
        if target.exists() and target.stat().st_size > 1000:
            print(f"  ✓ {filename} (already exists)")
            continue
        
        print(f"  ↓ {filename}...", end=" ", flush=True)
        try:
            urllib.request.urlretrieve(url, target)
            print(f"✓ ({target.stat().st_size // 1024} KB)")
        except Exception as exc:
            print(f"✗ ({exc})")
            # Create placeholder so app doesn't crash
            target.write_bytes(b"")


def _generate_wav(
    filepath: Path,
    duration_ms: int,
    frequencies: list[tuple[float, float, float]],
    volume: float = 0.3,
    sample_rate: int = 44100,
) -> None:
    """
    Generate a WAV file with layered sine waves.
    
    frequencies: list of (start_hz, end_hz, amplitude) tuples
                 for frequency sweeps over the duration.
    """
    n_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    
    for i in range(n_samples):
        t = i / sample_rate
        progress = i / n_samples
        
        # Envelope: attack-decay for natural sound
        if progress < 0.05:
            envelope = progress / 0.05  # Attack
        elif progress > 0.8:
            envelope = (1.0 - progress) / 0.2  # Release
        else:
            envelope = 1.0
        
        # Sum all frequency layers
        value = 0.0
        for start_hz, end_hz, amp in frequencies:
            # Linear frequency sweep
            hz = start_hz + (end_hz - start_hz) * progress
            value += amp * math.sin(2 * math.pi * hz * t)
        
        # Apply envelope and volume
        value = value * envelope * volume
        
        # Clamp to [-1, 1]
        value = max(-1.0, min(1.0, value))
        
        # Convert to 16-bit PCM
        samples.append(int(value * 32767))
    
    # Write WAV file
    with wave.open(str(filepath), "w") as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)
        wav.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def setup_sounds() -> None:
    """Generate Jarvis-style sound effects."""
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n[2/2] Generating Jarvis sound effects...")
    
    sounds = {
        # Boot: rising chord (C-E-G ascending)
        "boot.wav": (800, [
            (261, 523, 0.4),  # C5 → C6
            (329, 659, 0.3),  # E5 → E6
            (392, 784, 0.3),  # G5 → G6
        ], 0.35),
        
        # Click: sharp high-pitched tap
        "click.wav": (80, [
            (1800, 1200, 0.6),
        ], 0.25),
        
        # Hover: soft rising tone
        "hover.wav": (120, [
            (800, 1000, 0.3),
        ], 0.15),
        
        # Success: pleasant ascending chord
        "success.wav": (400, [
            (523, 784, 0.4),   # C → G
            (659, 988, 0.3),   # E → B
            (784, 1175, 0.3),  # G → D
        ], 0.3),
        
        # Error: descending dissonant
        "error.wav": (300, [
            (600, 300, 0.5),
            (450, 225, 0.3),
        ], 0.3),
        
        # Thinking: pulsing mid-tone (repeating feel via frequency modulation)
        "thinking.wav": (600, [
            (440, 440, 0.3),
            (554, 554, 0.2),  # Subtle harmony
        ], 0.2),
        
        # Notification: bright alert
        "notify.wav": (250, [
            (880, 1320, 0.4),
            (1100, 1650, 0.3),
        ], 0.3),
    }
    
    for filename, (duration, freqs, volume) in sounds.items():
        target = SOUNDS_DIR / filename
        if target.exists() and target.stat().st_size > 100:
            print(f"  ✓ {filename} (already exists)")
            continue
        
        print(f"  ♪ {filename}...", end=" ", flush=True)
        try:
            _generate_wav(target, duration, freqs, volume)
            print(f"✓ ({target.stat().st_size // 1024} KB)")
        except Exception as exc:
            print(f"✗ ({exc})")


def main() -> None:
    print("\n" + "=" * 60)
    print("  DesktopAI v2.0 — Asset Setup")
    print("=" * 60)
    
    setup_fonts()
    setup_sounds()
    
    print("\n" + "=" * 60)
    print("  Asset setup complete.")
    print("  Run the app: python src/main.py --mock-ai")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()