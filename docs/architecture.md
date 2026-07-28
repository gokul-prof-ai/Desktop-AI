# 🏗️ Architecture Overview

Desktop-AI is built with a modular, scalable architecture. This guide explains how the system works under the hood.

## Table of Contents

- [System Architecture](#system-architecture)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Database Schema](#database-schema)
- [Design Patterns](#design-patterns)
- [Performance Considerations](#performance-considerations)

---

## System Architecture

### High-Level View

```
┌─────────────────────────────────────────────────────────┐
│                  Desktop-AI System                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │           User Interface Layer                    │   │
│  │  ┌────────────────────────────────────────────┐  │   │
│  │  │  Web Dashboard (HTML/CSS/JS)              │  │   │
│  │  │  Desktop GUI (PySide6 Qt)                 │  │   │
│  │  │  CLI Commands                             │  │   │
│  │  └────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Application Logic Layer                   │   │
│  │  ┌──────────────┐  ┌──────────────────────┐     │   │
│  │  │   Scanner    │  │  AI Integration      │     │   │
│  │  │   - Scan     │  │  - Classification    │     │   │
│  │  │   - Hash     │  │  - Summarization     │     │   │
│  │  │   - Metadata │  │  - Recommendations   │     │   │
│  │  └──────────────┘  └──────────────────────┘     │   │
│  │                                                   │   │
│  │  ┌──────────────┐  ┌──────────────────────┐     │   │
│  │  │  Organizer   │  │  Search Engine       │     │   │
│  │  │  - Plan      │  │  - Semantic Search   │     │   │
│  │  │  - Preview   │  │  - Full-text Search  │     │   │
│  │  │  - Apply     │  │  - Filtering         │     │   │
│  │  │  - Undo      │  └──────────────────────┘     │   │
│  │  └──────────────┘                                │   │
│  │                                                   │   │
│  │  ┌──────────────────────────────────────────┐   │   │
│  │  │  Real-Time Watcher                       │   │   │
│  │  │  - Monitor folders                       │   │   │
│  │  │  - Detect changes                        │   │   │
│  │  │  - Trigger organization                  │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Processing Layer                         │   │
│  │  ┌──────────────────────────────────────────┐   │   │
│  │  │  Document Reader                         │   │   │
│  │  │  - PDF extraction                        │   │   │
│  │  │  - DOCX parsing                          │   │   │
│  │  │  - Excel reading                         │   │   │
│  │  │  - OCR for images                        │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Storage Layer                            │   │
│  │  ┌──────────────┐  ┌──────────────────────┐     │   │
│  │  │   SQLite DB  │  │  FAISS Vectors       │     │   │
│  │  │  - Metadata  │  │  - Embeddings        │     │   │
│  │  │  - History   │  │  - Search index      │     │   │
│  │  │  - Config    │  └──────────────────────┘     │   │
│  │  └──────────────┘                                │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │         External Services                        │   │
│  │  ┌──────────────────────────────────────────┐   │   │
│  │  │  Ollama (Local LLM)                      │   │   │
│  │  │  - Inference                             │   │   │
│  │  │  - Model management                      │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. File Scanner (`src/scanner/`)

**Purpose:** Recursively scan directories and extract file information.

**Key Classes:**

```python
class FileScanner:
    """Scan directories and extract metadata"""
    - scan(directory, max_depth)
    - get_metadata(file_path)
    - calculate_hash(file_path)
    - detect_file_type(file_path)

class FileMetadata:
    """Structured file information"""
    - path: str
    - size: int
    - created: datetime
    - modified: datetime
    - type: str
    - hash: str
    - content_snippet: str
```

**How it works:**

1. Recursively traverses file system
2. Extracts metadata for each file
3. Calculates SHA-256 hash for duplicates
4. Detects file type from content
5. Stores in database

**Performance:**

- ~10,000 files/second on typical hardware
- Configurable recursion depth
- Batch processing for efficiency

### 2. AI Engine (`src/ai/`)

**Purpose:** Integrate Ollama for intelligent file operations.

**Key Classes:**

```python
class OllamaIntegration:
    """Manage Ollama connection and inference"""
    - classify_file(file_info)
    - summarize_content(text)
    - generate_recommendations(files)
    - validate_connection()

class Classifier:
    """AI-powered file classification"""
    - classify(file_metadata) -> Category
    - get_confidence() -> float
    - suggest_folder() -> str
```

**How it works:**

1. Connects to local Ollama instance
2. Sends file metadata to LLM
3. Receives classification categories
4. Scores confidence level
5. Caches results for performance

**Supported Models:**

- Mistral (balanced, recommended)
- Llama 2 (larger, slower)
- Neural Chat (smaller, faster)
- Zephyr (specialized)

### 3. Database Layer (`src/database/`)

**Purpose:** Persistent storage for all metadata and operations.

**Key Classes:**

```python
class DatabaseManager:
    """SQLite operations"""
    - insert_file_metadata(metadata)
    - query_files(filters)
    - get_file_by_hash(hash)
    - update_organization_history()

class QueryBuilder:
    """Construct efficient queries"""
    - build_search_query(filters)
    - apply_sorting(sort_by)
    - paginate_results(page, per_page)
```

**Tables:**

- `files` — File metadata
- `classifications` — AI classifications
- `organizations` — Organization history
- `embeddings` — FAISS vector data
- `config` — User settings

### 4. Document Reader (`src/document_reader/`)

**Purpose:** Extract text and metadata from various file formats.

**Key Classes:**

```python
class DocumentReader:
    """Factory for document readers"""
    - read(file_path) -> Content

class PDFReader(DocumentReader):
    """Extract text from PDFs"""
    - read_pdf()
    - extract_metadata()
    - handle_scanned_images()

class OfficeReader(DocumentReader):
    """Parse DOCX and XLSX files"""
    - read_docx()
    - read_xlsx()
    - extract_formatting()

class ImageOCR(DocumentReader):
    """OCR for scanned documents"""
    - extract_text()
    - confidence_score()
```

**Supported Formats:**

- PDF (PyMuPDF)
- DOCX (python-docx)
- XLSX (openpyxl)
- Images (pytesseract)

### 5. File Organizer (`src/organizer/`)

**Purpose:** Safely organize files with preview and undo.

**Key Classes:**

```python
class FileOrganizer:
    """Orchestrate file organization"""
    - plan_organization(files) -> OrganizationPlan
    - preview_changes() -> Preview
    - apply_changes()
    - undo_last_operation()

class OrganizationPlan:
    """Proposed file movements"""
    - source_path: str
    - destination_path: str
    - reason: str
    - confidence: float

class UndoManager:
    """Manage undo/redo operations"""
    - record_operation(operation)
    - undo_last()
    - redo_last()
```

**Workflow:**

1. Analyze files (AI classification)
2. Plan organization (determine moves)
3. Generate preview (show what will happen)
4. Apply changes (move files safely)
5. Record history (enable undo)

### 6. Folder Watcher (`src/watcher/`)

**Purpose:** Real-time monitoring and automatic organization.

**Key Classes:**

```python
class FolderWatcher:
    """Monitor folders for changes"""
    - start_watching(folders)
    - stop_watching()
    - on_file_created(event)
    - on_file_modified(event)

class WatcherEvent:
    """File system event"""
    - event_type: str  # created, modified, deleted
    - file_path: str
    - timestamp: datetime
    - action: Callable  # organize, classify, etc.
```

**How it works:**

1. Uses Watchdog library for OS-level monitoring
2. Detects file system changes
3. Triggers AI classification
4. Suggests organization
5. Optional: auto-organize

### 7. Search Engine (`src/search/`)

**Purpose:** Fast, intelligent file discovery.

**Key Classes:**

```python
class SemanticSearch:
    """FAISS-based semantic search"""
    - index_files(embeddings)
    - search(query, top_k=10)
    - update_index()

class FullTextSearch:
    """SQLite full-text search"""
    - search(keyword)
    - apply_filters(filters)
    - combine_results(semantic, fulltext)
```

**Search Methods:**

1. **Semantic:** Find by meaning (FAISS)
2. **Keyword:** Traditional full-text search
3. **Metadata:** Filter by date, size, type
4. **Content:** Search within files

---

## Data Flow

### File Scanning Flow

```
User Input (folder path)
         ↓
   [Scanner]
         ↓
  ├─ Recursive traversal
  ├─ Extract metadata
  ├─ Calculate hash
  └─ Detect file type
         ↓
 [Document Reader]
         ↓
  ├─ Extract text/content
  ├─ Generate summaries
  └─ Get additional metadata
         ↓
 [Database Layer]
         ↓
  └─ Store all information
         ↓
 [Vector Embeddings]
         ↓
  ├─ Generate embeddings
  ├─ Build FAISS index
  └─ Enable semantic search
         ↓
 Scan Complete ✓
```

### Classification & Organization Flow

```
Scanned Files (in DB)
         ↓
 [AI Classifier]
         ↓
  ├─ Connect to Ollama
  ├─ Send file info
  ├─ Receive category
  └─ Cache result
         ↓
 [Organizer]
         ↓
  ├─ Plan folder structure
  ├─ Determine destinations
  └─ Calculate confidence
         ↓
 [Preview Generator]
         ↓
  ├─ Show proposed changes
  ├─ List file movements
  └─ Estimate impact
         ↓
 User Review/Approval
         ↓
 [File Organizer]
         ↓
  ├─ Create destination folders
  ├─ Move files safely
  ├─ Handle errors
  └─ Record operations
         ↓
 [History Manager]
         ↓
  ├─ Store operation log
  ├─ Enable undo
  └─ Audit trail
         ↓
 Organization Complete ✓
```

### Search Flow

```
User Query
         ↓
   [Query Parser]
         ↓
  ├─ Parse natural language
  ├─ Extract intent
  └─ Build search terms
         ↓
   ┌─────────────────────┬─────────────────────┐
   ↓                     ↓                     ↓
[Semantic Search]  [Full-Text Search]  [Metadata Filter]
   ↓                     ↓                     ↓
[FAISS Index]      [SQLite FTS]        [Date/Size/Type]
   ↓                     ↓                     ↓
   └─────────────────────┴─────────────────────┘
         ↓
 [Result Ranking]
         ↓
  ├─ Score each result
  ├─ Combine methods
  └─ Return top matches
         ↓
 Search Results ✓
```

---

## Technology Stack

### Core Technologies

| Layer        | Technology   | Purpose             |
| ------------ | ------------ | ------------------- |
| **Language** | Python 3.13+ | Core implementation |
| **Database** | SQLite       | Metadata storage    |
| **AI**       | Ollama       | Local LLM inference |
| **Search**   | FAISS        | Semantic search     |
| **GUI**      | PySide6      | Desktop application |
| **Web**      | FastAPI      | REST API            |
| **Testing**  | pytest       | Unit tests          |

### Key Libraries

```python
# File Operations
watchdog         # File system monitoring
filetype         # File type detection
python-magic     # Content-based detection

# Document Processing
PyMuPDF         # PDF extraction
python-docx     # Word document parsing
openpyxl        # Excel spreadsheet reading
pytesseract     # OCR for images

# Data & Search
FAISS           # Vector similarity search
SQLAlchemy      # ORM (if used)

# AI Integration
requests        # HTTP to Ollama
json            # Data serialization

# User Interface
PySide6         # Qt for Python GUI
FastAPI         # Web framework

# Development
pytest          # Unit testing
black           # Code formatting
flake8          # Linting
```

---

## Database Schema

### Core Tables

```sql
-- Files metadata
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    extension TEXT,
    file_type TEXT,
    size INTEGER,
    hash TEXT UNIQUE,
    created_date DATETIME,
    modified_date DATETIME,
    content_preview TEXT,
    is_duplicate BOOLEAN,
    scanned_at DATETIME,
    UNIQUE(hash)
);

-- AI Classifications
CREATE TABLE classifications (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    category TEXT,
    confidence FLOAT,
    suggested_folder TEXT,
    classification_date DATETIME,
    model_used TEXT,
    FOREIGN KEY(file_id) REFERENCES files(id)
);

-- Organization Operations
CREATE TABLE organizations (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    source_path TEXT,
    destination_path TEXT,
    operation_type TEXT,  -- move, copy, delete
    status TEXT,  -- pending, completed, failed
    operation_date DATETIME,
    can_undo BOOLEAN,
    FOREIGN KEY(file_id) REFERENCES files(id)
);

-- Vector Embeddings
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    embedding BLOB,  -- Vector from FAISS
    embedding_model TEXT,
    created_at DATETIME,
    FOREIGN KEY(file_id) REFERENCES files(id)
);

-- Configuration
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT,
    type TEXT,  -- string, int, float, json
    updated_at DATETIME
);
```

---

## Design Patterns

### 1. **Factory Pattern**

```python
class DocumentReaderFactory:
    """Create appropriate reader for file type"""

    @staticmethod
    def create_reader(file_path: str) -> DocumentReader:
        if file_path.endswith('.pdf'):
            return PDFReader()
        elif file_path.endswith('.docx'):
            return DocxReader()
        # ... more types
