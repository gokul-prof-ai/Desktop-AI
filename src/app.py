"""
DesktopAI
Main Entry Point
"""

from datetime import datetime

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

    data_folder = config.PROJECT_ROOT / "data"

    scanner = FileScanner()
    files = scanner.scan(data_folder)

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