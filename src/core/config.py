"""
Application Configuration
=========================
Centralized configuration for Desktop AI.

This file contains:
- Application settings
- AI / Ollama settings
- File processing limits
- Classifier limits
- Summarizer limits
- Recommender limits
- Performance settings
- Logging settings
- Supported file extensions
"""

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

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = Path(
    _get_env(
        "DESKTOP_AI_DATA_DIR",
        str(BASE_DIR / "data"),
    )
)

CACHE_DIR = Path(
    _get_env(
        "DESKTOP_AI_CACHE_DIR",
        str(DATA_DIR / "cache"),
    )
)

LOG_DIR = Path(
    _get_env(
        "DESKTOP_AI_LOG_DIR",
        str(DATA_DIR / "logs"),
    )
)

REPORT_DIR = Path(
    _get_env(
        "DESKTOP_AI_REPORT_DIR",
        str(DATA_DIR / "reports"),
    )
)


# ============================================================
# APPLICATION
# ============================================================

APP_NAME = _get_env(
    "APP_NAME",
    "Desktop AI",
)

APP_VERSION = _get_env(
    "APP_VERSION",
    "2.0.0",
)

DEBUG = _get_bool(
    "DEBUG",
    False,
)


# ============================================================
# AI / OLLAMA CONFIGURATION
# ============================================================

OLLAMA_HOST = _get_env(
    "OLLAMA_HOST",
    "http://127.0.0.1:11434",
)

OLLAMA_MODEL = _get_env(
    "OLLAMA_MODEL",
    "llama3.2:3b",
)

OLLAMA_TIMEOUT = _get_float(
    "OLLAMA_TIMEOUT",
    120.0,
)

OLLAMA_CONNECT_TIMEOUT = _get_float(
    "OLLAMA_CONNECT_TIMEOUT",
    10.0,
)

OLLAMA_TEMPERATURE = _get_float(
    "OLLAMA_TEMPERATURE",
    0.2,
)

OLLAMA_MAX_TOKENS = _get_int(
    "OLLAMA_MAX_TOKENS",
    2048,
)


# ============================================================
# AI PROCESSING LIMITS
# ============================================================

# Maximum amount of text sent to the general AI processor.
AI_MAX_TEXT_LENGTH = _get_int(
    "AI_MAX_TEXT_LENGTH",
    8000,
)

# Maximum number of characters used when extracting document text.
DOCUMENT_MAX_TEXT_LENGTH = _get_int(
    "DOCUMENT_MAX_TEXT_LENGTH",
    10000,
)

# Maximum text passed to the classifier.
#
# This is the configuration you asked about.
CLASSIFIER_MAX_TEXT_LENGTH = _get_int(
    "CLASSIFIER_MAX_TEXT_LENGTH",
    2000,
)

# Maximum text passed to the summarizer.
SUMMARIZER_MAX_TEXT_LENGTH = _get_int(
    "SUMMARIZER_MAX_TEXT_LENGTH",
    4000,
)

# Maximum text preview used by the recommender.
RECOMMENDER_MAX_TEXT_PREVIEW_LENGTH = _get_int(
    "RECOMMENDER_MAX_TEXT_PREVIEW_LENGTH",
    500,
)


# ============================================================
# FILE PROCESSING
# ============================================================

MAX_FILE_SIZE_MB = _get_int(
    "MAX_FILE_SIZE_MB",
    100,
)

MAX_FILE_SIZE_BYTES = (
    MAX_FILE_SIZE_MB * 1024 * 1024
)

MAX_FILES_PER_SCAN = _get_int(
    "MAX_FILES_PER_SCAN",
    10000,
)

MAX_FOLDER_DEPTH = _get_int(
    "MAX_FOLDER_DEPTH",
    20,
)


# ============================================================
# PDF PROCESSING
# ============================================================

PDF_MAX_PAGES = _get_int(
    "PDF_MAX_PAGES",
    100,
)

PDF_MAX_TEXT_LENGTH = _get_int(
    "PDF_MAX_TEXT_LENGTH",
    50000,
)


# ============================================================
# OCR CONFIGURATION
# ============================================================

OCR_ENABLED = _get_bool(
    "OCR_ENABLED",
    True,
)

OCR_MAX_PAGES = _get_int(
    "OCR_MAX_PAGES",
    20,
)

OCR_MAX_IMAGE_SIZE_MB = _get_int(
    "OCR_MAX_IMAGE_SIZE_MB",
    20,
)


# ============================================================
# EXCEL / CSV PROCESSING
# ============================================================

EXCEL_MAX_ROWS = _get_int(
    "EXCEL_MAX_ROWS",
    10000,
)

EXCEL_MAX_COLUMNS = _get_int(
    "EXCEL_MAX_COLUMNS",
    100,
)

CSV_MAX_ROWS = _get_int(
    "CSV_MAX_ROWS",
    10000,
)


# ============================================================
# TEXT / DOCUMENT PROCESSING
# ============================================================

TEXT_MAX_FILE_SIZE_MB = _get_int(
    "TEXT_MAX_FILE_SIZE_MB",
    20,
)

WORD_MAX_TEXT_LENGTH = _get_int(
    "WORD_MAX_TEXT_LENGTH",
    30000,
)


# ============================================================
# CLASSIFICATION
# ============================================================

CLASSIFICATION_ENABLED = _get_bool(
    "CLASSIFICATION_ENABLED",
    True,
)

CLASSIFICATION_CONFIDENCE_THRESHOLD = _get_float(
    "CLASSIFICATION_CONFIDENCE_THRESHOLD",
    0.60,
)

