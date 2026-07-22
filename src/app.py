"""
DesktopAI
Main Entry Point
"""

from datetime import datetime
from pathlib import Path

from scanner.scanner import FileScanner


def main():
    print("=" * 50)
    print("🚀 DesktopAI")
    print("=" * 50)
    print(f"Started: {datetime.now()}")
    print("Status: Ready")

    scanner = FileScanner()

    folder = Path("data")

    files = scanner.scan(folder)

    print(f"\nFound {len(files)} file(s):\n")

    for file in files:
        print(f"- {file.name} ({file.size} bytes)")

    print("=" * 50)


if __name__ == "__main__":
    main()