"""
DesktopAI
Main Entry Point
"""

import sys
from datetime import datetime
from pathlib import Path

from core import config
from core.logger import get_logger
from database.database import DatabaseManager
from scanner.scanner import FileScanner

logger = get_logger("app")


def main():
    print("=" * 50)
    print("🚀 DesktopAI")
    print("=" * 50)
    print(f"Started: {datetime.now()}")
    print("Status: Ready")

    logger.info("Application started.")

    # Folder to scan: a path passed on the command line wins, then
    # falls back to config.SCAN_FOLDER (which itself defaults to the
    # bundled data/ sample folder, or DESKTOPAI_SCAN_FOLDER if set).
    scan_folder = Path(sys.argv[1]) if len(sys.argv) > 1 else config.SCAN_FOLDER

    if not scan_folder.exists():
        print(f"\nFolder not found: {scan_folder}")
        logger.warning(f"Scan folder does not exist: {scan_folder}")
        return

    print(f"\nScanning: {scan_folder}")

    scanner = FileScanner()
    files = scanner.scan(scan_folder)

    db = DatabaseManager(config.DATABASE_PATH)
    db.connect()
    for file in files:
        db.save_file(file)
    db.close()

    print(f"\nFound {len(files)} file(s):\n")

    for file in files:
        hash_preview = file.file_hash[:12] if file.file_hash else "unreadable"
        print(f"- {file.name} ({file.size} bytes) [{hash_preview}]")

    print(f"\nSaved {len(files)} record(s) to database.")
    print("=" * 50)


if __name__ == "__main__":
    main()