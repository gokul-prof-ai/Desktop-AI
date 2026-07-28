# 🚀 DesktopAI Organizer

**DesktopAI** is a modern, offline-first, AI-powered desktop application that intelligently analyzes, categorizes, and organizes your files locally. Built with privacy in mind, it uses local Large Language Models (LLMs) via Ollama to understand your files without ever sending your data to the cloud.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green?logo=qt)
![AI](https://img.shields.io/badge/AI-Ollama-ff7000?logo=ollama)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Key Features

- **🧠 Hybrid AI Categorization:** Instant rule-based sorting (milliseconds) + Local LLM fallback for ambiguous files (seconds).
- **🎨 Modern GUI:** Dark theme, drag-and-drop, live progress, and smart preview tables.
- **🔒 100% Offline & Private:** Your files and AI prompts never leave your machine.
- **🛡️ Robust & Reliable:** Handles Windows file locks, corrupted files, and includes a 1-click Undo feature.

---

## 📦 Installation & Setup

### Prerequisites

1. Python 3.10+ installed.
2. Ollama installed and running (`ollama serve`).

### Steps

bash
git clone https://github.com/gokul-prof-ai/Desktop-AI.git
cd Desktop-AI
python -m venv .venv
.venv\Scripts\activate # Windows
pip install -r requirements.txt
ollama pull llama3.2:1b

---

## 🚀 How to Use

1. Launch the app: `python run.py`
2. Drag and drop a messy folder into the Drop Zone.
3. Click **🔍 Analyze Folder** to see AI suggestions.
4. Click **✅ Apply Organization** to move files.
5. Made a mistake? Click **↩️ Undo Last**.

---

## 📂 Project Structure

````text
Desktop-AI/
├── src/
│   ├── ai/               # Hybrid AI categorizer
│   ├── core/             # Config and logging
│   ├── documents/        # PDF, DOCX, Excel, OCR parsers
│   ├── gui/              # PySide6 Modern GUI
│   ├── organizer/        # Auto-organizer pipeline
│   └── scanner/          # Recursive file scanner
├── docs/                 # Professional documentation
├── run.py                # Main app launcher
└── requirements.txt      # Dependencies

---

### 📁 FOLDER 2: `src/core/`

#### 📄 File: `src/core/config.py`
```python
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
OLLAMA_MODEL = os.getenv("DESKTOPAI_OLLAMA_MODEL", "llama3.2")
OLLAMA_MODEL_FAST = os.getenv("DESKTOPAI_OLLAMA_MODEL_FAST", "llama3.2:1b")
OLLAMA_HOST = os.getenv("DESKTOPAI_OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"

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
````
