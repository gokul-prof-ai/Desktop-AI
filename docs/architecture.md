# Architecture Overview

## System Layers (Detailed)

### Layer 1: User Interface

- CLI (current)
- GUI (PySide6, planned)
- Web dashboard (future)

### Layer 2: Application Core

- Scanner Module
- Organizer Module
- Watcher Module
- Search Module

### Layer 3: AI Services

- Ollama Integration
- Classification Engine
- Summarization Engine
- Recommendation Engine

### Layer 4: Data Management

- SQLite Database
- FAISS Vector Store
- File System
- Metadata Cache

## Data Flow Diagrams

[Add mermaid/ASCII diagrams for:]

- Scanning → Classification → Organization
- Search Query → Embedding → FAISS → Results
- File Watch → AI Analysis → Suggestions

## Module Dependencies

\`\`\`
Scanner → Database
↓
Organizer → AI Services
↓
Watcher → Notification System
\`\`\`

## Extension Points

- How to add new file readers
- How to add new AI models
- How to add new search strategies
