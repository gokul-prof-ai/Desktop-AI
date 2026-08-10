from unittest.mock import Mock

import pytest

from services.application_services import ApplicationServices


def test_start_delegates_to_watcher() -> None:
    watcher = Mock()
    watcher.start.return_value = True
    file_service = Mock()

    services = ApplicationServices(
        file_service=file_service,
        watcher_service=watcher,
    )

    assert services.start() is True
    watcher.start.assert_called_once_with()


def test_stop_delegates_to_watcher() -> None:
    watcher = Mock()
    watcher.stop.return_value = True
    file_service = Mock()
    services = ApplicationServices(file_service=file_service, watcher_service=watcher)

    assert services.stop() is True
    watcher.stop.assert_called_once_with()


def test_close_stops_watcher_and_closes_file_service() -> None:
    watcher = Mock()
    file_service = Mock()
    services = ApplicationServices(file_service=file_service, watcher_service=watcher)

    services.close()
    services.close()

    watcher.stop.assert_called_once_with()
    file_service.close.assert_called_once_with()
    assert services.is_closed is True


def test_start_after_close_is_rejected() -> None:
    services = ApplicationServices(file_service=Mock(), watcher_service=Mock())
    services.close()

    with pytest.raises(RuntimeError, match="already been closed"):
        services.start()
