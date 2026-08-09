"""
DesktopAI
Tests for the Search Index Manager module.
"""

import pytest

from search.index_manager import SearchIndex


def test_new_index_is_empty():
    index = SearchIndex(dimension=3)
    assert len(index) == 0


def test_add_increases_length():
    index = SearchIndex(dimension=3)
    index.add("file1.txt", [1.0, 0.0, 0.0])
    index.add("file2.txt", [0.0, 1.0, 0.0])
    assert len(index) == 2


def test_search_returns_closest_match_first():
    """A query vector should match the file with the most similar
    (highest cosine similarity) embedding, ranked first."""
    index = SearchIndex(dimension=3)
    index.add("cat.txt", [1.0, 0.0, 0.0])
    index.add("dog.txt", [0.0, 1.0, 0.0])
    index.add("cat_photo.txt", [0.9, 0.1, 0.0])

    results = index.search([1.0, 0.0, 0.0], top_k=2)

    assert len(results) == 2
    assert results[0][0] == "cat.txt"
    assert results[1][0] == "cat_photo.txt"


def test_search_on_empty_index_returns_empty_list():
    index = SearchIndex(dimension=3)
    results = index.search([1.0, 0.0, 0.0], top_k=5)
    assert results == []


def test_search_top_k_larger_than_index_does_not_error():
    index = SearchIndex(dimension=3)
    index.add("only_file.txt", [1.0, 0.0, 0.0])

    results = index.search([1.0, 0.0, 0.0], top_k=10)

    assert len(results) == 1


def test_save_and_load_roundtrip(tmp_path):
    index = SearchIndex(dimension=3)
    index.add("file1.txt", [1.0, 0.0, 0.0])
    index.add("file2.txt", [0.0, 1.0, 0.0])

    base_path = tmp_path / "my_index"
    index.save(base_path)

    assert base_path.with_suffix(".faiss").exists()
    assert base_path.with_suffix(".json").exists()

    loaded = SearchIndex.load(base_path)

    assert len(loaded) == 2
    results = loaded.search([1.0, 0.0, 0.0], top_k=1)
    assert results[0][0] == "file1.txt"


def test_load_missing_index_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        SearchIndex.load(tmp_path / "does_not_exist")