"""
DesktopAI
Tests for the Folder Watcher module.
"""

import time

from watcher.watcher import FolderWatcher, wait_for_stable_file


def test_wait_for_stable_file_returns_false_when_missing(tmp_path):
    """A file that doesn't exist can never be considered stable."""
    missing = tmp_path / "does_not_exist.txt"

    result = wait_for_stable_file(
        missing, stability_seconds=1, poll_interval_seconds=1, timeout_seconds=2
    )

    assert result is False


def test_wait_for_stable_file_returns_true_for_unchanging_file(tmp_path):
    """A file whose size never changes should be reported stable
    quickly, without waiting for the full timeout."""
    stable_file = tmp_path / "already_done.txt"
    stable_file.write_text("hello, this file is not being written to")

    result = wait_for_stable_file(
        stable_file, stability_seconds=1, poll_interval_seconds=1, timeout_seconds=5
    )

    assert result is True


def test_wait_for_stable_file_times_out_for_growing_file(tmp_path):
    """A file that keeps growing should never be reported stable —
    wait_for_stable_file should give up at the timeout instead of
    hanging forever."""
    import threading

    growing_file = tmp_path / "still_downloading.txt"
    growing_file.write_text("a")
    keep_writing = threading.Event()
    keep_writing.set()

    def keep_growing():
        # Writes continuously (faster than the 1-second poll
        # interval below), so every poll sees a different size.
        while keep_writing.is_set():
            with growing_file.open("a") as file:
                file.write("more data")
            time.sleep(0.2)

    grower = threading.Thread(target=keep_growing, daemon=True)
    grower.start()

    try:
        result = wait_for_stable_file(
            growing_file, stability_seconds=2, poll_interval_seconds=1, timeout_seconds=3
        )
    finally:
        keep_writing.clear()
        grower.join()

    assert result is False


def test_folder_watcher_skips_missing_folders_without_raising(tmp_path):
    """start() should skip folders that don't exist rather than
    crashing, since a missing Downloads/Desktop folder shouldn't
    stop the whole app."""
    missing_folder = tmp_path / "does_not_exist"

    watcher = FolderWatcher(folders=[missing_folder])

    watcher.start()  # should not raise
    watcher.stop()


def test_folder_watcher_detects_new_file(tmp_path):
    """Dropping a new, already-complete file into a watched folder
    should trigger the on_new_file callback with its path."""
    detected: list = []

    watcher = FolderWatcher(
        folders=[tmp_path],
        on_new_file=lambda path: detected.append(path),
    )
    watcher.start()

    try:
        new_file = tmp_path / "report.txt"
        new_file.write_text("quarterly numbers")

        # The watcher waits config.WATCH_STABILITY_SECONDS before
        # reporting a file, so give it a little time to notice.
        deadline = time.time() + 10
        while time.time() < deadline and not detected:
            time.sleep(0.5)
    finally:
        watcher.stop()

    assert len(detected) == 1
    assert detected[0].name == "report.txt"