# Scanner Module Design

## Purpose

The scanner module discovers files in a folder and collects basic metadata.

It reads file content only when needed to calculate hashes and detect file type. It does not modify files.

---

## Responsibilities

- Scan folders recursively
- Respect a maximum scan depth
- Detect regular files
- Collect metadata
- Calculate SHA-256 file hashes
- Detect file type from content when possible
- Skip hidden files and inaccessible paths safely
- Return structured data

---

## Input

A folder path.

Example:

```text
C:\Users\Gokul\Documents
```

---

## Output

A list of `FileInfo` objects.

Each `FileInfo` contains:

- Name
- Full path
- Extension
- Size
- Created date
- Modified date
- SHA-256 hash, when readable
- Detected MIME type, when available

---

## Safety Boundaries

The scanner will NOT:

- Detect duplicates
- Use AI
- Move files
- Delete files

These belong to future modules.
