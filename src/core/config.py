"""
DesktopAI
Application Configuration

This is the ONE place where tunable settings live: folder scan
depth, the Ollama model name, timeouts, and so on. Before this
file existed, these values were hardcoded and scattered across
several modules (scanner.py, ollama_client.py, classifier.py...).
That made them hard to find and easy to forget about.

Every setting below has a sensible default, so the app works with
zero configuration. Any setting can be overridden without touching
code, by setting an environment variable named DESKTOPAI_<NAME>.

Example (before running the app):
    Windows (cmd):        set DESKTOPAI_OLLAMA_MODEL=mistral
    Windows (PowerShell):  $env:DESKTOPAI_OLLAMA_MODEL = "mistral"
    macOS / Linux:         export DESKTOPAI_OLLAMA_MODEL=mistral
"""

import os
from pathlib import Path

# The project's root folder — the one containing src/, data/, logs/,
# etc. Every other path in this file is built from this, so paths
# work the same regardless of which folder you run the app from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _get_int(name: str, default: int) -> int:
    """
    Read an integer setting from an environment variable named
    DESKTOPAI_<name>, falling back to `default` if it isn't set or
    isn't a valid whole number.
    """
    raw_value = os.environ.get(f"DESKTOPAI_{name}")

    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError:
        return default


def _get_str(name: str, default: str) -> str:
    """
    Read a string setting from an environment variable named
    DESKTOPAI_<name>, falling back to `default` if it isn't set.
    """
    return os.environ.get(f"DESKTOPAI_{name}", default)


# ---------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------

# How many levels of subfolders the scanner will descend into
# by default. 0 means "top-level folder only".
SCAN_MAX_DEPTH = _get_int("SCAN_MAX_DEPTH", 5)

# How many bytes to read at a time while hashing a file. Reading
# in fixed-size chunks (instead of the whole file at once) keeps
# memory usage constant even for very large files.
HASH_CHUNK_SIZE = _get_int("HASH_CHUNK_SIZE", 8192)


# ---------------------------------------------------------------
# Database
# ---------------------------------------------------------------

# Where the SQLite database file lives. The folder is created
# automatically the first time the app connects to it.
DATABASE_PATH = PROJECT_ROOT / "data" / "desktopai.db"


# ---------------------------------------------------------------
# Logging
# ---------------------------------------------------------------

# Where per-module log files (scanner.log, database.log, etc.) are
# written.
LOGS_DIR = PROJECT_ROOT / "logs"


# ---------------------------------------------------------------
# AI / Ollama
# ---------------------------------------------------------------

# The local Ollama server's generation endpoint.
OLLAMA_URL = _get_str("OLLAMA_URL", "http://localhost:11434/api/generate")

# Which Ollama model to use by default. Must already be pulled
# locally (run: ollama pull <model-name>).
OLLAMA_MODEL = _get_str("OLLAMA_MODEL", "llama3.2")

# How long to wait for Ollama to respond before giving up.
OLLAMA_TIMEOUT_SECONDS = _get_int("OLLAMA_TIMEOUT_SECONDS", 60)

# How much extracted text to send to the AI for each task. Longer
# text gets truncated first, so requests stay fast and reliable.
CLASSIFIER_MAX_TEXT_LENGTH = _get_int("CLASSIFIER_MAX_TEXT_LENGTH", 2000)
SUMMARIZER_MAX_TEXT_LENGTH = _get_int("SUMMARIZER_MAX_TEXT_LENGTH", 4000)
RECOMMENDER_MAX_TEXT_PREVIEW_LENGTH = _get_int(
    "RECOMMENDER_MAX_TEXT_PREVIEW_LENGTH", 500
)