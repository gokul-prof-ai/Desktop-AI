"""
DesktopAI v2.0 — Application Services

Composition root for application-level services. The GUI owns one instance of
this container and therefore one FileService and one WatcherService for the
application lifetime.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from services.file_service import FileService
from services.watcher_service import WatcherService


class ApplicationServices:
    """Own and coordinate application-level services."""

    def __init__(
        self,
        *,
        watch_folders: list[Path | str] | None = None,
        on_new_file: Callable[[dict], None] | None = None,
        file_service: FileService | None = None,
        watcher_service: WatcherService | None = None,
    ) -> None:
        self.file_service = file_service or FileService()
        self.watcher_service = watcher_service or WatcherService(
            folders=watch_folders,
            on_new_file=on_new_file,
        )
        self._closed = False

    @property
    def is_closed(self) -> bool:
        return self._closed

    def start(self) -> bool:
        """Start background application services."""
        if self._closed:
            raise RuntimeError("ApplicationServices has already been closed.")
        return self.watcher_service.start()

    def stop(self) -> bool:
        """Stop background application services."""
        return self.watcher_service.stop()

    def close(self) -> None:
        """Release all application resources. Safe to call repeatedly."""
        if self._closed:
            return

        self.watcher_service.stop()
        self.file_service.close()
        self._closed = True
