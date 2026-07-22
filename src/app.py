"""
DesktopAI
Main Entry Point
"""

from datetime import datetime
from pathlib import Path

from core.logger import get_logger
from scanner.scanner import FileScanner

logger = get_logger("app")


def main():
    print("=" * 50)
    print("🚀 DesktopAI")
    print("=" * 50)
    print(f"Started: {datetime.now()}")
    print("Status: Ready")

    logger.info("Application started.")

    scanner = FileScanner()

    project_root = Path(__file__).resolve().parent.parent
    folder = project_root / "data"

    files = scanner.scan(folder)

    print(f"\nFound {len(files)} file(s):\n")

    for file in files:
        # Show a shortened version of the hash (first 12 characters)
        # since the full 64-character SHA-256 hash is hard to read
        # at a glance in a console listing.
        hash_preview = file.file_hash[:12] if file.file_hash else "unreadable"
        print(f"- {file.name} ({file.size} bytes) [{hash_preview}]")

    print("=" * 50)


if __name__ == "__main__":
    main()