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

DesktopAI currently includes an early foundation for local file indexing:

- Recursive folder scanning with a configurable depth limit
- File metadata extraction
- SHA-256 file hashing
- File type detection from file content
- SQLite storage for scanned file metadata
- Centralized logging
- Unit tests for scanner, database, and logger behavior

---

## Planned Features

### File Management

- Intelligent file organization
- Automatic categorization
- Duplicate detection
- Large file discovery
- Empty folder cleanup
- Undo support for file operations

### Document Intelligence

- PDF understanding
- Word document reading
- Excel analysis
- OCR for images
- Metadata extraction

### AI

- Local Large Language Models
- Natural language commands
- AI reasoning
- Personalized recommendations
- Offline-first operation

### Search

- Semantic search
- Keyword search
- Content search
- Smart filters

---

## Tech Stack

- Python 3.13
- SQLite
- pytest
- filetype
- Watchdog
- Ollama
- PySide6
- FAISS
- EasyOCR
- PyMuPDF

---

## Project Status

Phase 4 - Database foundation

---

## Roadmap

- [x] Project Planning
- [x] File Scanner
- [x] File Hashing
- [x] File Type Detection
- [x] SQLite Database Foundation
- [x] Logging
- [x] Unit Tests
- [ ] Configuration Management
- [ ] AI Integration
- [ ] Organizer Engine
- [ ] Semantic Search
- [ ] GUI
- [ ] Voice Support

---

## License

MIT License