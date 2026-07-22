# Scanner Module Design

## Purpose

The scanner module discovers files in a folder and collects basic metadata.

It does not modify files.

---

# Responsibilities

- Scan folders recursively
- Detect files
- Collect metadata
- Skip inaccessible files safely
- Return structured data

---

# Input

A folder path.

Example:

C:\Users\Gokul\Documents

---

# Output

A list of FileInfo objects.

Each FileInfo contains:

- Name
- Full path
- Extension
- Size
- Created date
- Modified date

---

# Out of Scope

The scanner will NOT:

- Read file contents
- Calculate hashes
- Detect duplicates
- Use AI
- Move files
- Delete files

These belong to future modules.