"""
DesktopAI
Phase 14 Packaging & Distribution Build Script

Bundles DesktopAI into a standalone Windows executable using PyInstaller.
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def build():
    print("=" * 60)
    print("[BUILD] Building DesktopAI Windows Standalone Release Package")
    print("=" * 60)

    entry_point = PROJECT_ROOT / "src" / "gui_app.py"
    output_dir = PROJECT_ROOT / "dist"
    build_dir = PROJECT_ROOT / "build"

    if not entry_point.exists():
        print(f"Error: Entry point {entry_point} not found!")
        sys.exit(1)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=DesktopAI",
        f"--distpath={output_dir}",
        f"--workpath={build_dir}",
        f"--add-data={PROJECT_ROOT / 'config'};config",
        f"--add-data={PROJECT_ROOT / 'data'};data",
        f"--add-data={PROJECT_ROOT / 'docs'};docs",
        f"--paths={PROJECT_ROOT / 'src'}",
        str(entry_point),
    ]

    print("Running command:")
    print(" ".join(cmd))
    print("-" * 60)

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode == 0:
        print("\n[SUCCESS] Build successful! Distribution created at:")
        print(output_dir / "DesktopAI")
    else:
        print(f"\n[FAILED] Build failed with exit code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
