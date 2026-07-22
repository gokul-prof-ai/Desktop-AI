"""
DesktopAI
Scanner Module

This module scans a folder and collects basic metadata
about each file without modifying anything.
"""

from datetime import datetime
from pathlib import Path

from core.logger import get_logger
from .file_info import FileInfo

logger = get_logger("scanner")


class FileScanner:
    """Scans folders and returns file metadata."""

    def scan(self, folder: Path) -> list[FileInfo]:
        """
        Scan a single folder (non-recursive).

        Args:
            folder (Path):
                The folder to scan.

        Returns:
            list[FileInfo]:
                A list containing metadata for each discovered file.
        """

        files: list[FileInfo] = []

        # Check whether the folder exists
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder}")

        # Check whether the path is actually a directory
        if not folder.is_dir():
            raise NotADirectoryError(f"{folder} is not a directory.")

        logger.info("Scanning folder: %s", folder)

        # Loop through every item inside the folder
        for item in folder.iterdir():

            # Ignore subfolders for now
            if not item.is_file():
                continue

            # Ignore hidden/system files like .gitkeep, .DS_Store
            if item.name.startswith("."):
                continue

            # Read file metadata, but don't let one bad file
            # (locked, permission-denied, etc.) kill the whole scan
            try:
                stat = item.stat()
            except OSError as error:
                logger.warning("Skipping unreadable file %s: %s", item, error)
                continue

            # Create a FileInfo object
            file_info = FileInfo(
                name=item.name,
                path=item,
                extension=item.suffix,
                size=stat.st_size,
                created=datetime.fromtimestamp(stat.st_ctime),
                modified=datetime.fromtimestamp(stat.st_mtime),
            )

            # Add it to the list
            files.append(file_info)

        logger.info("Scan complete: %d file(s) found in %s", len(files), folder)

        return files