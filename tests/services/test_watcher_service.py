"""Tests for the DesktopAI v2 WatcherService facade."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from services.watcher_service import WatcherService


class FakeWatcher:
    """Minimal watcher double used to test service lifecycle behavior."""

    instances: list["FakeWatcher"] = []

    def __init__(self, *, folders=None, on_new_file=None):
        self.folders = folders
        self.on_new_file = on_new_file
        self.start_calls = 0
        self.stop_calls = 0
        self.__class__.instances.append(self)

    def start(self):
        self.start_calls += 1

    def stop(self):
        self.stop_calls += 1


def setup_function() -> None:
    FakeWatcher.instances.clear()


def test_start_is_idempotent() -> None:
    service = WatcherService(
        folders=[Path("C:/Downloads")],
        watcher_factory=FakeWatcher,
    )

    assert service.start() is True
    assert service.start() is False
    assert service.is_running is True
    assert len(FakeWatcher.instances) == 1
    assert FakeWatcher.instances[0].start_calls == 1


def test_stop_is_idempotent() -> None:
    service = WatcherService(watcher_factory=FakeWatcher)

    assert service.stop() is False
    assert service.start() is True
    assert service.stop() is True
    assert service.stop() is False
    assert service.is_running is False
    assert FakeWatcher.instances[0].stop_calls == 1


def test_explicit_folders_are_passed_to_watcher() -> None:
    folders = [Path("C:/Downloads"), Path("C:/Desktop")]
    service = WatcherService(folders=folders, watcher_factory=FakeWatcher)

    service.start()

    assert FakeWatcher.instances[0].folders == folders
    assert service.watched_folders == folders


def test_default_folders_are_delegated_to_underlying_watcher() -> None:
    service = WatcherService(watcher_factory=FakeWatcher)

    service.start()

    assert FakeWatcher.instances[0].folders is None
    assert service.watched_folders is None


def test_new_file_callback_is_converted_to_plain_dict() -> None:
    received: list[dict] = []
    service = WatcherService(
        on_new_file=received.append,
        watcher_factory=FakeWatcher,
    )
    service.start()

    callback = FakeWatcher.instances[0].on_new_file
    callback(Path("C:/Downloads/Invoice.PDF"))

    assert received == [
        {
            "path": "C:/Downloads/Invoice.PDF",
            "filename": "Invoice.PDF",
            "extension": ".pdf",
        }
    ]


def test_callback_failure_does_not_escape_service() -> None:
    callback = MagicMock(side_effect=RuntimeError("consumer failed"))
    service = WatcherService(on_new_file=callback, watcher_factory=FakeWatcher)
    service.start()

    FakeWatcher.instances[0].on_new_file(Path("C:/Downloads/test.txt"))

    callback.assert_called_once()


def test_callback_is_optional() -> None:
    service = WatcherService(watcher_factory=FakeWatcher)
    service.start()

    FakeWatcher.instances[0].on_new_file(Path("C:/Downloads/test.txt"))
