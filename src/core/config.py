import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# AI Configuration

OLLAMA_MODEL = os.getenv(
    "DESKTOPAI_OLLAMA_MODEL",
    "llama3.2"
)

OLLAMA_MODEL_FAST = os.getenv(
    "DESKTOPAI_OLLAMA_MODEL_FAST",
    "llama3.2:1b"
)

OLLAMA_HOST = os.getenv(
    "DESKTOPAI_OLLAMA_HOST",
    "http://localhost:11434"
)

OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"


# ---------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------

EMBEDDING_MODEL = os.getenv(
    "DESKTOPAI_EMBEDDING_MODEL",
    "nomic-embed-text",
)

OLLAMA_EMBEDDINGS_URL = f"{OLLAMA_HOST}/api/embeddings"

OLLAMA_TIMEOUT_SECONDS = int(
    os.getenv("DESKTOPAI_OLLAMA_TIMEOUT_SECONDS", "30")
)


# ---------------------------------------------------------------
# Folder Watcher
# ---------------------------------------------------------------

WATCH_STABILITY_SECONDS = int(
    os.getenv("DESKTOPAI_WATCH_STABILITY_SECONDS", "2")
)

WATCH_POLL_INTERVAL_SECONDS = int(
    os.getenv("DESKTOPAI_WATCH_POLL_INTERVAL_SECONDS", "1")
)

# Performance Configuration
MAX_WORKERS = int(os.getenv("DESKTOPAI_MAX_WORKERS", "4"))
HASH_CHUNK_SIZE = 8192

# Scanner Configuration
SCAN_MAX_DEPTH = 10 
SUPPORTED_EXTENSIONS = [
    ".pdf", ".docx", ".xlsx", ".xls", ".txt", ".md", ".csv", ".json",
    ".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".rs", ".go",
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".heic",
    ".mp3", ".wav", ".mp4", ".mkv", ".avi",
    ".zip", ".rar", ".7z", ".tar", ".gz"
]