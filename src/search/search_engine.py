"""
DesktopAI
Search Engine

Ties the embedder and the FAISS index together into two simple
operations: build the semantic search index from already-scanned
files, and search it with a plain-language query.

Building the index does NOT scan your folders itself — it reads
whatever files are already stored in the database (see
scanner.FileScanner + database.DatabaseManager, or just run
src/app.py first). This keeps "finding files" and "understanding
files" as separate, independently-testable steps, matching the
rest of DesktopAI's architecture.
"""

from dataclasses import dataclass
from pathlib import Path

from core import config
from core.logger import get_logger
from database.database import DatabaseManager
from scanner.file_info import FileInfo
from search.embedder import get_embedding
from search.index_manager import SearchIndex
from watcher.suggestion_engine import extract_text

logger = get_logger("search")


@dataclass
class SearchResult:
    """One semantic search match."""

    path: Path
    score: float


def build_search_index(
    files: list[FileInfo] | None = None,
    db_path: Path = config.DATABASE_PATH,
    index_path: Path = config.SEARCH_INDEX_PATH,
) -> int:
    """
    Build (or rebuild) the semantic search index: read each file's
    text, embed it, and save the resulting index to disk.

    Args:
        files (list[FileInfo] | None):
            Files to index. Defaults to every file already stored
            in the database (i.e. whatever src/app.py has scanned
            so far).
        db_path (Path):
            Where to load files from, if `files` isn't given.
        index_path (Path):
            Where to save the resulting index (see
            SearchIndex.save for the exact filenames).

    Returns:
        int:
            How many files were successfully indexed. Files with no
            extractable text, or where the AI is unavailable, are
            skipped (not an error).
    """
    if files is None:
        db = DatabaseManager(db_path)
        db.connect()
        files = db.load_files()
        db.close()

    if not files:
        logger.info("No files to index.")
        return 0

    index: SearchIndex | None = None
    indexed_count = 0

    for file_info in files:
        text = extract_text(file_info.path)
        truncated_text = text[: config.EMBEDDING_MAX_TEXT_LENGTH]

        vector = get_embedding(truncated_text)
        if vector is None:
            logger.info("Skipping %s (no text or AI unavailable).", file_info.path)
            continue

        if index is None:
            index = SearchIndex(dimension=len(vector))

        index.add(str(file_info.path), vector)
        indexed_count += 1

    if index is None:
        logger.info("Nothing was indexed (no file had usable text).")
        return 0

    index.save(index_path)
    logger.info("Search index built: %d file(s) indexed.", indexed_count)

    return indexed_count


def semantic_search(
    query: str,
    top_k: int = config.SEARCH_TOP_K,
    index_path: Path = config.SEARCH_INDEX_PATH,
) -> list[SearchResult]:
    """
    Search previously-indexed files using a plain-language query.

    Args:
        query (str):
            What to search for, e.g. "tax documents from last year".
        top_k (int):
            Maximum number of results to return.
        index_path (Path):
            Where the index was saved by build_search_index().

    Returns:
        list[SearchResult]:
            Best matches first. Empty if the query is empty, the
            index hasn't been built yet, or the AI is unavailable.
    """
    if not query or not query.strip():
        logger.info("Empty search query; skipping.")
        return []

    try:
        index = SearchIndex.load(index_path)
    except FileNotFoundError:
        logger.warning("No search index found at %s. Build one first.", index_path)
        return []

    vector = get_embedding(query)
    if vector is None:
        logger.warning("Could not embed the search query (AI unavailable).")
        return []

    matches = index.search(vector, top_k)

    return [SearchResult(path=Path(path), score=score) for path, score in matches]