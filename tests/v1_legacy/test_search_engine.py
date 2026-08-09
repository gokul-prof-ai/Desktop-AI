"""
DesktopAI
Tests for the Search Engine module.
"""

from datetime import datetime

import search.search_engine as search_engine_module
from scanner.file_info import FileInfo
from search.search_engine import build_search_index, semantic_search


def _make_file_info(path):
    """A minimal FileInfo for tests that don't care about hashing/typing."""
    return FileInfo(
        name=path.name,
        path=path,
        extension=path.suffix,
        size=path.stat().st_size,
        created=datetime.now(),
        modified=datetime.now(),
    )


def test_build_search_index_embeds_and_saves(tmp_path, monkeypatch):
    """build_search_index() should extract each file's text, embed
    it, and save an index containing one entry per file that had
    usable text."""
    file_a = tmp_path / "a.txt"
    file_a.write_text("cats and dogs")
    file_b = tmp_path / "b.txt"
    file_b.write_text("tax invoice 2026")

    monkeypatch.setattr(
        search_engine_module, "extract_text", lambda path: path.read_text()
    )
    monkeypatch.setattr(
        search_engine_module,
        "get_embedding",
        lambda text: [1.0, 0.0] if "cats" in text else [0.0, 1.0],
    )

    index_path = tmp_path / "index" / "search_index"
    count = build_search_index(
        files=[_make_file_info(file_a), _make_file_info(file_b)],
        index_path=index_path,
    )

    assert count == 2
    assert index_path.with_suffix(".faiss").exists()
    assert index_path.with_suffix(".json").exists()


def test_build_search_index_skips_files_with_no_usable_text(tmp_path, monkeypatch):
    """A file the AI can't embed (e.g. no text, AI unavailable)
    should be skipped, not counted, and not crash the whole build."""
    file_a = tmp_path / "empty.bin"
    file_a.write_bytes(b"")

    monkeypatch.setattr(search_engine_module, "extract_text", lambda path: "")
    monkeypatch.setattr(search_engine_module, "get_embedding", lambda text: None)

    index_path = tmp_path / "index" / "search_index"
    count = build_search_index(files=[_make_file_info(file_a)], index_path=index_path)

    assert count == 0
    assert not index_path.with_suffix(".faiss").exists()


def test_build_search_index_with_no_files_returns_zero(tmp_path):
    index_path = tmp_path / "index" / "search_index"
    count = build_search_index(files=[], index_path=index_path)
    assert count == 0


def test_semantic_search_returns_best_match(tmp_path, monkeypatch):
    """An end-to-end round trip: build an index, then search it and
    get the most relevant file back first."""
    file_a = tmp_path / "cats.txt"
    file_a.write_text("cats and dogs")
    file_b = tmp_path / "tax.txt"
    file_b.write_text("tax invoice 2026")

    monkeypatch.setattr(
        search_engine_module, "extract_text", lambda path: path.read_text()
    )
    monkeypatch.setattr(
        search_engine_module,
        "get_embedding",
        lambda text: [1.0, 0.0] if "cats" in text else [0.0, 1.0],
    )

    index_path = tmp_path / "index" / "search_index"
    build_search_index(
        files=[_make_file_info(file_a), _make_file_info(file_b)],
        index_path=index_path,
    )

    results = semantic_search("cats", top_k=1, index_path=index_path)

    assert len(results) == 1
    assert results[0].path == file_a


def test_semantic_search_with_no_index_returns_empty_list(tmp_path):
    """Searching before an index has ever been built should return
    an empty list, not raise."""
    index_path = tmp_path / "index" / "search_index"
    results = semantic_search("anything", index_path=index_path)
    assert results == []


def test_semantic_search_with_empty_query_returns_empty_list(tmp_path):
    index_path = tmp_path / "index" / "search_index"
    results = semantic_search("   ", index_path=index_path)
    assert results == []