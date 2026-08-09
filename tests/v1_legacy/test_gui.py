"""
DesktopAI
Tests for the GUI module.

Since PySide6 requires a display server, these tests mock the
heavyweight components (Ollama, FAISS, database) and focus on
verifying that workers call the right functions and that tabs
can be constructed without crashing.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------
# Worker tests
# ---------------------------------------------------------------


@patch("gui.main_window.DatabaseManager")
@patch("gui.main_window.FileScanner")
def test_scan_worker_calls_scanner_and_saves_to_db(mock_scanner_cls, mock_db_cls):
    """ScanWorker should scan the folder and save each file to the DB."""
    from gui.main_window import ScanWorker

    file_info = MagicMock()
    mock_scanner = MagicMock()
    mock_scanner.scan.return_value = [file_info]
    mock_scanner_cls.return_value = mock_scanner

    mock_db = MagicMock()
    mock_db_cls.return_value = mock_db

    worker = ScanWorker(Path("/some/folder"))
    worker.run()

    mock_scanner.scan.assert_called_once_with(Path("/some/folder"))
    mock_db.save_file.assert_called_once_with(file_info)


@patch("gui.main_window.DatabaseManager")
@patch("gui.main_window.FileScanner")
def test_scan_worker_emits_finished_signal(mock_scanner_cls, mock_db_cls):
    """ScanWorker.finished should emit the list of scanned files."""
    from gui.main_window import ScanWorker

    files = [MagicMock(), MagicMock()]
    mock_scanner = MagicMock()
    mock_scanner.scan.return_value = files
    mock_scanner_cls.return_value = mock_scanner

    worker = ScanWorker(Path("/some/folder"))
    mock_handler = MagicMock()
    worker.finished.connect(mock_handler)
    worker.run()

    mock_handler.assert_called_once_with(files)


@patch("gui.main_window.DatabaseManager")
@patch("gui.main_window.FileScanner")
def test_scan_worker_emits_failed_on_error(mock_scanner_cls, mock_db_cls):
    """ScanWorker.failed should emit the error message on exception."""
    from gui.main_window import ScanWorker

    mock_scanner = MagicMock()
    mock_scanner.scan.side_effect = RuntimeError("disk error")
    mock_scanner_cls.return_value = mock_scanner

    worker = ScanWorker(Path("/some/folder"))
    mock_handler = MagicMock()
    worker.failed.connect(mock_handler)
    worker.run()

    mock_handler.assert_called_once()
    assert "disk error" in mock_handler.call_args[0][0]


@patch("gui.main_window.build_search_index")
def test_build_index_worker_calls_build_search_index(mock_build):
    """BuildIndexWorker should call build_search_index() and emit the count."""
    from gui.main_window import BuildIndexWorker

    mock_build.return_value = 42

    worker = BuildIndexWorker()
    mock_handler = MagicMock()
    worker.finished.connect(mock_handler)
    worker.run()

    mock_build.assert_called_once()
    mock_handler.assert_called_once_with(42)


@patch("gui.main_window.build_search_index")
def test_build_index_worker_emits_failed_on_error(mock_build):
    """BuildIndexWorker.failed should emit on exception."""
    from gui.main_window import BuildIndexWorker

    mock_build.side_effect = RuntimeError("index error")

    worker = BuildIndexWorker()
    mock_handler = MagicMock()
    worker.failed.connect(mock_handler)
    worker.run()

    mock_handler.assert_called_once()
    assert "index error" in mock_handler.call_args[0][0]


@patch("gui.main_window.semantic_search")
def test_search_worker_calls_semantic_search(mock_search):
    """SearchWorker should call semantic_search with the query."""
    from gui.main_window import SearchWorker

    results = [MagicMock()]
    mock_search.return_value = results

    worker = SearchWorker("tax documents")
    mock_handler = MagicMock()
    worker.finished.connect(mock_handler)
    worker.run()

    mock_search.assert_called_once_with("tax documents")
    mock_handler.assert_called_once_with(results)


@patch("gui.main_window.semantic_search")
def test_search_worker_emits_failed_on_error(mock_search):
    """SearchWorker.failed should emit on exception."""
    from gui.main_window import SearchWorker

    mock_search.side_effect = RuntimeError("search error")

    worker = SearchWorker("query")
    mock_handler = MagicMock()
    worker.failed.connect(mock_handler)
    worker.run()

    mock_handler.assert_called_once()
    assert "search error" in mock_handler.call_args[0][0]


@patch("gui.main_window.generate_response")
def test_chat_worker_calls_generate_response(mock_gen):
    """ChatWorker should call generate_response with the prompt."""
    from gui.main_window import ChatWorker

    mock_gen.return_value = "Hello there!"

    worker = ChatWorker("Hi")
    mock_handler = MagicMock()
    worker.finished.connect(mock_handler)
    worker.run()

    mock_gen.assert_called_once_with("Hi")
    mock_handler.assert_called_once_with("Hello there!")


@patch("gui.main_window.generate_response")
def test_chat_worker_emits_empty_string_when_ai_unavailable(mock_gen):
    """ChatWorker should emit '' if the AI returns None."""
    from gui.main_window import ChatWorker

    mock_gen.return_value = None

    worker = ChatWorker("Hi")
    mock_handler = MagicMock()
    worker.finished.connect(mock_handler)
    worker.run()

    mock_handler.assert_called_once_with("")


@patch("gui.main_window.generate_response")
def test_chat_worker_emits_failed_on_error(mock_gen):
    """ChatWorker.failed should emit on exception."""
    from gui.main_window import ChatWorker

    mock_gen.side_effect = RuntimeError("connection refused")

    worker = ChatWorker("Hi")
    mock_handler = MagicMock()
    worker.failed.connect(mock_handler)
    worker.run()

    mock_handler.assert_called_once()
    assert "connection refused" in mock_handler.call_args[0][0]


# ---------------------------------------------------------------
# Chat tab prompt building
# ---------------------------------------------------------------


@pytest.fixture(scope="module")
def qapp_instance():
    """Create a single QApplication for all widget tests."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_chat_tab_build_prompt_includes_recent_history(qapp_instance):
    """_build_prompt should include recent conversation turns."""
    from gui.main_window import ChatTab

    tab = ChatTab()
    tab._history = [
        ("What is Python?", "A programming language."),
        ("What is SQLite?", "A lightweight database."),
    ]

    prompt = tab._build_prompt("Tell me a joke")

    assert "What is Python?" in prompt
    assert "What is SQLite?" in prompt
    assert "Tell me a joke" in prompt
    assert prompt.endswith("Assistant:")


def test_chat_tab_build_prompt_limits_history(qapp_instance):
    """_build_prompt should only include the last MAX_HISTORY_TURNS."""
    from gui.main_window import ChatTab

    tab = ChatTab()
    tab.MAX_HISTORY_TURNS = 2
    tab._history = [
        ("Q1", "A1"),
        ("Q2", "A2"),
        ("Q3", "A3"),
        ("Q4", "A4"),
    ]

    prompt = tab._build_prompt("Q5")

    assert "Q1" not in prompt
    assert "Q2" not in prompt
    assert "Q3" in prompt
    assert "Q4" in prompt
    assert "Q5" in prompt
