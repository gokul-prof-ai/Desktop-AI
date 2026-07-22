# DesktopAI Architecture

## High-Level Architecture

```
                         User

                           │

                  DesktopAI Interface

                           │

                    AI Planner / Brain

                           │

      ┌────────────────────┼────────────────────┐

      │                    │                    │

 File Scanner        Search Engine       Organizer

      │                    │                    │

      └────────────────────┼────────────────────┘

                           │

                    SQLite Database

                           │

      ┌────────────────────┼────────────────────┐

      │                    │                    │

 Document Reader      AI Models         Memory System

      │                    │                    │

 PDF / DOCX / XLSX     Ollama         User Preferences
```

---

## Module Responsibilities

### Scanner

Scans folders and extracts metadata from files.

### Database

Stores metadata, history, settings, and AI-generated information.

### AI Engine

Uses local language models to classify files, summarize content, and suggest actions.

### Organizer

Moves, renames, archives, and manages files after user approval.

### Search

Provides keyword and semantic search across indexed files.

### Memory

Learns user preferences and improves future recommendations.

### GUI

Provides a desktop interface for interacting with DesktopAI.

---

## Data Flow

```
User Request

↓

Scan Files

↓

Extract Metadata

↓

Read Documents

↓

AI Analysis

↓

Generate Suggestions

↓

User Approval

↓

Execute Actions

↓

Save History
```

---

## Core Design Principles

- Offline-first
- Privacy-first
- Modular architecture
- Safe automation
- User approval before destructive actions
- Explainable AI decisions
- Extensible design