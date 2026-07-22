# DesktopAI Testing Strategy

## Goal

Every important module should have automated tests.

---

# Test Structure

tests/

- test_scanner.py
- test_database.py
- test_search.py
- test_ai.py
- test_memory.py

---

# Scanner Tests

- Empty folder
- Large folder
- Hidden files
- Permission denied
- Invalid path

---

# Database Tests

- Create database
- Insert record
- Update record
- Delete record

---

# AI Tests

- Classification
- Summaries
- Invalid prompts

---

# Search Tests

- Keyword search
- Semantic search
- Empty database

---

# Performance

Large folders should be scanned efficiently.

Memory usage should remain stable.

---

# Test Framework

- pytest

Future:

- GitHub Actions
- Continuous Integration