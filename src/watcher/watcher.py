"""
DesktopAI
Folder Watcher

Watches one or more folders (e.g. Downloads, Desktop) for newly
created files and calls a callback once each file has finished
being written to disk (so a half-downloaded file isn't reported
too early).

This module only detects new files — it never classifies,
recommends, moves, or deletes anything itself. That separation
means the watcher can be tested and trusted on its own, regardless
of what a caller decides to do with each new file.
"""

import threading
import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from core import config
from core.logger import get_logger

logger = get_logger("watcher")

# A callback that receives the path of a new, fully-written file.
NewFileCallback = Callable[[Path], None]


def wait_for_stable_file(
    path: Path,
    stability_seconds: int = config.WATCH_STABILITY_SECONDS,
    poll_interval_seconds: int = config.WATCH_POLL_INTERVAL_SECONDS,
    timeout_seconds: int = 300,
) -> bool:
    """
    Poll a file's size until it stays the same for `stability_seconds`,
    so partially-downloaded or partially-copied files aren't reported
    as "new" too early.

    Args:
        path (Path):
            The file to watch.
        stability_seconds (int):
            How long the size must remain unchanged to be
            considered stable. Defaults to config.WATCH_STABILITY_SECONDS.
        poll_interval_seconds (int):
            How often to re-check the file's size. Defaults to
            config.WATCH_POLL_INTERVAL_SECONDS.
        timeout_seconds (int):
            Give up after this many seconds, so a file that never
            finishes (e.g. an interrupted download) doesn't get
            watched forever.

    Returns:
        bool:
            True if the file became stable, False if it disappeared
            or the timeout was reached.
    """
    elapsed_stable = 0
    elapsed_total = 0
    last_size = None

    while elapsed_total < timeout_seconds:
        if not path.exists():
            return False

        try:
            current_size = path.stat().st_size
        except OSError:
            return False

        if current_size == last_size:
            elapsed_stable += poll_interval_seconds
            if elapsed_stable >= stability_seconds:
                return True
        else:
            elapsed_stable = 0
            last_size = current_size

        time.sleep(poll_interval_seconds)
        elapsed_total += poll_interval_seconds

    return False


class _NewFileHandler(FileSystemEventHandler):
    """Watches for file-creation events and waits for each file to
    become stable before reporting it to the caller's callback."""

    def __init__(self, on_new_file: NewFileCallback):
        self._on_new_file = on_new_file

    def on_created(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Wait-for-stability runs on its own thread so it never
        # blocks watchdog from noticing other new files meanwhile.
        thread = threading.Thread(
            target=self._wait_then_notify, args=(path,), daemon=True
        )
        thread.start()

    def _wait_then_notify(self, path: Path) -> None:
        if not wait_for_stable_file(path):
            logger.info("Ignoring %s (removed or never stabilized).", path)
            return

        logger.info("New stable file detected: %s", path)

        try:
            self._on_new_file(path)
        except Exception as error:  # noqa: BLE001
            # A bad callback must never take down the watcher thread.
            logger.warning("Error while handling new file %s: %s", path, error)


class FolderWatcher:
    """Watches a set of folders for new files, using the `watchdog` library."""

    def __init__(
        self,
        folders: list[Path] | None = None,
        on_new_file: NewFileCallback | None = None,
    ):
        """
        Args:
            folders (list[Path] | None):
                Folders to watch. Defaults to config.WATCH_FOLDERS.
            on_new_file (Callable[[Path], None] | None):
                Called with the path of each new, stable file. This
                is a notification only — FolderWatcher never moves,
                classifies, or deletes anything itself. Defaults to
                a no-op if not provided.
        """
        self.folders = folders if folders is not None else config.WATCH_FOLDERS
        self._on_new_file = on_new_file if on_new_file is not None else (lambda path: None)
        self._observer = Observer()
        self._started = False

    def start(self) -> None:
        """
        Start watching all configured folders in the background.
        Folders that don't exist are skipped with a warning, rather
        than raising, so one bad path doesn't stop the others from
        being watched.
        """
        if self._started:
            return

        handler = _NewFileHandler(self._on_new_file)
        scheduled_any = False

        for folder in self.folders:
            if not folder.exists():
                logger.warning("Watch folder does not exist, skipping: %s", folder)
                continue

            self._observer.schedule(handler, str(folder), recursive=False)
            scheduled_any = True
            logger.info("Watching folder: %s", folder)

        if not scheduled_any:
            logger.warning("No valid folders to watch; watcher will run idle.")

        self._observer.start()
        self._started = True

    def stop(self) -> None:
        """Stop watching and release the background thread. Safe to call more than once."""
        if not self._started:
            return

        self._observer.stop()
        self._observer.join()
        self._started = False
        logger.info("Folder watcher stopped.")