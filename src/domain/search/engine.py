"""
DesktopAI v2.0 — Search Engine
File: src/domain/search/engine.py

The public interface for semantic search in DesktopAI.
All GUI code and services go through this module — they never
import from embedder.py or index.py directly.

Two operations are exposed:

    build_index()  — build or incrementally update the search index
    search()       — find files matching a plain-language query

Both operations are fast enough to run on a QThread worker
(see gui/views/search_view.py _SearchWorker and _IndexWorker).
Neither blocks the GUI thread.

Replaces the old src/search/search_engine.py, which:
    - Called Ollama directly (bypassing AIGateway)
    - Rebuilt the entire index from scratch every time
    - Returned a SearchResult dataclass instead of a dict
      (which didn't match what search_view.py expected)
"""

from __future__ import annotations

from pathlib import Path

from core.constants import DATA_DIR
from core.logger import get_logger
from domain.search.index import IncrementalSearchIndex

logger = get_logger(__name__)

# Default location for the FAISS index files.
# Produces DATA_DIR/search_index.faiss + DATA_DIR/search_index.json
_DEFAULT_INDEX_PATH = DATA_DIR / "search_index"

# Module-level index instance — shared across all callers in the same
# process. The GUI workers call build_index() and search() through
# FileService, which calls these functions.
_index = IncrementalSearchIndex(index_path=_DEFAULT_INDEX_PATH)


def build_index(index_path: Path | None = None) -> dict:
    """
    Build or incrementally update the semantic search index.

    On first call: embeds all files currently in the database.
    On subsequent calls: re-embeds only files flagged as dirty
    (modified since last index build), leaving everything else alone.

    The file watcher marks files dirty automatically. You can also
    trigger a manual rebuild from the SearchView "Rebuild Index" button.

    Args:
        index_path:
            Override the index storage location. Defaults to
            DATA_DIR/search_index. Pass a custom path in tests.

    Returns:
        dict with keys:
            "indexed"  (int)        — new/updated files embedded
            "skipped"  (int)        — files with no text or AI error
            "removed"  (int)        — deleted files removed from index
            "total"    (int)        — total files in index after build
            "error"    (str | None) — error message on failure
    """
    global _index

    if index_path is not None:
        # Create a fresh instance for the custom path (used in tests)
        idx = IncrementalSearchIndex(index_path=index_path)
    else:
        idx = _index

    logger.info("build_index() called")
    stats = idx.build()
    logger.info("build_index() complete: %s", stats)
    return stats


def search(query: str, top_k: int = 20, index_path: Path | None = None) -> list[dict]:
    """
    Search the index with a plain-language query.

    Args:
        query:
            What to search for, e.g. "tax documents from last year".
            Empty or whitespace-only strings return an empty list.
        top_k:
            Maximum number of results to return (default 20).
        index_path:
            Override the index location (used in tests).

    Returns:
        list[dict], each dict has:
            "path"  (str)   — absolute file path
            "score" (float) — cosine similarity, higher = better match

        Sorted best-match first. Empty list if:
            - query is empty
            - the index hasn't been built yet
            - the AI provider is unavailable

    Raises:
        FileNotFoundError:
            If the index has never been built. The caller (FileService
            or SearchView) should catch this and show the "Build Index"
            empty state.
    """
    global _index

    if not query or not query.strip():
        return []

    if index_path is not None:
        idx = IncrementalSearchIndex(index_path=index_path)
    else:
        idx = _index

    logger.debug("search() query=%r top_k=%d", query, top_k)
    results = idx.search(query, top_k=top_k)
    logger.debug("search() returned %d results", len(results))
    return results