# Module Developer Guide

## Overview

Desktop-AI consists of 9 major modules:

## 1. Scanner Module (src/scanner/)

**Purpose:** Recursively scan folders, extract file metadata
**Main Files:**

- scanner.py - FileScanner class
- file_info.py - FileInfo data class

**Key Classes:**

- FileScanner: Main scanning engine
- FileInfo: File metadata container

**Examples:**
\`\`\`python
from src.scanner import FileScanner
scanner = FileScanner()
files = scanner.scan('/home/user/docs', max_depth=3)
for file in files:
print(f"{file.name}: {file.size} bytes, {file.detected_type}")
\`\`\`

**Testing:** See tests/test_scanner.py (8 test cases)

---

## 2. AI Module (src/ai/)

**Purpose:** Classification, summarization, recommendations
**Key Classes:**

- Classifier
- Summarizer
- OllamaClient

**Config:** config/ollama_config.yaml

**Examples:**
[Code examples]

---

## 3. Search Module (src/search/)

**Purpose:** Semantic search using FAISS + embeddings
**Key Classes:**

- SearchEngine
- Embedder

**Performance:** ~200ms for queries on 10K files

---

## 4-9. [Similarly detailed]
