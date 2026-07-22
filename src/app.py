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
        print(f"- {file.name} ({file.size} bytes)")

    print("=" * 50)


if __name__ == "__main__":
    main()