```

### 2. **Strategy Pattern**

```python
class SearchStrategy:
    """Base search strategy"""
    def search(self, query: str) -> List[File]:
        pass

class SemanticSearchStrategy(SearchStrategy):
    """Semantic search implementation"""
    def search(self, query: str) -> List[File]:
        # FAISS implementation

class FullTextSearchStrategy(SearchStrategy):
    """Full-text search implementation"""
    def search(self, query: str) -> List[File]:
        # SQLite FTS implementation
```

### 3. **Observer Pattern**

```python
class FileWatcher:
    """Observable file changes"""

    def __init__(self):
        self.observers = []

    def attach(self, observer: Callable):
        self.observers.append(observer)

    def notify(self, event):
        for observer in self.observers:
            observer(event)
```

### 4. **Command Pattern**

```python
class Command:
    """Base command for organization"""
    def execute(self):
        pass
    def undo(self):
        pass

class MoveFileCommand(Command):
    def __init__(self, source: str, destination: str):
        self.source = source
        self.destination = destination

    def execute(self):
        # Move file
        pass

    def undo(self):
        # Undo move
        pass
```

---

## Performance Considerations

### Optimization Strategies

1. **Scanning**
   - Batch processing in chunks
   - Configurable recursion depth
   - Skip large files optionally
   - Hash incrementally

2. **AI Integration**
   - Cache classifications
   - Batch inference when possible
   - Use smaller models for speed
   - Async processing

3. **Search**
   - FAISS index for O(1) semantic search
   - SQLite full-text indexing
   - Query result caching
   - Pagination for large results

4. **Storage**
   - Database indexing on frequently queried columns
   - Cleanup old data periodically
   - Efficient blob storage for embeddings
   - Archive old operations

### Scalability Limits

| Aspect       | Limit     | Notes                                    |
| ------------ | --------- | ---------------------------------------- |
| Files        | 10M+      | SQLite handles millions efficiently      |
| Folder Depth | 20+       | Configurable, prevents runaway recursion |
| File Size    | 10GB+     | Scanning speed affected                  |
| Query Speed  | <100ms    | With proper indexing                     |
| Memory       | 500MB-2GB | Depends on model and dataset             |

---

## Extension Points

The architecture supports extensions at:

1. **Document Readers** — Add new file format support
2. **AI Models** — Switch Ollama models anytime
3. **Search Strategies** — Implement custom search
4. **Organization Rules** — Custom folder organization
5. **UI Themes** — Customize appearance
6. **Export Formats** — New output formats

---

<div align="center">

**Ready to dive deeper?**

[API Reference →](./api-reference.md) •
[Configuration →](./configuration.md) •
[Back to README ↑](../README.md)

</div>