CLASSIFICATION_BATCH_SIZE = _get_int(
    "CLASSIFICATION_BATCH_SIZE",
    10,
)


# ============================================================
# SUMMARIZATION
# ============================================================

SUMMARIZATION_ENABLED = _get_bool(
    "SUMMARIZATION_ENABLED",
    True,
)

SUMMARY_MAX_SENTENCES = _get_int(
    "SUMMARY_MAX_SENTENCES",
    8,
)


# ============================================================
# RECOMMENDATION ENGINE
# ============================================================

RECOMMENDER_ENABLED = _get_bool(
    "RECOMMENDER_ENABLED",
    True,
)

RECOMMENDER_MAX_RESULTS = _get_int(
    "RECOMMENDER_MAX_RESULTS",
    10,
)

RECOMMENDER_MIN_CONFIDENCE = _get_float(
    "RECOMMENDER_MIN_CONFIDENCE",
    0.50,
)


# ============================================================
# FILE ORGANIZATION
# ============================================================

ORGANIZATION_ENABLED = _get_bool(
    "ORGANIZATION_ENABLED",
    True,
)

AUTO_MOVE_FILES = _get_bool(
    "AUTO_MOVE_FILES",
    False,
)

CREATE_MISSING_FOLDERS = _get_bool(
    "CREATE_MISSING_FOLDERS",
    True,
)

PRESERVE_FILE_NAMES = _get_bool(
    "PRESERVE_FILE_NAMES",
    True,
)


# ============================================================
# PERFORMANCE
# ============================================================

MAX_WORKERS = _get_int(
    "MAX_WORKERS",
    max(2, (os.cpu_count() or 4) // 2),
)

SCAN_BATCH_SIZE = _get_int(
    "SCAN_BATCH_SIZE",
    100,
)

PROCESS_BATCH_SIZE = _get_int(
    "PROCESS_BATCH_SIZE",
    20,
)

CACHE_ENABLED = _get_bool(
    "CACHE_ENABLED",
    True,
)


# ============================================================
# LOGGING
# ============================================================

LOG_LEVEL = _get_env(
    "LOG_LEVEL",
    "INFO",
)

LOG_FILE_NAME = _get_env(
    "LOG_FILE_NAME",
    "desktop_ai.log",
)

LOG_MAX_SIZE_MB = _get_int(
    "LOG_MAX_SIZE_MB",
    10,
)

LOG_BACKUP_COUNT = _get_int(
    "LOG_BACKUP_COUNT",
    5,
)


# ============================================================
# SUPPORTED FILE EXTENSIONS
# ============================================================

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".log",
    ".csv",
}

DOCUMENT_EXTENSIONS = {
    ".doc",
    ".docx",
    ".odt",
    ".rtf",
}

PDF_EXTENSIONS = {
    ".pdf",
}

SPREADSHEET_EXTENSIONS = {
    ".xls",
    ".xlsx",
    ".xlsm",
    ".ods",
}

PRESENTATION_EXTENSIONS = {
    ".ppt",
    ".pptx",
    ".odp",
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
}

ARCHIVE_EXTENSIONS = {
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
}


# ============================================================
# FAST PATH RULES
# ============================================================

FAST_PATH_RULES = {
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
    """
    Create application directories if they do not already exist.
    """
    directories = (
        DATA_DIR,
        CACHE_DIR,
        LOG_DIR,
        REPORT_DIR,
    )

    for directory in directories:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


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
        raise ValueError(
            "OLLAMA_HOST cannot be empty."
        )

    if not OLLAMA_MODEL:
        raise ValueError(
            "OLLAMA_MODEL cannot be empty."
        )

    if not 0 <= OLLAMA_TEMPERATURE <= 2:
        raise ValueError(
            "OLLAMA_TEMPERATURE must be between 0 and 2."
        )

    if not 0 < CLASSIFICATION_CONFIDENCE_THRESHOLD <= 1:
        raise ValueError(
            "CLASSIFICATION_CONFIDENCE_THRESHOLD "
            "must be between 0 and 1."
        )

    if not 0 < RECOMMENDER_MIN_CONFIDENCE <= 1:
        raise ValueError(
            "RECOMMENDER_MIN_CONFIDENCE "
            "must be between 0 and 1."
        )

    if MAX_FILE_SIZE_MB <= 0:
        raise ValueError(
            "MAX_FILE_SIZE_MB must be greater than 0."
        )

    if MAX_FILES_PER_SCAN <= 0:
        raise ValueError(
            "MAX_FILES_PER_SCAN must be greater than 0."
        )

    if MAX_WORKERS <= 0:
        raise ValueError(
            "MAX_WORKERS must be greater than 0."
        )


# ============================================================
# INITIALIZE CONFIGURATION
# ============================================================

ensure_directories()
validate_config()

# ============================================================
# FOLDER WATCHER
# ============================================================

# Folders monitored by FolderWatcher.
# Override via DESKTOP_AI_WATCH_FOLDERS (colon-separated paths).
_watch_folders_env = os.getenv("DESKTOP_AI_WATCH_FOLDERS", "")
WATCH_FOLDERS: list[Path] = (
    [Path(p) for p in _watch_folders_env.split(":") if p.strip()]
    if _watch_folders_env
    else [Path.home() / "Downloads", Path.home() / "Desktop"]
)

WATCH_STABILITY_SECONDS: int = _get_int("WATCH_STABILITY_SECONDS", 2)
WATCH_POLL_INTERVAL_SECONDS: int = _get_int("WATCH_POLL_INTERVAL_SECONDS", 1)
