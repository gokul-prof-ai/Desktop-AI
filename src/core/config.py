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


def _get_path(name: str, default: Path) -> Path:
    """
    Read a single folder path from an environment variable named
    DESKTOPAI_<name>, falling back to `default` if it isn't set.
    """
    raw_value = os.environ.get(f"DESKTOPAI_{name}")

    if raw_value is None:
        return default

    return Path(raw_value)


def _get_path_list(name: str, default: list[Path]) -> list[Path]:
    """
    Read a comma-separated list of folder paths from an environment
    variable named DESKTOPAI_<name>, falling back to `default` if
    it isn't set.

    Example: DESKTOPAI_WATCH_FOLDERS=C:\\Users\\me\\Downloads,C:\\Users\\me\\Desktop
    """
    raw_value = os.environ.get(f"DESKTOPAI_{name}")

    if raw_value is None:
        return default

    return [Path(piece.strip()) for piece in raw_value.split(",") if piece.strip()]


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

# The folder src/app.py scans by default. Defaults to the bundled
# data/ sample folder (handy for a quick smoke test), but should be
# pointed at a real folder (e.g. your Downloads or Documents) to do
# anything useful. Override with an environment variable, or pass a
# folder path directly on the command line: `python src/app.py <folder>`.
SCAN_FOLDER = _get_path("SCAN_FOLDER", PROJECT_ROOT / "data")


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


# ---------------------------------------------------------------
# Watcher
# ---------------------------------------------------------------

# Folders watched for newly created files. Defaults to the current
# user's Downloads and Desktop folders.
WATCH_FOLDERS = _get_path_list(
    "WATCH_FOLDERS",
    [Path.home() / "Downloads", Path.home() / "Desktop"],
)

# How long (in seconds) a file's size must stay unchanged before
# it's treated as "done" being written or downloaded. Prevents
# generating a suggestion for a half-downloaded file.
WATCH_STABILITY_SECONDS = _get_int("WATCH_STABILITY_SECONDS", 2)

# How often (in seconds) the watcher re-checks a pending file's
# size while waiting for it to stabilize.
WATCH_POLL_INTERVAL_SECONDS = _get_int("WATCH_POLL_INTERVAL_SECONDS", 1)
# ---------------------------------------------------------------
# Search (Semantic)
# ---------------------------------------------------------------

# The local Ollama server's embeddings endpoint.
OLLAMA_EMBEDDINGS_URL = _get_str(
    "OLLAMA_EMBEDDINGS_URL", "http://localhost:11434/api/embeddings"
)

# Which Ollama model generates embeddings. This is a separate,
# much smaller/faster model than OLLAMA_MODEL (which handles
# chat-style tasks like classification/summarization) — good for
# low-end machines. Must already be pulled locally
# (run: ollama pull all-minilm).
EMBEDDING_MODEL = _get_str("EMBEDDING_MODEL", "all-minilm")

# How much extracted text to send to the embedding model per file.
# Longer text is truncated first, so embedding stays fast even on
# low-end hardware.
EMBEDDING_MAX_TEXT_LENGTH = _get_int("EMBEDDING_MAX_TEXT_LENGTH", 2000)

# Where the semantic search index is saved on disk. Two files are
# written next to this path: "<name>.faiss" (the vectors) and
# "<name>.json" (which file path each vector belongs to).
SEARCH_INDEX_PATH = PROJECT_ROOT / "data" / "search_index"

# How many results semantic_search() returns by default.
SEARCH_TOP_K = _get_int("SEARCH_TOP_K", 5)