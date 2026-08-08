import os
from pathlib import Path

# -----------------------------------------------------------------------------
# Base directories
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

# Ensure runtime directories exist.
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# Database / Search storage
# -----------------------------------------------------------------------------

# Central SQLite database used by DatabaseManager and the semantic search
# engine when no explicit database path is supplied.
DATABASE_PATH = Path(
    os.getenv("DESKTOPAI_DATABASE_PATH", str(DATA_DIR / "desktop_ai.db"))
)

# Base path for the FAISS semantic-search index. SearchIndex adds .faiss and
# .json automatically when saving/loading.
SEARCH_INDEX_PATH = Path(
    os.getenv("DESKTOPAI_SEARCH_INDEX_PATH", str(DATA_DIR / "search_index"))
)

# Maximum amount of extracted text sent to the embedding model per file.
EMBEDDING_MAX_TEXT_LENGTH = int(
    os.getenv("DESKTOPAI_EMBEDDING_MAX_TEXT_LENGTH", "10000")
)

# Default number of semantic-search matches returned.
SEARCH_TOP_K = int(os.getenv("DESKTOPAI_SEARCH_TOP_K", "10"))

# -----------------------------------------------------------------------------
# AI / Ollama configuration
# -----------------------------------------------------------------------------

OLLAMA_MODEL = os.getenv("DESKTOPAI_OLLAMA_MODEL", "llama3.2")
OLLAMA_MODEL_FAST = os.getenv(
    "DESKTOPAI_OLLAMA_MODEL_FAST", "llama3.2:1b"
)  # Ultra-fast for sorting
OLLAMA_HOST = os.getenv(
    "DESKTOPAI_OLLAMA_HOST", "http://localhost:11434"
).rstrip("/")
OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"

# Small local model dedicated to semantic-search embeddings.
EMBEDDING_MODEL = os.getenv(
    "DESKTOPAI_EMBEDDING_MODEL", "nomic-embed-text"
)
OLLAMA_EMBEDDINGS_URL = f"{OLLAMA_HOST}/api/embeddings"

OLLAMA_TIMEOUT_SECONDS = int(
    os.getenv("DESKTOPAI_OLLAMA_TIMEOUT_SECONDS", "30")
)

# -----------------------------------------------------------------------------
# Folder watcher
# -----------------------------------------------------------------------------

# A file must remain unchanged for this many seconds before it is considered
# stable and ready for processing.
WATCH_STABILITY_SECONDS = int(
    os.getenv("DESKTOPAI_WATCH_STABILITY_SECONDS", "2")
)

# How frequently the watcher checks file stability.
WATCH_POLL_INTERVAL_SECONDS = int(
    os.getenv("DESKTOPAI_WATCH_POLL_INTERVAL_SECONDS", "1")
)

# -----------------------------------------------------------------------------
# Performance configuration
# -----------------------------------------------------------------------------

MAX_WORKERS = int(os.getenv("DESKTOPAI_MAX_WORKERS", "4"))
HASH_CHUNK_SIZE = 8192

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
