# DesktopAI API Design

## Purpose

Every module should expose a clear and stable public interface.

---

# Scanner (implemented: src/scanner/scanner.py)

Public API

- FileScanner().scan(folder, max_depth)

Returns:

- A list of FileInfo objects (name, path, extension, size, created,
  modified, file_hash, detected_type)

---

# Organizer (implemented: src/organizer/organizer.py)

Public API

- Organizer().preview(actions)
- Organizer().apply(actions)
- Organizer().undo_last()

---

# Search (planned — not yet implemented)

Public API

- keyword_search()
- semantic_search()

---

# Database (implemented: src/database/database.py)

Public API

- connect()
- save_file()
- load_files()
- delete_file()

---

# AI (implemented: src/ai/classifier.py, summarizer.py, recommender.py)

Public API

- classify_file(text)
- summarize_file(text)
- recommend_action(file_name, category, text)

---

# Memory (planned — not yet implemented)

Public API

- remember()
- recall()
- forget()

---

# Rules

Modules should communicate only through their public API.

Never access another module's internal implementation directly.