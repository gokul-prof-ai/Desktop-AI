# DesktopAI

> Offline-first AI Desktop Assistant for Intelligent File Organization

[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue)]()
[![Tests](https://img.shields.io/badge/Tests-88%2F88-green)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]()

DesktopAI is an intelligent offline desktop assistant that organizes, understands, and searches your files using local AI.

**[📖 Full Documentation](docs/00-TABLE_OF_CONTENTS.md)** | **[🚀 Quick Start](QUICK_START.md)** | **[🤝 Contributing](CONTRIBUTING.md)**

## ⚡ Quick Demo

```bash
# 1. Install (2 min)
git clone https://github.com/gokul-prof-ai/Desktop-AI.git
cd Desktop-AI && pip install -r requirements.txt

# 2. Run (1 min)
python src/app.py C:\Users\YourName\Downloads

# 3. Search (Instant)
python src/search_app.py
> "Find all budget spreadsheets from 2024"
✓ Results: budget-2024-q1.xlsx, budget-2024-q2.xlsx, ...
```

## Features

### 🔍 Smart File Organization

- AI-powered file classification
- Preview before changes
- Full undo support
- Intelligent folder recommendations

### 🧠 Semantic Search

- Natural language queries
- Local embeddings (privacy-first)
- Sub-200ms search on 10K files

### 📝 Document Understanding

- PDF, DOCX, Excel extraction
- OCR for images
- Automatic summarization

### 👀 Real-Time Monitoring

- Watch Downloads/Desktop folders
- Get AI suggestions instantly
- Auto-organize on demand (v2.0)

## Tech Stack

- Python 3.13
- SQLite + FAISS
- Ollama (local LLM)
- PySide6 (GUI, planned)

## Installation

See [Installation Guide](docs/01-INSTALLATION.md) for detailed setup.

```bash
pip install -r requirements.txt
python src/app.py <folder>
```

## Usage

- **User Guide:** [docs/03-USER_GUIDE.md](docs/03-USER_GUIDE.md)
- **Configuration:** [docs/10-CONFIGURATION.md](docs/10-CONFIGURATION.md)
- **Troubleshooting:** [docs/11-TROUBLESHOOTING.md](docs/11-TROUBLESHOOTING.md)

## Development

- **Setup:** [docs/07-DEVELOPMENT.md](docs/07-DEVELOPMENT.md)
- **Architecture:** [docs/04-ARCHITECTURE.md](docs/04-ARCHITECTURE.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Testing:** [docs/09-TESTING.md](docs/09-TESTING.md)

## Project Status

Phase 9 Complete: Semantic Search ✅
Next: GUI Application (v1.0)

[Full Roadmap](docs/13-ROADMAP.md)

## License

MIT License © 2024 Gokul

---

**Questions?** Check [Troubleshooting](docs/11-TROUBLESHOOTING.md) or [open an issue](https://github.com/gokul-prof-ai/Desktop-AI/issues)
