"""
DesktopAI v2.0 — Application-Wide Constants
File: src/core/constants.py

This file contains values that are fixed at build time and never change
at runtime. Things that CAN change at runtime (model name, host URL,
user preferences) live in the Settings service (infrastructure/config/).

Rule: No logic here. No imports. Pure data only.
"""

from __future__ import annotations

from pathlib import Path

# ── Identity ───────────────────────────────────────────────────────────────
APP_NAME: str = "DesktopAI"
APP_VERSION: str = "2.0.0"
APP_VERSION_TUPLE: tuple[int, int, int] = (2, 0, 0)
ORGANIZATION_NAME: str = "DesktopAI"

# ── Paths ──────────────────────────────────────────────────────────────────
# All paths are anchored to the repository root, not the current
# working directory. This means the app works correctly regardless
# of where it is launched from.

# src/core/constants.py → src/ → repo root
_SRC_DIR: Path = Path(__file__).resolve().parent.parent
ROOT_DIR: Path = _SRC_DIR.parent

# Standard project directories
CONFIG_DIR: Path = ROOT_DIR / "config"
LOGS_DIR: Path = ROOT_DIR / "logs"
DATA_DIR: Path = ROOT_DIR / "data"
ASSETS_DIR: Path = ROOT_DIR / "assets"
PLUGINS_DIR: Path = ROOT_DIR / "plugins"

# Default config files (created by Settings service if missing)
DEFAULT_APP_TOML: Path = CONFIG_DIR / "app.toml"
DEFAULT_CATEGORIES_TOML: Path = CONFIG_DIR / "categories.toml"

# ── File Scanner ───────────────────────────────────────────────────────────
SCAN_MAX_DEPTH: int = 10
HASH_CHUNK_SIZE: int = 8192  # bytes — used when computing file MD5

# All file extensions DesktopAI will process.
# Grouped by type for readability.
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
    # Documents
    ".pdf", ".docx", ".doc", ".xlsx", ".xls",
    ".txt", ".md", ".csv", ".json", ".rtf",
    # Code
    ".py", ".js", ".ts", ".html", ".css",
    ".java", ".cpp", ".c", ".rs", ".go",
    # Images
    ".png", ".jpg", ".jpeg", ".tiff",
    ".bmp", ".gif", ".heic", ".webp",
    # Audio / Video
    ".mp3", ".wav", ".mp4", ".mkv", ".avi",
    # Archives
    ".zip", ".rar", ".7z", ".tar", ".gz",
})

# Extensions where we attempt OCR text extraction
OCR_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".heic", ".webp",
})

# Extensions where we attempt PDF text extraction
PDF_EXTENSIONS: frozenset[str] = frozenset({".pdf"})

# ── AI / Ollama defaults ───────────────────────────────────────────────────
# These are FALLBACK defaults only.
# Real values come from config/app.toml via the Settings service.
DEFAULT_OLLAMA_HOST: str = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL: str = "llama3.2"
DEFAULT_OLLAMA_MODEL_FAST: str = "llama3.2:1b"
DEFAULT_OLLAMA_TIMEOUT: int = 60  # seconds

# ── Performance ────────────────────────────────────────────────────────────
DEFAULT_MAX_WORKERS: int = 4
EMBEDDING_BATCH_SIZE: int = 32   # files per embedding batch
MAX_SEARCH_RESULTS: int = 50

# ── Database ───────────────────────────────────────────────────────────────
DB_FILENAME: str = "desktop_ai.db"
DB_SCHEMA_VERSION: int = 2        # increment when migrations are added

# ── Logging ────────────────────────────────────────────────────────────────
LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
LOG_MAX_BYTES: int = 5 * 1024 * 1024   # 5 MB per log file
LOG_BACKUP_COUNT: int = 3               # keep 3 rotated log files

# ── GUI ────────────────────────────────────────────────────────────────────
WINDOW_MIN_WIDTH: int = 1024
WINDOW_MIN_HEIGHT: int = 680
WINDOW_DEFAULT_WIDTH: int = 1280
WINDOW_DEFAULT_HEIGHT: int = 800
SIDEBAR_WIDTH: int = 220