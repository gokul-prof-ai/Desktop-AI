"""
DesktopAI v2.0 — Configuration Layer (Legacy Compatibility + V2 Extensions)
File: src/core/config.py

────────────────────────────────────────────────────────────────────────────
PURPOSE
────────────────────────────────────────────────────────────────────────────
Flat, environment-variable-backed configuration layer.

Two roles:
  1. BACKWARD COMPATIBILITY — V1 modules doing `from core import config`
     keep working. Every constant they reference is defined here.
  2. V2 EXTENSIONS — Embeddings, search, chat, memory, history, export,
     plugins, updater, and mock-AI mode live here too.

CRASH-PROOFING (NEW)
  A module-level __getattr__ (PEP 562) at the bottom of this file catches
  ANY attribute a legacy module requests that is not explicitly defined.
  Instead of raising AttributeError at import time, it returns a sensible
  default derived from the name and logs a warning. This means unknown
  config references can never crash app startup again — you will see a
  "[config] fallback" warning instead, telling you exactly what to add.

OVERRIDE PATTERN
  Every value can be overridden via environment variable, e.g.:
      $env:OLLAMA_MODEL="llama3.2:1b"     (PowerShell)
      set OLLAMA_MODEL=llama3.2:1b        (CMD)

Run `python src/main.py --mock-ai` to force MOCK_AI on without Ollama.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import os
from pathlib import Path

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _get_env(name: str, default: str) -> str:
    """Get a string environment variable with a fallback."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _get_int(name: str, default: int) -> int:
    """Get a positive integer environment variable safely."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        parsed = int(value)
        if parsed <= 0:
            return default
        return parsed
    except (TypeError, ValueError):
        return default


def _get_float(name: str, default: float) -> float:
    """Get a positive float environment variable safely."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        parsed = float(value)
        if parsed <= 0:
            return default
        return parsed
    except (TypeError, ValueError):
        return default


