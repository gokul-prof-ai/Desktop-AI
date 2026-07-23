# DesktopAI

> Offline-first AI Desktop Assistant for Windows

DesktopAI is an intelligent desktop assistant designed to organize, understand, search, and manage files locally using AI.

Unlike cloud-based assistants, DesktopAI runs primarily on your computer, ensuring privacy while providing intelligent automation.

---

## Vision

DesktopAI is more than a file organizer.

It is designed to become an AI Operating System Companion capable of:

- Organizing files intelligently
- Understanding documents
- Performing semantic search
- Learning user preferences
- Automating repetitive tasks
- Assisting with desktop productivity

---

## Current Capabilities

DesktopAI currently includes:

- Recursive folder scanning with a configurable depth limit
- File metadata extraction
- SHA-256 file hashing
- File type detection from file content
- SQLite storage for scanned file metadata
- Text extraction from PDF, DOCX, and Excel files, plus OCR for images
- Local AI file classification, summarization, and folder recommendations (via Ollama)
- File organization with a mandatory preview step and full undo support
- Offline-first folder watching (Downloads/Desktop) with real-time AI suggestions
- Semantic (natural-language) search over scanned files via local embeddings (`all-minilm`) and FAISS
- Scanning a real folder: pass a path to `python src/app.py <folder>`, or set `DESKTOPAI_SCAN_FOLDER`
- Centralized logging and configuration
- Unit tests covering every module above (88 tests)

---

## Planned Features

### File Management

- Automatic categorization
- Duplicate detection
- Large file discovery
- Empty folder cleanup

### AI

- Natural language commands
- Auto-organize (move files) straight from watcher suggestions, not just print them

### Search

- Keyword search
- Content search
- Smart filters

### Interface

- Desktop GUI (PySide6)
- Voice support

---

## Tech Stack

- Python 3.13
- SQLite
- pytest
- filetype
- Watchdog
- Ollama
- PyMuPDF (PDF text extraction)
- python-docx (Word text extraction)
- openpyxl (Excel text extraction)
- pytesseract (OCR for images)
- FAISS + NumPy (semantic search)
- PySide6 (planned, GUI)

---

## Project Status

Phase 9 - Semantic Search complete (see [docs/roadmap.md](docs/roadmap.md) for the full phase breakdown)

---

## Roadmap

- [x] Project Planning
- [x] File Scanner
- [x] File Hashing
- [x] File Type Detection
- [x] SQLite Database Foundation
- [x] Logging
- [x] Unit Tests
- [x] Document Readers (PDF, DOCX, Excel, OCR)
- [x] Configuration Management
- [x] AI Integration (classification, summarization, recommendations)
- [x] Organizer Engine (preview, apply, undo)
- [x] Folder Watcher
- [x] Semantic Search
- [ ] GUI
- [ ] Voice Support

---

## License

MIT License