# DesktopAI Coding Standards

## Purpose

This document defines the coding standards followed throughout the DesktopAI project.

---

# General Principles

- Write readable code before clever code.
- Keep functions focused on a single responsibility.
- Prefer composition over inheritance.
- Avoid duplicated logic.
- Design modules to be reusable.

---

# Naming Conventions

## Variables

Use descriptive snake_case names.

Example:

```python
file_path
scan_results
folder_name
```

Avoid:

```python
x
tmp
abc
```

---

## Functions

Functions should use verbs.

Examples:

- scan_folder()
- calculate_hash()
- read_pdf()
- organize_files()

---

## Classes

Use PascalCase.

Examples:

- FileScanner
- DatabaseManager
- AIPlanner

---

## Constants

Use uppercase.

Example:

```python
MAX_FILE_SIZE
DEFAULT_SCAN_DEPTH
```

---

# Function Design

Each function should:

- Perform one task
- Return predictable values
- Raise meaningful exceptions
- Include type hints
- Include a docstring

Example:

```python
def scan_folder(path: str) -> list:
    """Scan a folder and return discovered files."""
```

---

# Comments

Write comments only when they explain *why*, not *what*.

Good:

```python
# Skip hidden files to improve scan performance.
```

Bad:

```python
# Increment i
i += 1
```

---

# Error Handling

Never silently ignore exceptions.

Instead:

- Log the error
- Explain the cause
- Continue safely when possible

---

# Imports

Standard Library

↓

Third-party packages

↓

Local modules

---

# Code Formatting

- Black formatter
- 4-space indentation
- UTF-8 encoding
- Maximum line length: 88 characters

---

# Version Control

Commit only completed work.

Commit messages should be meaningful.

Examples:

- Add file scanner module
- Implement SQLite database
- Improve search engine performance