"""
DesktopAI
Tests for the centralized Logger module.
"""

from core.logger import get_logger


def test_get_logger_creates_log_file(tmp_path, monkeypatch):
    """Calling get_logger() should create a log file for that module."""
    # Point the logger at a throwaway folder so this test never
    # touches the project's real logs/ directory.
    import core.logger as logger_module

    monkeypatch.setattr(logger_module, "LOGS_DIR", tmp_path)

    logger = logger_module.get_logger("test_module")
    logger.info("hello from test")

    log_file = tmp_path / "test_module.log"
    assert log_file.exists()
    assert "hello from test" in log_file.read_text(encoding="utf-8")


def test_get_logger_does_not_duplicate_handlers(tmp_path, monkeypatch):
    """Calling get_logger() twice with the same name should not
    attach duplicate handlers (which would cause duplicate log lines)."""
    import core.logger as logger_module

    monkeypatch.setattr(logger_module, "LOGS_DIR", tmp_path)

    logger_first = logger_module.get_logger("duplicate_test")
    handler_count_after_first_call = len(logger_first.handlers)

    logger_second = logger_module.get_logger("duplicate_test")
    handler_count_after_second_call = len(logger_second.handlers)

    assert handler_count_after_first_call == handler_count_after_second_call