import os
from pathlib import Path

# -----------------------------------------------------------------------------
# Base directories
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

for directory in (DATA_DIR, LOGS_DIR, CONFIG_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# AI / Ollama configuration
# -----------------------------------------------------------------------------

OLLAMA_MODEL = os.getenv("DESKTOPAI_OLLAMA_MODEL", "llama3.2")
OLLAMA_MODEL_FAST = os.getenv("DESKTOPAI_OLLAMA_MODEL_FAST", "llama3.2:1b")
OLLAMA_HOST = os.getenv("DESKTOPAI_OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"
OLLAMA_EMBEDDINGS_URL = f"{OLLAMA_HOST}/api/embeddings"
OLLAMA_TIMEOUT_SECONDS = int(
    os.getenv("DESKTOPAI_OLLAMA_TIMEOUT_SECONDS", "30")
)

# Dedicated embedding model for semantic search. This must be separate from
# the general-purpose LLM because Ollama embedding models return vectors.
EMBEDDING_MODEL = os.getenv(
    "DESKTOPAI_EMBEDDING_MODEL",
    "nomic-embed-text",
)

# -----------------------------------------------------------------------------
# Folder watcher configuration
# -----------------------------------------------------------------------------

WATCH_STABILITY_SECONDS = int(
    os.getenv("DESKTOPAI_WATCH_STABILITY_SECONDS", "2")
)
WATCH_POLL_INTERVAL_SECONDS = int(
    os.getenv("DESKTOPAI_WATCH_POLL_INTERVAL_SECONDS", "1")
)

# Default watched folders. Callers can always provide an explicit list to
# FolderWatcher, which is what the tests do. Environment variables allow users
# to override the defaults without modifying source code.
def _default_watch_folders() -> list[Path]:
    configured = os.getenv("DESKTOPAI_WATCH_FOLDERS", "").strip()
    if configured:
        return [Path(item).expanduser() for item in configured.split(os.pathsep) if item.strip()]

    home = Path.home()
    return [
        home / "Downloads",
        home / "Desktop",
    ]


WATCH_FOLDERS = _default_watch_folders()

# -----------------------------------------------------------------------------
# Performance configuration
# -----------------------------------------------------------------------------

MAX_WORKERS = int(os.getenv("DESKTOPAI_MAX_WORKERS", "4"))
HASH_CHUNK_SIZE = int(os.getenv("DESKTOPAI_HASH_CHUNK_SIZE", "8192"))

# -----------------------------------------------------------------------------
# Scanner configuration
# -----------------------------------------------------------------------------

SCAN_MAX_DEPTH = int(os.getenv("DESKTOPAI_SCAN_MAX_DEPTH", "10"))
SUPPORTED_EXTENSIONS = [
    ".pdf", ".docx", ".xlsx", ".xls", ".txt", ".md", ".csv", ".json",
    ".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".rs", ".go",
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".heic",
    ".mp3", ".wav", ".mp4", ".mkv", ".avi",
    ".zip", ".rar", ".7z", ".tar", ".gz",
]
