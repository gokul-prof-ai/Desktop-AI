"""
DesktopAI
Scanner Module

This module scans a folder — and its subfolders, up to a depth
limit — and collects basic metadata about each file without
modifying anything.
"""

import hashlib
from datetime import datetime
from pathlib import Path

from core.logger import get_logger
from .file_info import FileInfo

logger = get_logger("scanner")

# Read files in fixed-size chunks when hashing, so memory usage
# stays constant even for very large files.
HASH_CHUNK_SIZE = 8192


class FileScanner:
    """Scans folders (recursively, up to a depth limit) and returns file metadata."""

    def scan(self, folder: Path, max_depth: int = 5) -> list[FileInfo]:
        """
        Recursively scan a folder and its subfolders.

        Args:
            folder (Path):
                The top-level folder to scan.
            max_depth (int):
                How many levels of subfolders to descend into.
                0 means only scan the top-level folder itself
                (the old non-recursive behavior). Defaults to 5
                so an unexpectedly deep folder tree can't make
                the scan run forever.

        Returns:
            list[FileInfo]:
                A list containing metadata for each discovered file,
                across the top-level folder and its subfolders.
        """

        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder}")

        if not folder.is_dir():
            raise NotADirectoryError(f"{folder} is not a directory.")

        logger.info("Scanning folder: %s (max_depth=%d)", folder, max_depth)

        files: list[FileInfo] = []

        # Explicit stack of (folder_to_scan, current_depth) pairs,
        # instead of a recursive function call. This avoids ever
        # hitting Python's recursion limit on a deep folder tree.
        folders_to_visit: list[tuple[Path, int]] = [(folder, 0)]

        while folders_to_visit:
            current_folder, depth = folders_to_visit.pop()

            try:
                entries = list(current_folder.iterdir())
            except OSError as error:
                logger.warning(
                    "Skipping unreadable folder %s: %s", current_folder, error
                )
                continue

            for item in entries:

                # Ignore hidden/system files and folders like .gitkeep, .git
                if item.name.startswith("."):
                    continue

                if item.is_dir():
                    # Never follow symlinked folders — a symlink could
                    # point back to an ancestor folder and cause an
                    # infinite loop.
                    if item.is_symlink():
                        logger.warning(
                            "Skipping symlinked folder to avoid loops: %s", item
                        )
                        continue

                    # Only queue this subfolder if we haven't hit the
                    # depth limit yet.
                    if depth < max_depth:
                        folders_to_visit.append((item, depth + 1))
                    continue

                if not item.is_file():
                    continue

                # Read file metadata, but don't let one bad file
                # (locked, permission-denied, etc.) kill the whole scan
                try:
                    stat = item.stat()
                except OSError as error:
                    logger.warning("Skipping unreadable file %s: %s", item, error)
                    continue

                file_hash = self._hash_file(item)

                file_info = FileInfo(
                    name=item.name,
                    path=item,
                    extension=item.suffix,
                    size=stat.st_size,
                    created=datetime.fromtimestamp(stat.st_ctime),
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    file_hash=file_hash,
                )

                files.append(file_info)

        logger.info(
            "Scan complete: %d file(s) found in %s (max_depth=%d)",
            len(files),
            folder,
            max_depth,
        )

        return files

    def _hash_file(self, path: Path) -> str | None:
        """
        Compute the SHA-256 hash of a file's contents.

        Reads the file in fixed-size chunks rather than all at once,
        so memory usage stays constant regardless of file size.

        Args:
            path (Path):
                The file to hash.

        Returns:
            str | None:
                The hash as a hex string, or None if the file
                could not be read (e.g. locked or permission denied).
        """

        sha256 = hashlib.sha256()

        try:
            with path.open("rb") as file:
                for chunk in iter(lambda: file.read(HASH_CHUNK_SIZE), b""):
                    sha256.update(chunk)
        except OSError as error:
            logger.warning("Could not hash file %s: %s", path, error)
            return None

        return sha256.hexdigest()