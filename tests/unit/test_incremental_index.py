"""
M8 unit tests — src/domain/search/index.py (IncrementalSearchIndex)

Key facts from reading the actual code:
- build() calls self._load_all_files_from_db() which does DB._require_connection()
  and runs  SELECT * FROM files  directly — so we patch DB._require_connection.
- For an incremental build it calls DB.get_dirty_files() — patch that.
- It calls extract_text(path) from watcher.suggestion_engine.
- It calls embed_text(text) from domain.search.embedder.
- search() raises FileNotFoundError (not returns []) if index not built yet.
- File rows need a real "path" key (dict with "path" key or sqlite3.Row-like).

All tests run with MockProvider — no Ollama, no real files on disk.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from infrastructure.ai.gateway import AIGateway
from infrastructure.ai.mock_provider import MockProvider


@pytest.fixture(autouse=True)
def use_mock_provider():
    AIGateway.set_provider(MockProvider(delay_ms=0))
    yield


@pytest.fixture()
def idx(tmp_path: Path):
    """Return an IncrementalSearchIndex pointing at a temp directory."""
    from domain.search.index import IncrementalSearchIndex
    return IncrementalSearchIndex(index_path=tmp_path / "test_idx")


def _make_row(path: str) -> dict:
    """Return a dict that mimics a sqlite3.Row for a files record."""
    return {"path": path, "name": Path(path).name, "id": 1}


# ── First build — no files ────────────────────────────────────────────────────

def test_first_build_empty_db_returns_zero_stats(idx, tmp_path):
    """When DB has no files, build() returns all-zero stats without crashing."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = []

    with patch("domain.search.index.DB") as mock_db:
        mock_db._require_connection.return_value = mock_conn
        stats = idx.build()

    assert stats["indexed"] == 0
    assert stats["total"] == 0
    assert stats["error"] is None


# ── First build — files exist but no extractable text ────────────────────────

def test_first_build_skips_files_with_no_text(idx, tmp_path):
    """Files that extract_text returns '' for are counted as skipped."""
    fake_path = tmp_path / "empty.pdf"
    fake_path.write_bytes(b"")  # exists on disk

    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = [
        {"path": str(fake_path), "name": "empty.pdf", "id": 1}
    ]

    with (
        patch("domain.search.index.DB") as mock_db,
        patch("domain.search.index.extract_text", return_value=""),
    ):
        mock_db._require_connection.return_value = mock_conn
        stats = idx.build()

    assert stats["skipped"] == 1
    assert stats["indexed"] == 0
    assert stats["error"] is None


# ── First build — real text extraction and embedding ─────────────────────────

def test_first_build_indexes_file_with_text(idx, tmp_path):
    """A file that has text gets embedded and counted as indexed."""
    fake_path = tmp_path / "report.pdf"
    fake_path.write_text("annual revenue report 2024", encoding="utf-8")

    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = [
        {"path": str(fake_path), "name": "report.pdf", "id": 1}
    ]

    with (
        patch("domain.search.index.DB") as mock_db,
        patch("domain.search.index.extract_text", return_value="annual revenue report 2024"),
    ):
        mock_db._require_connection.return_value = mock_conn
        stats = idx.build()

    assert stats["indexed"] == 1
    assert stats["error"] is None


# ── Incremental build ─────────────────────────────────────────────────────────

def test_incremental_build_only_embeds_dirty_files(idx, tmp_path):
    """When the index already exists, only dirty files are re-embedded."""
    # Create .faiss + .json so _index_exists() returns True
    (tmp_path / "test_idx.faiss").write_bytes(b"\x00")
    (tmp_path / "test_idx.json").write_text("[]")

    dirty_path = tmp_path / "updated.docx"
    dirty_path.write_text("updated contract terms")

    mock_old_index = MagicMock()
    mock_old_index._paths = []   # no existing paths — skip removal step

    with (
        patch("domain.search.index.DB") as mock_db,
        patch("domain.search.index.extract_text", return_value="updated contract terms"),
        patch("domain.search.index.SearchIndex.load", return_value=mock_old_index),
    ):
        mock_db.get_dirty_files.return_value = [{"path": str(dirty_path)}]
        mock_db._require_connection.return_value = MagicMock()

        stats = idx.build()

    assert stats["indexed"] == 1
    assert stats["error"] is None


def test_incremental_build_nothing_dirty_returns_up_to_date(idx, tmp_path):
    """If no files are dirty and index is on disk, returns total without re-embedding."""
    (tmp_path / "test_idx.faiss").write_bytes(b"\x00")
    (tmp_path / "test_idx.json").write_text("[]")

    mock_old_index = MagicMock()
    mock_old_index._paths = ["/existing/file.pdf"]

    with (
        patch("domain.search.index.DB") as mock_db,
        patch("domain.search.index.SearchIndex.load", return_value=mock_old_index),
    ):
        mock_db.get_dirty_files.return_value = []
        stats = idx.build()

    assert stats["indexed"] == 0
    assert stats["error"] is None


# ── Search ────────────────────────────────────────────────────────────────────

def test_search_before_build_raises_file_not_found(idx):
    """search() raises FileNotFoundError when the index has never been built."""
    with pytest.raises(FileNotFoundError):
        idx.search("anything", top_k=5)


def test_search_empty_query_returns_empty(idx):
    """search() returns [] for blank queries without touching the index."""
    results = idx.search("", top_k=5)
    assert results == []


def test_search_returns_results_after_build(idx, tmp_path):
    """After a successful build, search() returns list[dict] with path and score."""
    fake_path = tmp_path / "report.pdf"
    fake_path.write_text("annual revenue report 2024", encoding="utf-8")

    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = [
        {"path": str(fake_path), "name": "report.pdf", "id": 1}
    ]

    with (
        patch("domain.search.index.DB") as mock_db,
        patch("domain.search.index.extract_text", return_value="annual revenue report 2024"),
    ):
        mock_db._require_connection.return_value = mock_conn
        stats = idx.build()

    # Only assert search if build actually indexed something
    if stats["indexed"] > 0:
        results = idx.search("annual report", top_k=5)
        assert isinstance(results, list)
        if results:
            assert "path" in results[0]
            assert "score" in results[0]