def _get_bool(name: str, default: bool) -> bool:
    """Get a boolean environment variable safely."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


# ============================================================
# MOCK / TEST MODE
# ============================================================
# True when running with --mock-ai or during tests. Domain code and the
# AIGateway should check this flag and skip real Ollama network calls.
MOCK_AI: bool = _get_bool("DESKTOP_AI_MOCK", False)


def enable_mock_mode() -> None:
    """Turn on mock-AI mode at runtime (called by main.py --mock-ai)."""
    global MOCK_AI
    MOCK_AI = True


def disable_mock_mode() -> None:
    """Turn off mock-AI mode at runtime."""
    global MOCK_AI
    MOCK_AI = False


def is_mock_mode() -> bool:
    """Return True if the app is running with mocked AI backends."""
    return MOCK_AI


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR: Path = Path(__file__).resolve().parent
PROJECT_ROOT: Path = BASE_DIR.parent.parent

DATA_DIR: Path = Path(
    _get_env("DESKTOP_AI_DATA_DIR", str(PROJECT_ROOT / "data"))
)

SCAN_FOLDER: Path = Path(
    _get_env("DESKTOPAI_SCAN_FOLDER", str(PROJECT_ROOT / "data"))
)

CACHE_DIR: Path = Path(
    _get_env("DESKTOP_AI_CACHE_DIR", str(DATA_DIR / "cache"))
)

LOG_DIR: Path = Path(
    _get_env("DESKTOP_AI_LOG_DIR", str(DATA_DIR / "logs"))
)

REPORT_DIR: Path = Path(
    _get_env("DESKTOP_AI_REPORT_DIR", str(DATA_DIR / "reports"))
)

EXPORT_DIR: Path = Path(
    _get_env("DESKTOP_AI_EXPORT_DIR", str(DATA_DIR / "exports"))
)


# ============================================================
# STORAGE PATHS
# ============================================================

# SQLite database holding scanned file metadata + history.
DATABASE_PATH: Path = Path(
    _get_env("DESKTOP_AI_DATABASE_PATH", str(DATA_DIR / "desktop_ai.db"))
)

# FAISS semantic search index directory.
SEARCH_INDEX_PATH: Path = Path(
    _get_env("DESKTOP_AI_SEARCH_INDEX_PATH", str(DATA_DIR / "search_index"))
)

# MemoryStore preferences database (learned user preferences).
MEMORY_DB_PATH: Path = Path(
    _get_env("DESKTOP_AI_MEMORY_DB_PATH", str(DATA_DIR / "memory.db"))
)
MEMORY_PATH: Path = MEMORY_DB_PATH

# V1 alias — some legacy modules reference DB_PATH.
DB_PATH: Path = DATABASE_PATH


# ============================================================
# APPLICATION
# ============================================================

APP_NAME: str = _get_env("APP_NAME", "Desktop AI")
APP_VERSION: str = _get_env("APP_VERSION", "2.0.0")
DEBUG: bool = _get_bool("DEBUG", False)


# ============================================================
# AI / OLLAMA CONFIGURATION
# ============================================================

OLLAMA_HOST: str = _get_env("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL: str = _get_env("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_TIMEOUT: float = _get_float("OLLAMA_TIMEOUT", 120.0)
OLLAMA_CONNECT_TIMEOUT: float = _get_float("OLLAMA_CONNECT_TIMEOUT", 10.0)
OLLAMA_TEMPERATURE: float = _get_float("OLLAMA_TEMPERATURE", 0.2)
OLLAMA_MAX_TOKENS: int = _get_int("OLLAMA_MAX_TOKENS", 2048)

# ── V1 aliases (fixes ai/ollama_client.py crash) ────────────
# ollama_client.py reads config.OLLAMA_URL at module import time.
OLLAMA_URL: str = OLLAMA_HOST
OLLAMA_BASE_URL: str = OLLAMA_HOST
OLLAMA_API_URL: str = f"{OLLAMA_HOST}/api"
REQUEST_TIMEOUT: float = OLLAMA_TIMEOUT
MAX_RETRIES: int = _get_int("OLLAMA_MAX_RETRIES", 3)
RETRY_BACKOFF_SECONDS: float = _get_float("OLLAMA_RETRY_BACKOFF", 1.5)

# ── Derived endpoints ────────────────────────────────────────
OLLAMA_GENERATE_URL: str = f"{OLLAMA_HOST}/api/generate"
OLLAMA_CHAT_URL: str = f"{OLLAMA_HOST}/api/chat"
OLLAMA_TAGS_URL: str = f"{OLLAMA_HOST}/api/tags"

# Alias expected by search/embedder.py (seconds).
OLLAMA_TIMEOUT_SECONDS: float = OLLAMA_TIMEOUT


# ============================================================
# AI / OLLAMA EMBEDDING CONFIGURATION
# ============================================================

# Model used for semantic-search embeddings. Pull locally with:
#   ollama pull nomic-embed-text
EMBEDDING_MODEL: str = _get_env("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

# Ollama embeddings endpoint.
OLLAMA_EMBEDDINGS_URL: str = f"{OLLAMA_HOST}/api/embeddings"

# Expected embedding vector dimension (0 = auto-detect).
# nomic-embed-text → 768, all-minilm → 384.
EMBEDDING_DIMENSION: int = _get_int("EMBEDDING_DIMENSION", 768)


# ============================================================
# AI PROCESSING LIMITS
# ============================================================

AI_MAX_TEXT_LENGTH: int = _get_int("AI_MAX_TEXT_LENGTH", 8000)
DOCUMENT_MAX_TEXT_LENGTH: int = _get_int("DOCUMENT_MAX_TEXT_LENGTH", 10000)
CLASSIFIER_MAX_TEXT_LENGTH: int = _get_int("CLASSIFIER_MAX_TEXT_LENGTH", 2000)
SUMMARIZER_MAX_TEXT_LENGTH: int = _get_int("SUMMARIZER_MAX_TEXT_LENGTH", 4000)
RECOMMENDER_MAX_TEXT_PREVIEW_LENGTH: int = _get_int(
    "RECOMMENDER_MAX_TEXT_PREVIEW_LENGTH", 500
)
# Maximum text embedded for semantic search.
EMBEDDING_MAX_TEXT_LENGTH: int = _get_int("EMBEDDING_MAX_TEXT_LENGTH", 8000)


# ============================================================
# SEMANTIC SEARCH CONFIGURATION
# ============================================================

SEARCH_TOP_K: int = _get_int("SEARCH_TOP_K", 10)
SEARCH_MIN_SCORE: float = _get_float("SEARCH_MIN_SCORE", 0.30)
SEARCH_MAX_RESULTS: int = _get_int("SEARCH_MAX_RESULTS", 50)
SEARCH_DEBOUNCE_MS: int = _get_int("SEARCH_DEBOUNCE_MS", 300)
# When True, only changed files are re-embedded (dirty-file tracking).
SEARCH_INCREMENTAL: bool = _get_bool("SEARCH_INCREMENTAL", True)


# ============================================================
# FILE PROCESSING
# ============================================================

MAX_FILE_SIZE_MB: int = _get_int("MAX_FILE_SIZE_MB", 100)
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_FILES_PER_SCAN: int = _get_int("MAX_FILES_PER_SCAN", 10000)
MAX_FOLDER_DEPTH: int = _get_int("MAX_FOLDER_DEPTH", 20)
SCAN_MAX_DEPTH: int = MAX_FOLDER_DEPTH
HASH_CHUNK_SIZE: int = _get_int("HASH_CHUNK_SIZE", 65536)


# ============================================================
# PDF PROCESSING
# ============================================================

PDF_MAX_PAGES: int = _get_int("PDF_MAX_PAGES", 100)
PDF_MAX_TEXT_LENGTH: int = _get_int("PDF_MAX_TEXT_LENGTH", 50000)


# ============================================================
# OCR CONFIGURATION
# ============================================================

OCR_ENABLED: bool = _get_bool("OCR_ENABLED", True)
OCR_MAX_PAGES: int = _get_int("OCR_MAX_PAGES", 20)
OCR_MAX_IMAGE_SIZE_MB: int = _get_int("OCR_MAX_IMAGE_SIZE_MB", 20)
OCR_LANGUAGES: str = _get_env("OCR_LANGUAGES", "eng")


# ============================================================
# EXCEL / CSV PROCESSING
# ============================================================

EXCEL_MAX_ROWS: int = _get_int("EXCEL_MAX_ROWS", 10000)
EXCEL_MAX_COLUMNS: int = _get_int("EXCEL_MAX_COLUMNS", 100)
CSV_MAX_ROWS: int = _get_int("CSV_MAX_ROWS", 10000)


# ============================================================
# TEXT / DOCUMENT PROCESSING
# ============================================================

TEXT_MAX_FILE_SIZE_MB: int = _get_int("TEXT_MAX_FILE_SIZE_MB", 20)
WORD_MAX_TEXT_LENGTH: int = _get_int("WORD_MAX_TEXT_LENGTH", 30000)


# ============================================================
# CLASSIFICATION
# ============================================================

CLASSIFICATION_ENABLED: bool = _get_bool("CLASSIFICATION_ENABLED", True)
CLASSIFICATION_CONFIDENCE_THRESHOLD: float = _get_float(
    "CLASSIFICATION_CONFIDENCE_THRESHOLD", 0.60
)
CLASSIFICATION_BATCH_SIZE: int = _get_int("CLASSIFICATION_BATCH_SIZE", 10)


# ============================================================
# SUMMARIZATION
# ============================================================

SUMMARIZATION_ENABLED: bool = _get_bool("SUMMARIZATION_ENABLED", True)
SUMMARY_MAX_SENTENCES: int = _get_int("SUMMARY_MAX_SENTENCES", 8)


# ============================================================
# RECOMMENDATION ENGINE
# ============================================================

RECOMMENDER_ENABLED: bool = _get_bool("RECOMMENDER_ENABLED", True)
RECOMMENDER_MAX_RESULTS: int = _get_int("RECOMMENDER_MAX_RESULTS", 10)
RECOMMENDER_MIN_CONFIDENCE: float = _get_float("RECOMMENDER_MIN_CONFIDENCE", 0.50)


# ============================================================
# CHAT CONFIGURATION (V2 ChatView)
# ============================================================

CHAT_MAX_HISTORY_MESSAGES: int = _get_int("CHAT_MAX_HISTORY_MESSAGES", 20)
CHAT_MAX_CONTEXT_FILES: int = _get_int("CHAT_MAX_CONTEXT_FILES", 8)
CHAT_SYSTEM_PROMPT: str = _get_env(
    "CHAT_SYSTEM_PROMPT",
    "You are DesktopAI, a local file-organization assistant. "
    "Answer using only the provided file context. Be concise.",
)
CHAT_TEMPERATURE: float = _get_float("CHAT_TEMPERATURE", 0.3)


# ============================================================
# MEMORY CONFIGURATION (V2 MemoryStore)
# ============================================================

MEMORY_ENABLED: bool = _get_bool("MEMORY_ENABLED", True)
MEMORY_MIN_CONFIDENCE: float = _get_float("MEMORY_MIN_CONFIDENCE", 0.50)
MEMORY_MAX_AGE_DAYS: int = _get_int("MEMORY_MAX_AGE_DAYS", 180)


# ============================================================
# HISTORY / AUDIT TRAIL (V2 History view)
# ============================================================

HISTORY_ENABLED: bool = _get_bool("HISTORY_ENABLED", True)
HISTORY_PAGE_SIZE: int = _get_int("HISTORY_PAGE_SIZE", 50)
HISTORY_RETENTION_DAYS: int = _get_int("HISTORY_RETENTION_DAYS", 0)  # 0 = forever


# ============================================================
# EXPORT CONFIGURATION (V2 ExportManager)
# ============================================================

EXPORT_DEFAULT_FORMAT: str = _get_env("EXPORT_DEFAULT_FORMAT", "csv")
EXPORT_INCLUDE_METADATA: bool = _get_bool("EXPORT_INCLUDE_METADATA", True)


# ============================================================
# FILE ORGANIZATION
# ============================================================

ORGANIZATION_ENABLED: bool = _get_bool("ORGANIZATION_ENABLED", True)
AUTO_MOVE_FILES: bool = _get_bool("AUTO_MOVE_FILES", False)
CREATE_MISSING_FOLDERS: bool = _get_bool("CREATE_MISSING_FOLDERS", True)
PRESERVE_FILE_NAMES: bool = _get_bool("PRESERVE_FILE_NAMES", True)
# Collisions append " (1)", " (2)", ... instead of skipping/overwriting.
HANDLE_NAME_COLLISIONS: bool = _get_bool("HANDLE_NAME_COLLISIONS", True)


# ============================================================
# FOLDER WATCHER
# ============================================================

_watch_folders_env: str = os.getenv("DESKTOP_AI_WATCH_FOLDERS", "")
WATCH_FOLDERS: list[Path] = (
    [Path(p) for p in _watch_folders_env.split(":") if p.strip()]
    if _watch_folders_env
    else [Path.home() / "Downloads", Path.home() / "Desktop"]
)

WATCH_STABILITY_SECONDS: int = _get_int("WATCH_STABILITY_SECONDS", 2)
WATCH_POLL_INTERVAL_SECONDS: int = _get_int("WATCH_POLL_INTERVAL_SECONDS", 1)
# Watcher events trigger incremental search-index updates.
WATCH_AUTO_INDEX: bool = _get_bool("WATCH_AUTO_INDEX", True)


# ============================================================
# PLUGIN CONFIGURATION (V2 PluginHost)
# ============================================================

PLUGINS_ENABLED: bool = _get_bool("PLUGINS_ENABLED", True)
PLUGINS_DIR: Path = Path(
    _get_env("DESKTOP_AI_PLUGINS_DIR", str(BASE_DIR.parent / "plugins"))
)


# ============================================================
# UPDATE CHECKER (V2)
# ============================================================

UPDATER_ENABLED: bool = _get_bool("UPDATER_ENABLED", False)
UPDATER_RELEASES_URL: str = _get_env(
    "UPDATER_RELEASES_URL",
    "https://api.github.com/repos/gokul-prof-ai/Desktop-AI/releases/latest",
)
UPDATER_CHECK_INTERVAL_HOURS: int = _get_int("UPDATER_CHECK_INTERVAL_HOURS", 24)


# ============================================================
# PERFORMANCE
# ============================================================

MAX_WORKERS: int = _get_int("MAX_WORKERS", max(2, (os.cpu_count() or 4) // 2))
SCAN_BATCH_SIZE: int = _get_int("SCAN_BATCH_SIZE", 100)
PROCESS_BATCH_SIZE: int = _get_int("PROCESS_BATCH_SIZE", 20)
CACHE_ENABLED: bool = _get_bool("CACHE_ENABLED", True)


# ============================================================
# LOGGING
# ============================================================

LOG_LEVEL: str = _get_env("LOG_LEVEL", "INFO")
LOG_FILE_NAME: str = _get_env("LOG_FILE_NAME", "desktop_ai.log")
LOG_MAX_SIZE_MB: int = _get_int("LOG_MAX_SIZE_MB", 10)
LOG_BACKUP_COUNT: int = _get_int("LOG_BACKUP_COUNT", 5)


# ============================================================
# SUPPORTED FILE EXTENSIONS
# ============================================================

TEXT_EXTENSIONS: set[str] = {".txt", ".md", ".log", ".csv"}
DOCUMENT_EXTENSIONS: set[str] = {".doc", ".docx", ".odt", ".rtf"}
PDF_EXTENSIONS: set[str] = {".pdf"}
SPREADSHEET_EXTENSIONS: set[str] = {".xls", ".xlsx", ".xlsm", ".ods"}
PRESENTATION_EXTENSIONS: set[str] = {".ppt", ".pptx", ".odp"}
IMAGE_EXTENSIONS: set[str] = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp",
}
ARCHIVE_EXTENSIONS: set[str] = {".zip", ".rar", ".7z", ".tar", ".gz"}

# Everything we know how to extract text from.
ALL_SUPPORTED_EXTENSIONS: set[str] = (
    TEXT_EXTENSIONS
    | DOCUMENT_EXTENSIONS
    | PDF_EXTENSIONS
    | SPREADSHEET_EXTENSIONS
    | PRESENTATION_EXTENSIONS
    | IMAGE_EXTENSIONS
)


# ============================================================
# FAST PATH RULES
# ============================================================

FAST_PATH_RULES: dict[str, str] = {
    # Documents
    ".pdf": "Documents",
    ".doc": "Documents",
    ".docx": "Documents",
    ".odt": "Documents",
    ".rtf": "Documents",
    # Spreadsheets
    ".xls": "Spreadsheets",
    ".xlsx": "Spreadsheets",
    ".xlsm": "Spreadsheets",
    ".ods": "Spreadsheets",
    # Presentations
    ".ppt": "Presentations",
    ".pptx": "Presentations",
    ".odp": "Presentations",
    # Text
    ".txt": "Text",
    ".md": "Text",
    ".log": "Text",
    ".csv": "Data",
    # Images
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".bmp": "Images",
    ".tiff": "Images",
    ".tif": "Images",
    ".webp": "Images",
    # Archives
    ".zip": "Archives",
    ".rar": "Archives",
    ".7z": "Archives",
    ".tar": "Archives",
    ".gz": "Archives",
}


# ============================================================
# DIRECTORY INITIALIZATION
# ============================================================

def ensure_directories() -> None:
    """Create application directories if they do not already exist."""
    directories = (
        DATA_DIR,
        CACHE_DIR,
        LOG_DIR,
        REPORT_DIR,
        EXPORT_DIR,
        PLUGINS_DIR,
        SEARCH_INDEX_PATH.parent,
        DATABASE_PATH.parent,
    )
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError:
            # An un-creatable path should not hard-crash startup;
            # the owning subsystem raises a clearer error on use.
            pass


# ============================================================
# CONFIGURATION VALIDATION
# ============================================================

def validate_config() -> None:
    """
    Validate important configuration values.

    Raises:
        ValueError: If a configuration value is invalid.
    """
    if not OLLAMA_HOST:
        raise ValueError("OLLAMA_HOST cannot be empty.")
    if not OLLAMA_MODEL:
        raise ValueError("OLLAMA_MODEL cannot be empty.")
    if not 0 <= OLLAMA_TEMPERATURE <= 2:
        raise ValueError("OLLAMA_TEMPERATURE must be between 0 and 2.")
    if not 0 < CLASSIFICATION_CONFIDENCE_THRESHOLD <= 1:
        raise ValueError(
            "CLASSIFICATION_CONFIDENCE_THRESHOLD must be between 0 and 1."
        )
    if not 0 < RECOMMENDER_MIN_CONFIDENCE <= 1:
        raise ValueError("RECOMMENDER_MIN_CONFIDENCE must be between 0 and 1.")
    if not 0 <= SEARCH_MIN_SCORE <= 1:
        raise ValueError("SEARCH_MIN_SCORE must be between 0 and 1.")
    if MAX_FILE_SIZE_MB <= 0:
        raise ValueError("MAX_FILE_SIZE_MB must be greater than 0.")
    if MAX_FILES_PER_SCAN <= 0:
        raise ValueError("MAX_FILES_PER_SCAN must be greater than 0.")
    if MAX_WORKERS <= 0:
        raise ValueError("MAX_WORKERS must be greater than 0.")
    if SEARCH_TOP_K <= 0:
        raise ValueError("SEARCH_TOP_K must be greater than 0.")


# ============================================================
# DEBUG / INTROSPECTION HELPERS
# ============================================================

def to_dict() -> dict:
    """Return a plain dict snapshot of every explicit config value."""
    snapshot: dict = {}
    for key, value in globals().items():
        if key.startswith("_"):
            continue
        if key.isupper():
            snapshot[key] = str(value)
    return snapshot


def get_config_summary() -> str:
    """Human-readable summary of the active config (for --debug logs)."""
    lines = [
        "DesktopAI Configuration Summary",
        "───────────────────────────────",
        f"  APP              : {APP_NAME} v{APP_VERSION}",
        f"  MOCK_AI          : {MOCK_AI}",
        f"  DEBUG            : {DEBUG}",
        f"  OLLAMA_URL       : {OLLAMA_URL}",
        f"  OLLAMA_MODEL     : {OLLAMA_MODEL}",
        f"  EMBEDDING_MODEL  : {EMBEDDING_MODEL}",
        f"  DATA_DIR         : {DATA_DIR}",
        f"  DATABASE_PATH    : {DATABASE_PATH}",
        f"  SEARCH_INDEX_PATH: {SEARCH_INDEX_PATH}",
        f"  SEARCH_TOP_K     : {SEARCH_TOP_K}",
        f"  MAX_WORKERS      : {MAX_WORKERS}",
        f"  LOG_LEVEL        : {LOG_LEVEL}",
    ]
    return "\n".join(lines)


# ============================================================
# CRASH-PROOF FALLBACK (PEP 562 module __getattr__)
# ============================================================
# If any legacy module references config.SOMETHING that is not explicitly
# defined above, we return a sensible default derived from the name and
# print a warning — instead of raising AttributeError at import time.
#
# Watch the console/log for "[config] fallback" lines: each one tells you
# exactly which constant a legacy module expects so it can be promoted to
# an explicit definition above.

_FALLBACK_LOGGED: set[str] = set()


def _fallback_default(name: str):
    """Derive a sensible default value from a missing constant's name."""
    if name.endswith("_URL"):
        return OLLAMA_HOST
    if name.endswith("_TIMEOUT") or name.endswith("_SECONDS"):
        return OLLAMA_TIMEOUT
    if name.endswith("_PATH"):
        return DATA_DIR / name.lower().replace("_path", "")
    if name.endswith("_DIR"):
        return DATA_DIR / name.lower().replace("_dir", "")
    if name.endswith("_MODEL"):
        return OLLAMA_MODEL
    if name.endswith("_MAX_TEXT_LENGTH") or name.endswith("_MAX_LENGTH"):
        return AI_MAX_TEXT_LENGTH
    if name.endswith("_ENABLED"):
        return True
    if name.endswith("_SIZE") or name.endswith("_TOP_K") or name.endswith("_K"):
        return 10
    if name.endswith("_THRESHOLD") or name.endswith("_CONFIDENCE"):
        return 0.5
    if name.endswith("_BATCH_SIZE") or name.endswith("_WORKERS"):
        return MAX_WORKERS
    return ""


def __getattr__(name: str):
    """
    Module-level attribute fallback.

    Only fires when normal attribute lookup fails, i.e. for constants a
    legacy module expects that this file does not define explicitly.
    """
    if name.startswith("_"):
        raise AttributeError(name)

    default = _fallback_default(name)

    if name not in _FALLBACK_LOGGED:
        _FALLBACK_LOGGED.add(name)
        print(
            f"[config] fallback: '{name}' is not defined in core/config.py "
            f"— using default {default!r}. Add it explicitly to silence this.",
            flush=True,
        )

    # Cache into module globals so the fallback only computes once.
    globals()[name] = default
    return default


# ============================================================
# INITIALIZE CONFIGURATION
# ============================================================

ensure_directories()
validate_config()