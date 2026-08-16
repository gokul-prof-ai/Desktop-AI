"""
M8 unit tests — src/infrastructure/storage/migrations/002_embeddings.sql

Tests that:
  1. The embeddings table is created when the DB connects.
  2. mark_file_dirty() sets is_dirty = 1 for the given file path.
  3. get_dirty_files() returns only rows where is_dirty = 1.
  4. Deleting a file row cascades to the embeddings row.

Uses a real SQLite in-memory DB (no mocks) — this is a true integration
test of the migration SQL and the Python helper methods on DatabaseManager.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.storage.database import DatabaseManager


@pytest.fixture()
def db(tmp_path: Path):
    """Return a connected DatabaseManager using a temp .db file."""
    manager = DatabaseManager(db_path=tmp_path / "test_m8.db")
    manager.connect()
    yield manager
    manager.close()


def _insert_file(db: DatabaseManager, path: str) -> int:
    """Insert a minimal file row and return its id.
    Column names from migration 001: filename, size_bytes, modified_at, md5_hash.
    """
    conn = db._conn
    conn.execute(
        """
        INSERT INTO files (path, filename, extension, size_bytes, modified_at, md5_hash)
        VALUES (?, ?, ?, ?, datetime('now'), 'abc123deadbeef')
        """,
        (path, Path(path).name, Path(path).suffix or ".txt", 1024),
    )
    conn.commit()
    row = conn.execute("SELECT id FROM files WHERE path = ?", (path,)).fetchone()
    return row["id"]


def _insert_embedding(db: DatabaseManager, file_id: int, is_dirty: int = 0) -> None:
    """Insert an embeddings row for the given file_id.
    Real columns from migration 002: file_id, model, vector_dim, indexed_at, is_dirty.
    """
    db._conn.execute(
        """
        INSERT INTO embeddings (file_id, model, vector_dim, is_dirty, indexed_at)
        VALUES (?, 'mock', 384, ?, datetime('now'))
        """,
        (file_id, is_dirty),
    )
    db._conn.commit()


# ── Table creation ────────────────────────────────────────────────────────────

def test_embeddings_table_exists(db: DatabaseManager):
    row = db._conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings'"
    ).fetchone()
    assert row is not None, "embeddings table was not created by migration 002"


def test_embeddings_table_has_required_columns(db: DatabaseManager):
    cols = [r[1] for r in db._conn.execute("PRAGMA table_info(embeddings)").fetchall()]
    for required in ("id", "file_id", "is_dirty"):
        assert required in cols, f"Column '{required}' missing from embeddings table"


# ── mark_file_dirty() ─────────────────────────────────────────────────────────

def test_mark_file_dirty_sets_flag(db: DatabaseManager):
    path = "/home/user/docs/invoice.pdf"
    file_id = _insert_file(db, path)
    _insert_embedding(db, file_id, is_dirty=0)

    db.mark_file_dirty(path)

    row = db._conn.execute(
        "SELECT is_dirty FROM embeddings WHERE file_id = ?", (file_id,)
    ).fetchone()
    assert row is not None
    assert row["is_dirty"] == 1


def test_mark_file_dirty_nonexistent_path_is_noop(db: DatabaseManager):
    """mark_file_dirty on an unknown path must not raise."""
    db.mark_file_dirty("/does/not/exist.txt")   # should not raise


# ── get_dirty_files() ─────────────────────────────────────────────────────────

def test_get_dirty_files_returns_only_dirty(db: DatabaseManager):
    clean_path = "/docs/clean.pdf"
    dirty_path = "/docs/dirty.pdf"

    clean_id = _insert_file(db, clean_path)
    dirty_id  = _insert_file(db, dirty_path)
    _insert_embedding(db, clean_id, is_dirty=0)
    _insert_embedding(db, dirty_id,  is_dirty=1)

    dirty = db.get_dirty_files()
    paths = [r["path"] for r in dirty]

    assert dirty_path in paths
    assert clean_path not in paths


def test_get_dirty_files_empty_when_none_dirty(db: DatabaseManager):
    file_id = _insert_file(db, "/docs/all_good.pdf")
    _insert_embedding(db, file_id, is_dirty=0)

    assert db.get_dirty_files() == []


def test_get_dirty_files_empty_when_no_embeddings(db: DatabaseManager):
    """Files with no embeddings row should not appear in get_dirty_files."""
    _insert_file(db, "/docs/never_indexed.pdf")
    assert db.get_dirty_files() == []


# ── Cascade delete ────────────────────────────────────────────────────────────

def test_deleting_file_row_cascades_to_embeddings(db: DatabaseManager):
    path = "/docs/to_delete.pdf"
    file_id = _insert_file(db, path)
    _insert_embedding(db, file_id)

    db._conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
    db._conn.commit()

    row = db._conn.execute(
        "SELECT * FROM embeddings WHERE file_id = ?", (file_id,)
    ).fetchone()
    assert row is None, "CASCADE DELETE did not remove the embedding row"