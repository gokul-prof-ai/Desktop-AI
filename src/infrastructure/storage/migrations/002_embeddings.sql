-- DesktopAI v2.0 — Migration 002: Embeddings table
-- File: src/infrastructure/storage/migrations/002_embeddings.sql
--
-- Creates the embeddings table that tracks which files have been
-- embedded into the FAISS index, and whether each embedding is
-- still current (is_dirty = 0) or needs to be re-generated
-- (is_dirty = 1) because the file has changed since it was indexed.
--
-- database.py already references this table in:
--   - mark_file_dirty()   → UPDATE embeddings SET is_dirty = 1
--   - get_dirty_files()   → SELECT ... JOIN embeddings WHERE is_dirty = 1
--
-- The watcher calls mark_file_dirty() whenever a file is modified.
-- IncrementalSearchIndex calls get_dirty_files() at index-build
-- time to know which files need re-embedding.

CREATE TABLE IF NOT EXISTS embeddings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Which file this embedding belongs to.
    -- ON DELETE CASCADE: if the file row is removed, the embedding
    -- row is automatically cleaned up too.
    file_id      INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,

    -- Which model produced this embedding (e.g. "nomic-embed-text").
    -- Stored so we can detect when the embedding model changes and
    -- force a full re-index.
    model        TEXT    NOT NULL,

    -- The number of dimensions in the vector. Stored for sanity-
    -- checking: if the dimension changes (model swap), all embeddings
    -- must be rebuilt.
    dimension    INTEGER NOT NULL,

    -- 0 = current, 1 = stale (file modified since last embed).
    -- The watcher sets this to 1 when it sees a file change.
    -- IncrementalSearchIndex resets it to 0 after re-embedding.
    is_dirty     INTEGER NOT NULL DEFAULT 0,

    -- When this embedding was last generated.
    embedded_at  TEXT    NOT NULL DEFAULT (datetime('now', 'utc')),

    -- Each file can only have one embedding row at a time.
    UNIQUE(file_id)
);

-- Speed up the most common query: "which embeddings are dirty?"
CREATE INDEX IF NOT EXISTS idx_embeddings_dirty
    ON embeddings(is_dirty)
    WHERE is_dirty = 1;

-- Record that this migration has been applied.
INSERT OR IGNORE INTO schema_versions (version, name)
VALUES (2, '002_embeddings');