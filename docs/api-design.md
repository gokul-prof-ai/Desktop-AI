# DesktopAI API Design

## Purpose

Every module should expose a clear and stable public interface.

---

# Scanner

Public API

- scan_folder()
- scan_file()

Returns:

- File metadata
- File hash
- File type

---

# Organizer

Public API

- preview_changes()
- organize()
- undo()

---

# Search

Public API

- keyword_search()
- semantic_search()

---

# Database

Public API

- connect()
- save_file()
- load_files()
- delete_file()

---

# AI

Public API

- classify_file()
- summarize_document()
- suggest_folder()

---

# Memory

Public API

- remember()
- recall()
- forget()

---

# Rules

Modules should communicate only through their public API.

Never access another module's internal implementation directly.