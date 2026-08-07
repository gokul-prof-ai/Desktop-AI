"""
DesktopAI v2.0 — Centralized Logger
File: src/core/logger.py

Provides one consistent logging setup for the entire application.
Every module must get its logger through get_logger() — never by
calling logging.getLogger() directly.

Key improvements over V1:
- No dependency on config.py (logger can now log config errors)
- Rotating file handler (log files never grow beyond 5 MB)
- Debug mode support (console shows DEBUG when app launched with --debug)
- Structured format with module name for easy filtering
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Import only from constants — never from config or any other module.
# This keeps the logger at the very bottom of the dependency chain.
from core.constants import (
    LOGS_DIR,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT,
)

# ── Module-level state ─────────────────────────────────────────────────────
# Tracks whether the root configuration has been applied.
# This ensures we configure logging exactly once per process.
_is_configured: bool = False
_debug_mode: bool = False


def configure(debug: bool = False) -> None:
    """
    Configure the application-wide logging system.

    Call this ONCE at startup (in main.py) before any other module
    creates a logger. Subsequent calls are safely ignored.

    Args:
        debug: If True, the console handler shows DEBUG-level messages.
               If False (default), console only shows WARNING and above.
               Log FILES always capture everything (DEBUG and above).
    """
    global _is_configured, _debug_mode

    if _is_configured:
        return

    _debug_mode = debug
    _is_configured = True

    # Ensure the logs directory exists.
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Configure the root logger to accept everything.
    # Individual handlers decide what level they actually emit.
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Remove any handlers Python or a library may have already added.
    root.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # ── Main rotating file handler ─────────────────────────────────────
    # Writes all log levels. Rotates at 5 MB. Keeps 3 backups.
    main_log_path = LOGS_DIR / "desktop_ai.log"
    file_handler = RotatingFileHandler(
        filename=main_log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # ── Console handler ────────────────────────────────────────────────
    # Normal mode : WARNING and above (keeps terminal clean)
    # Debug mode  : DEBUG and above (shows everything)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.WARNING)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger for a module.

    Usage (at the top of any module):
        from core.logger import get_logger
        logger = get_logger(__name__)

        logger.debug("Scanning %s", folder_path)
        logger.info("Found %d files", count)
        logger.warning("File skipped: %s", reason)
        logger.error("Operation failed", exc_info=True)

    Args:
        name: Use __name__ so the logger name matches the module path.
              Example: "domain.scanner.scanner"

    Returns:
        A standard Python Logger. All output goes to logs/desktop_ai.log
        and to the console (level depends on debug mode).
    """
    if not _is_configured:
        # Auto-configure with safe defaults if called before configure().
        # This handles loggers created at import time.
        configure(debug=False)

    return logging.getLogger(name)


def set_debug_mode(enabled: bool) -> None:
    """
    Toggle debug mode at runtime.

    Useful for a Settings panel toggle — changes console verbosity
    without restarting the application.

    Args:
        enabled: True to show DEBUG on console, False for WARNING only.
    """
    global _debug_mode
    _debug_mode = enabled

    target_level = logging.DEBUG if enabled else logging.WARNING
    root = logging.getLogger()

    for handler in root.handlers:
        if isinstance(handler, logging.StreamHandler) and \
           not isinstance(handler, RotatingFileHandler):
            handler.setLevel(target_level)