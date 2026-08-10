"""
DesktopAI v2.0 — WatcherService
File: src/services/watcher_service.py

Application service that owns the lifecycle of the filesystem watcher.

Responsibilities:
- Start and stop the existing FolderWatcher safely.
- Expose stable, plain-Python event payloads to callers.
- Keep watchdog implementation details out of the GUI.
- Prevent duplicate starts and unsafe repeated stops.

WatcherService does not classify, move, rename, or delete files. It is a
notification/lifecycle service; file processing remains the responsibility
of FileService or another explicit application workflow.
"""
from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Callable, Optional

from core.logger import get_logger
from watcher.watcher import FolderWatcher

logger = get_logger(__name__)

NewFileCallback = Callable[[dict], None]


class WatcherService:
    """Application-level facade for the existing FolderWatcher."""

    def __init__(
        self,
        folders: Optional[list[Path | str]] = None,
        on_new_file: Optional[NewFileCallback] = None,
        watcher_factory: Callable[..., FolderWatcher] = FolderWatcher,
    ) -> None:
        self._folders = [Path(folder) for folder in folders] if folders is not None else None
        self._on_new_file = on_new_file
        self._watcher_factory = watcher_factory
        self._watcher: FolderWatcher | None = None
        self._running = False
        self._lock = Lock()

    @property
    def is_running(self) -> bool:
        """Return whether the watcher is currently running."""
        with self._lock:
            return self._running

    @property
    def watched_folders(self) -> list[Path] | None:
        """Return the explicitly configured folders, if any."""
        return list(self._folders) if self._folders is not None else None

    def start(self) -> bool:
        """Start the watcher once; return True only when a start occurred."""
        with self._lock:
            if self._running:
                return False

            kwargs: dict = {"on_new_file": self._handle_new_file}
            if self._folders is not None:
                kwargs["folders"] = self._folders

            watcher = self._watcher_factory(**kwargs)
            watcher.start()
            self._watcher = watcher
            self._running = True

        logger.info("WatcherService started.")
        return True

    def stop(self) -> bool:
        """Stop the watcher once; return True only when a stop occurred."""
        with self._lock:
            if not self._running or self._watcher is None:
                return False

            watcher = self._watcher
            self._watcher = None
            self._running = False

        try:
            watcher.stop()
        finally:
            logger.info("WatcherService stopped.")
        return True

    def _handle_new_file(self, path: Path) -> None:
        """Convert a watchdog callback into a stable service payload."""
        payload = {
            "path": path.as_posix(),
            "filename": path.name,
            "extension": path.suffix.lower(),
        }

        if self._on_new_file is None:
            return

        try:
            self._on_new_file(payload)
        except Exception as exc:  # noqa: BLE001
            # A consumer callback must never terminate the watcher callback.
            logger.exception("WatcherService callback failed for %s: %s", path, exc)
