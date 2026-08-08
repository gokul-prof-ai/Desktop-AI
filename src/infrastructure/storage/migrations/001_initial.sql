-- DesktopAI v2.0 — Initial Schema
-- Migration: 001_initial
-- Applied by: DatabaseManager.migrate()
--
-- This file defines the complete V2 database schema.
-- Never edit this file after it has been applied to a database.
-- For schema changes, create 002_next_change.sql instead.

-- ── Schema version tracking ────────────────────────────────────────────────
-- Every migration inserts one row here.
-- DatabaseManager checks this table to know which migrations to apply.
CREATE TABLE IF NOT EXISTS schema_versions (
    version     INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    applied_at  TEXT    NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- ── Files ──────────────────────────────────────────────────────────────────
-- One row per file that DesktopAI has ever scanned.
-- path is the absolute path at the time of scanning.
CREATE TABLE IF NOT EXISTS files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    path            TEXT    NOT NULL UNIQUE,
    filename        TEXT    NOT NULL,
    extension       TEXT    NOT NULL DEFAULT '',
    size_bytes      INTEGER NOT NULL DEFAULT 0,
    modified_at     TEXT,               -- ISO-8601 from filesystem
    md5_hash        TEXT,               -- for change detection
    category        TEXT,               -- assigned by classifier
    confidence      REAL,               -- 0.0 to 1.0
    summary         TEXT,               -- AI-generated summary
    text_content    TEXT,               -- extracted text for search
    embedding_id    INTEGER,            -- foreign key into embeddings table
    scanned_at      TEXT    NOT NULL DEFAULT (datetime('now', 'utc')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_files_path      ON files(path);
CREATE INDEX IF NOT EXISTS idx_files_extension ON files(extension);
CREATE INDEX IF NOT EXISTS idx_files_category  ON files(category);

-- ── History (audit trail) ──────────────────────────────────────────────────
-- Every file operation DesktopAI performs is recorded here.
-- This is the table V1 defined but never wrote to.
-- V2 writes an entry for every move, rename, copy, and undo.
CREATE TABLE IF NOT EXISTS history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type     TEXT    NOT NULL,   -- 'move', 'rename', 'copy', 'undo', 'skip'
    source_path     TEXT    NOT NULL,
    target_path     TEXT,               -- NULL for 'skip' actions
    category        TEXT,
    confidence      REAL,
    model           TEXT,               -- which AI model made the decision
    status          TEXT    NOT NULL DEFAULT 'completed',  -- 'completed', 'failed', 'undone'
    error_message   TEXT,               -- populated if status = 'failed'
    batch_id        TEXT,               -- groups operations from same session
    performed_at    TEXT    NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_history_source_path  ON history(source_path);
CREATE INDEX IF NOT EXISTS idx_history_batch_id     ON history(batch_id);
CREATE INDEX IF NOT EXISTS idx_history_performed_at ON history(performed_at);
CREATE INDEX IF NOT EXISTS idx_history_status       ON history(status);

-- ── Embeddings ─────────────────────────────────────────────────────────────
-- Stores which files have been embedded and when.
-- The actual vectors live in the FAISS index file on disk.
-- This table tracks which files are in the index so we know what's stale.
CREATE TABLE IF NOT EXISTS embeddings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id         INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    model           TEXT    NOT NULL,
    vector_dim      INTEGER NOT NULL,
    indexed_at      TEXT    NOT NULL DEFAULT (datetime('now', 'utc')),
    is_dirty        INTEGER NOT NULL DEFAULT 0  -- 1 = file changed, re-embed needed
);

CREATE INDEX IF NOT EXISTS idx_embeddings_file_id  ON embeddings(file_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_is_dirty ON embeddings(is_dirty);

-- ── User preferences (memory) ──────────────────────────────────────────────
-- Stores learned user preferences that guide future organization decisions.
-- Example: user always moves "invoice_*.pdf" to /Documents/Finance/
-- The organizer consults this table before asking the AI.
CREATE TABLE IF NOT EXISTS preferences (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pref_type       TEXT    NOT NULL,   -- 'folder_preference', 'category_override', 'skip_pattern'
    pattern         TEXT    NOT NULL,   -- filename pattern or extension
    value           TEXT    NOT NULL,   -- preferred folder path or category name
    confidence      REAL    NOT NULL DEFAULT 1.0,
    use_count       INTEGER NOT NULL DEFAULT 1,
    last_used_at    TEXT    NOT NULL DEFAULT (datetime('now', 'utc')),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_preferences_pref_type ON preferences(pref_type);
CREATE INDEX IF NOT EXISTS idx_preferences_pattern   ON preferences(pattern);

-- ── Sessions ───────────────────────────────────────────────────────────────
-- Tracks each scan/organize session for grouping history entries.
CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT    PRIMARY KEY,  -- UUID
    folder_path     TEXT    NOT NULL,
    file_count      INTEGER NOT NULL DEFAULT 0,
    action_count    INTEGER NOT NULL DEFAULT 0,
    status          TEXT    NOT NULL DEFAULT 'running',  -- 'running', 'completed', 'cancelled'
    started_at      TEXT    NOT NULL DEFAULT (datetime('now', 'utc')),
    completed_at    TEXT
);

-- ── Mark this migration as applied ────────────────────────────────────────
INSERT OR IGNORE INTO schema_versions (version, name)
VALUES (1, '001_initial');