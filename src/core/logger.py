"""
DesktopAI
Centralized Logger

Provides one consistent logging setup for the whole application,
as defined in docs/logging-strategy.md. Every module should get its
logger through get_logger() instead of configuring logging itself.
"""

import logging
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Anchor logs/ to the project root, regardless of where a script
# is launched from (same reasoning as the app.py path fix).
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger configured to write to logs/<name>.log

    Args:
        name (str):
            Short module name, e.g. "app", "scanner", "database".
            This determines the log file: logs/<name>.log

    Returns:
        logging.Logger:
            A ready-to-use logger. Calling this more than once with
            the same name is safe and will not create duplicate
            log entries.
    """

    logger = logging.getLogger(name)

    # If this logger already has handlers attached, it was already
    # set up earlier in this run — return it as-is to avoid
    # duplicate log lines.
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    LOGS_DIR.mkdir(exist_ok=True)
    log_file = LOGS_DIR / f"{name}.log"

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Every log level goes to this module's own file.
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Only warnings and above surface on the console, so normal
    # operation stays quiet and real problems stand out.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Don't hand messages up to the root logger, or they'd be
    # printed a second time by Python's default configuration.
    logger.propagate = False

    return logger