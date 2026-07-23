"""
DesktopAI
Folder Watcher Demo

A standalone entry point that starts the FolderWatcher and prints
an AI suggestion for each new file dropped into a watched folder
(Downloads/Desktop by default — see config.WATCH_FOLDERS).

Run this, then create or copy a file into one of those folders to
see a live suggestion. Press Ctrl+C to stop.

This never moves or renames any file — it only prints suggestions.
"""

import time
from pathlib import Path

from core import config
from core.logger import get_logger
from watcher.suggestion_engine import build_suggestion
from watcher.watcher import FolderWatcher

logger = get_logger("app")


def handle_new_file(path: Path) -> None:
    """Build and print a suggestion for a newly detected file."""
    suggestion = build_suggestion(path)

    print(f"\n📄 New file: {suggestion.path.name}")
    print(f"   Category:  {suggestion.category or '(unknown)'}")
    print(f"   Suggested: {suggestion.suggested_folder or '(no suggestion)'}")


def main():
    print("=" * 50)
    print("👀 DesktopAI Folder Watcher")
    print("=" * 50)
    print("Watching:")
    for folder in config.WATCH_FOLDERS:
        print(f"  - {folder}")
    print("\nDrop a file into a watched folder to see a suggestion.")
    print("Press Ctrl+C to stop.\n")

    logger.info("Folder watcher demo started.")

    watcher = FolderWatcher(on_new_file=handle_new_file)
    watcher.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        watcher.stop()


if __name__ == "__main__":
    main()