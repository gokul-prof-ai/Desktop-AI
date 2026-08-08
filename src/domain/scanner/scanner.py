"""
DesktopAI v2.0 — File Scanner
File: src/domain/scanner/scanner.py

Walks a folder and produces FileInfo objects for every supported file.

Key improvements over V1:
- Emits progress via AppEvents (GUI can show a live progress bar)
- Respects Settings for max_depth, skip_hidden, skip_system, max_workers
- Computes MD5 hash for change detection (dirty file tracking)
- Uses concurrent.futures for parallel scanning on large folders
- Never crashes on a single bad file — logs the error and continues
"""

from __future__ import annotations

import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from core.constants import SUPPORTED_EXTENSIONS
from core.exceptions import PathNotFoundError, PathPermissionError
from core.logger import get_logger
from domain.scanner.file_info import FileInfo
from infrastructure.config.settings import Settings

logger = get_logger(__name__)

# System folders to always skip on Windows
_WINDOWS_SYSTEM_DIRS: frozenset[str] = frozenset({
    "$recycle.bin",
    "system volume information",
    "windows",
    "program files",
    "program files (x86)",
    "programdata",
    "appdata",
})


class FileScanner:
    """
    Scans a folder recursively and returns FileInfo objects.

    Usage:
        scanner = FileScanner()
        files = scanner.scan("/path/to/folder")
        for file_info in files:
            print(file_info)

    The scanner respects Settings:
        - scanner.max_depth    — how deep to recurse
        - scanner.max_workers  — parallel threads for hashing
        - scanner.skip_hidden  — skip dot-folders
        - scanner.skip_system  — skip Windows system folders
    """

    def __init__(self) -> None:
        self._max_depth:    int  = Settings.scanner.max_depth
        self._max_workers:  int  = Settings.scanner.max_workers
        self._skip_hidden:  bool = Settings.scanner.skip_hidden
        self._skip_system:  bool = Settings.scanner.skip_system

    # ── Public API ─────────────────────────────────────────────────────

    def scan(self, folder_path: str | Path) -> list[FileInfo]:
        """
        Scan a folder and return a list of FileInfo objects.

        Emits AppEvents.scan_started, scan_progress, and scan_completed.
        On error per-file, logs and continues — never raises mid-scan.

        Args:
            folder_path: Path to the folder to scan.

        Returns:
            List of FileInfo objects for every supported file found.

        Raises:
            PathNotFoundError:   If the folder does not exist.
            PathPermissionError: If DesktopAI cannot read the folder.
        """
        folder = Path(folder_path).resolve()

        self._validate_folder(folder)

        logger.info("Scan started: %s", folder)

        # Notify the GUI that a scan is starting.
        self._emit_started(str(folder))

        # Step 1: Collect all file paths (fast, single-threaded walk).
        all_paths = self._collect_paths(folder)
        total = len(all_paths)

        logger.info("Found %d files to process", total)

        if total == 0:
            self._emit_completed(0)
            return []

        # Step 2: Build FileInfo objects in parallel (MD5 is the slow part).
        results: list[FileInfo] = []
        completed = 0

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_map = {
                executor.submit(self._build_file_info, p): p
                for p in all_paths
            }

            for future in as_completed(future_map):
                completed += 1
                self._emit_progress(completed, total)

                try:
                    file_info = future.result()
                    if file_info is not None:
                        results.append(file_info)
                except Exception as exc:
                    path = future_map[future]
                    logger.warning("Failed to process %s: %s", path, exc)

        logger.info(
            "Scan complete: %d/%d files processed successfully",
            len(results), total,
        )

        self._emit_completed(len(results))
        return results

    # ── Path collection ────────────────────────────────────────────────

    def _collect_paths(self, root: Path) -> list[Path]:
        """
        Walk the directory tree and collect all supported file paths.

        Respects max_depth, skip_hidden, and skip_system settings.
        This is intentionally single-threaded — os.walk is fast enough
        and parallel directory walking causes more problems than it solves.
        """
        collected: list[Path] = []

        for dirpath, dirnames, filenames in os.walk(root):
            current_depth = len(Path(dirpath).relative_to(root).parts)

            if current_depth >= self._max_depth:
                dirnames.clear()  # Don't recurse further
                continue

            # Filter subdirectories in-place.
            # os.walk respects modifications to dirnames.
            dirnames[:] = [
                d for d in dirnames
                if self._should_visit_dir(Path(dirpath) / d)
            ]

            for filename in filenames:
                file_path = Path(dirpath) / filename
                if self._should_include_file(file_path):
                    collected.append(file_path)

        return collected

    def _should_visit_dir(self, dir_path: Path) -> bool:
        """Return True if this directory should be recursed into."""
        name = dir_path.name

        if self._skip_hidden and name.startswith("."):
            return False

        if self._skip_system and name.lower() in _WINDOWS_SYSTEM_DIRS:
            return False

        return True

    def _should_include_file(self, file_path: Path) -> bool:
        """Return True if this file should be included in scan results."""
        if self._skip_hidden and file_path.name.startswith("."):
            return False

        ext = file_path.suffix.lower()
        return ext in SUPPORTED_EXTENSIONS

    # ── FileInfo construction ──────────────────────────────────────────

    def _build_file_info(self, path: Path) -> FileInfo | None:
        """
        Build a FileInfo for a single file path.

        Reads file metadata from the filesystem.
        Computes MD5 hash for change detection.
        Returns None if the file cannot be read.
        """
        try:
            stat = path.stat()
        except (OSError, PermissionError) as exc:
            logger.warning("Cannot stat %s: %s", path, exc)
            return None

        try:
            md5 = self._compute_md5(path)
        except Exception as exc:
            logger.debug("Cannot hash %s: %s", path, exc)
            md5 = None

        modified_at: datetime | None = None
        try:
            modified_at = datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            )
        except Exception:
            pass

        return FileInfo(
            path=path,
            filename=path.name,
            extension=path.suffix.lower(),
            size_bytes=stat.st_size,
            modified_at=modified_at,
            md5_hash=md5,
        )

    def _compute_md5(self, path: Path) -> str:
        """
        Compute the MD5 hash of a file's contents.

        Reads in chunks to avoid loading large files into memory.
        Uses HASH_CHUNK_SIZE from constants (default 8192 bytes).
        """
        from core.constants import HASH_CHUNK_SIZE
        h = hashlib.md5()
        with open(path, "rb") as f:
            while chunk := f.read(HASH_CHUNK_SIZE):
                h.update(chunk)
        return h.hexdigest()

    # ── Validation ─────────────────────────────────────────────────────

    def _validate_folder(self, folder: Path) -> None:
        """Raise appropriate errors if the folder cannot be scanned."""
        if not folder.exists():
            raise PathNotFoundError(
                f"Folder does not exist: {folder}"
            )

        if not folder.is_dir():
            raise PathNotFoundError(
                f"Path is not a folder: {folder}"
            )

        if not os.access(folder, os.R_OK):
            raise PathPermissionError(
                f"No read permission for folder: {folder}"
            )

    # ── Event emission ─────────────────────────────────────────────────

    def _emit_started(self, folder_path: str) -> None:
        try:
            from core.events import AppEvents
            AppEvents.scan_started.emit(folder_path)
        except Exception:
            pass  # Events unavailable in headless/test mode

    def _emit_progress(self, done: int, total: int) -> None:
        try:
            from core.events import AppEvents
            AppEvents.scan_progress.emit(done, total)
        except Exception:
            pass

    def _emit_completed(self, total: int) -> None:
        try:
            from core.events import AppEvents
            AppEvents.scan_completed.emit(total)
        except Exception:
            pass