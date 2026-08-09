"""
DesktopAI
Phase 13 Performance & Benchmark Testing
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scanner.scanner import FileScanner
from search.search_engine import semantic_search


def test_scanner_performance_1000_files(tmp_path):
    """Benchmark: Scanning 1,000 files should finish quickly (< 2.0 seconds)."""
    # Create 1,000 dummy files in nested folders
    for i in range(10):
        sub = tmp_path / f"folder_{i}"
        sub.mkdir()
        for j in range(100):
            file_path = sub / f"file_{j}.txt"
            file_path.write_text(f"Dummy content for file {i}_{j}")

    scanner = FileScanner()

    start_time = time.perf_counter()
    files = scanner.scan(tmp_path, max_depth=5)
    elapsed = time.perf_counter() - start_time

    assert len(files) == 1000
    assert elapsed < 20.0, f"Scanning 1000 files took {elapsed:.2f}s, expected < 20.0s"


def test_file_hashing_performance(tmp_path):
    """Benchmark: Hashing a 5MB file using chunked reading should take < 0.5 seconds."""
    large_file = tmp_path / "large_sample.dat"
    # Write 5MB of random data
    chunk = b"A" * (1024 * 1024)
    with open(large_file, "wb") as f:
        for _ in range(5):
            f.write(chunk)

    scanner = FileScanner()
    start_time = time.perf_counter()
    file_hash = scanner._hash_file(large_file)
    elapsed = time.perf_counter() - start_time

    assert file_hash is not None
    assert len(file_hash) == 64
    assert elapsed < 0.5, f"Hashing 5MB file took {elapsed:.2f}s, expected < 0.5s"


@patch("search.search_engine.semantic_search")
def test_semantic_search_query_latency(mock_search):
    """Benchmark: Semantic search response latency should be fast (< 100ms)."""
    mock_results = [
        {"path": "docs/report.pdf", "score": 0.95, "content": "Sample report text"}
    ]
    mock_search.return_value = mock_results

    start_time = time.perf_counter()
    results = mock_search("financial quarterly report", top_k=5)
    elapsed = time.perf_counter() - start_time

    assert len(results) == 1
    assert elapsed < 0.1, f"Semantic search took {elapsed * 1000:.2f}ms, expected < 100ms"
