"""
DesktopAI v2.0 — Incremental Search Index
File: src/domain/search/index.py

Wraps the low-level SearchIndex (FAISS) with incremental update logic:
instead of rebuilding the entire index from scratch on every call, this
class only re-embeds files that have changed since the last build.

How it works:
    1. The database tracks every indexed file in the `embeddings` table.
    2. When the file watcher detects a change, it calls
       DB.mark_file_dirty(path) → sets embeddings.is_dirty = 1.
    3. When build() is called, IncrementalSearchIndex asks the database
       for all dirty files (DB.get_dirty_files()), re-embeds only those,
       and merges them into the saved index.
    4. Deleted files are removed from the path list before saving.

For the first-ever build (no index on disk yet), ALL files are treated
as dirty and the full index is built from scratch. This is identical in
behavior to the old build_search_index() function, just with tracking
added from that point forward.

This module does NOT touch the SearchIndex class in index_manager.py.
That class handles the FAISS mechanics and is imported here.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from core.exceptions import AIGatewayError
from core.logger import get_logger
from domain.search.embedder import embed_text
from infrastructure.storage.database import DB
from search.index_manager import SearchIndex
from watcher.suggestion_engine import extract_text

logger = get_logger(__name__)


class IncrementalSearchIndex:
    """
    Manages a FAISS search index with incremental (dirty-file only)
    updates tracked via the database's embeddings table.

    Usage:
        idx = IncrementalSearchIndex(index_path=Path("data/search_index"))

        # Build or update the index:
        stats = idx.build()
        print(f"Indexed {stats['indexed']} files, skipped {stats['skipped']}")

        # Search it:
        results = idx.search("invoices from 2023", top_k=10)
        for r in results:
            print(r["path"], r["score"])
    """

    def __init__(self, index_path: Path) -> None:
        """
        Args:
            index_path:
                Base path for the FAISS index files.
                SearchIndex saves two files: <path>.faiss and <path>.json
                e.g. Path("data/search_index") writes
                     data/search_index.faiss + data/search_index.json
        """
        self._index_path = index_path
        self._index: SearchIndex | None = None

    # ── Public API ─────────────────────────────────────────────────────

    def build(self) -> dict:
        """
        Build or incrementally update the search index.

        - If no index exists on disk: embeds ALL files in the database.
        - If an index exists: embeds only files where embeddings.is_dirty = 1.
        - Files that no longer exist on disk are removed from the index.

        Returns:
            dict with keys:
                "indexed"  (int)  — files successfully embedded this run
                "skipped"  (int)  — files with no text or AI unavailable
                "removed"  (int)  — deleted files removed from the index
                "total"    (int)  — total files now in the index
                "error"    (str | None) — error message if something failed
        """
        stats = {"indexed": 0, "skipped": 0, "removed": 0, "total": 0, "error": None}

        try:
            first_build = not self._index_exists()

            if first_build:
                logger.info("No existing index — performing full build.")
                self._index = None
                files_to_embed = self._load_all_files_from_db()
            else:
                logger.info("Existing index found — checking for dirty files.")
                self._index = SearchIndex.load(self._index_path)
                files_to_embed = DB.get_dirty_files()

            if not files_to_embed and not first_build:
                # Nothing changed — clean exit
                stats["total"] = len(self._index._paths) if self._index else 0
                logger.info("Index is up to date — no files to re-embed.")
                return stats

            # Remove deleted files from the existing index
            if self._index:
                removed = self._remove_deleted_files()
                stats["removed"] = removed

            # Embed dirty/new files and merge into index
            for file_row in files_to_embed:
                path_str = file_row["path"]
                path = Path(path_str)

                # Skip files that have disappeared from disk
                if not path.exists():
                    logger.debug("Skipping missing file: %s", path_str)
                    stats["skipped"] += 1
                    continue

                # Extract text from the file
                text = extract_text(path)
                if not text or not text.strip():
                    logger.debug("No text extractable from %s — skipping.", path_str)
                    stats["skipped"] += 1
                    continue

                # Get embedding via AIGateway
                try:
                    vector = embed_text(text)
                except (AIGatewayError, ValueError) as exc:
                    logger.warning("Could not embed %s: %s", path_str, exc)
                    stats["skipped"] += 1
                    continue

                # Initialise index on first successful embedding
                if self._index is None:
                    self._index = SearchIndex(dimension=len(vector))

                # If this file is already in the index, remove the old
                # vector first (FAISS doesn't support in-place updates)
                if path_str in (self._index._paths if self._index else []):
                    self._remove_path_from_index(path_str)

                self._index.add(path_str, vector)
                stats["indexed"] += 1

                # Record in DB and clear the dirty flag
                self._record_embedding(path_str, len(vector))

            # Save updated index to disk
            if self._index is not None:
                self._index.save(self._index_path)
                stats["total"] = len(self._index._paths)
                logger.info(
                    "Index saved: %d indexed, %d skipped, %d removed. Total: %d files.",
                    stats["indexed"], stats["skipped"], stats["removed"], stats["total"],
                )
            else:
                logger.warning("Index build complete but no files were embedded.")

        except Exception as exc:
            logger.error("Index build failed: %s", exc, exc_info=True)
            stats["error"] = str(exc)

        return stats

    def search(self, query: str, top_k: int = 20) -> list[dict]:
        """
        Search the index with a plain-language query.

        Loads the index from disk on first call (lazy load). Subsequent
        calls in the same session reuse the in-memory index.

        Args:
            query:  Natural language query, e.g. "invoices from 2023".
            top_k:  Maximum number of results to return.

        Returns:
            list[dict] with keys "path" (str) and "score" (float),
            sorted best-match first. Empty list if the index doesn't
            exist yet or the query can't be embedded.

        Raises:
            FileNotFoundError:  If the index has never been built.
        """
        if not query or not query.strip():
            return []

        # Lazy-load index from disk
        if self._index is None:
            if not self._index_exists():
                raise FileNotFoundError(
                    "Search index has not been built yet. "
                    "Click 'Build Search Index' to get started."
                )
            self._index = SearchIndex.load(self._index_path)

        try:
            vector = embed_text(query)
        except (AIGatewayError, ValueError) as exc:
            logger.warning("Could not embed search query: %s", exc)
            return []

        matches = self._index.search(vector, top_k)
        return [{"path": path, "score": score} for path, score in matches]

    # ── Private helpers ────────────────────────────────────────────────

    def _index_exists(self) -> bool:
        """Return True if both FAISS index files are on disk."""
        return (
            self._index_path.with_suffix(".faiss").exists()
            and self._index_path.with_suffix(".json").exists()
        )

    def _load_all_files_from_db(self) -> list[dict]:
        """Return every file record from the database for a full build."""
        conn = DB._require_connection()
        rows = conn.execute("SELECT * FROM files").fetchall()
        return [dict(r) for r in rows]

    def _remove_deleted_files(self) -> int:
        """
        Remove paths from the in-memory index that no longer exist on disk.
        Returns the count of removed entries.
        """
        if self._index is None:
            return 0

        existing_paths = [p for p in self._index._paths if Path(p).exists()]
        removed = len(self._index._paths) - len(existing_paths)

        if removed > 0:
            # Rebuild the index with only the surviving paths.
            # We must re-embed them because FAISS doesn't support
            # deletion by index — rebuilding is the cleanest approach.
            logger.info("Removing %d deleted files from index.", removed)
            old_index = self._index
            self._index = None  # Will be rebuilt in the main loop

            # Put the surviving paths back into a new index using the
            # vectors already stored in FAISS (no re-embedding needed).
            for i, path in enumerate(old_index._paths):
                if path not in existing_paths:
                    continue
                # Retrieve the vector from the old FAISS index
                vector = old_index._index.reconstruct(i).tolist()
                if self._index is None:
                    self._index = SearchIndex(dimension=old_index.dimension)
                # add() normalises again, so pass the raw (pre-normalised) vector.
                # For IndexFlatIP after normalise_L2, reconstruct() gives the
                # already-normalised vector — this is safe.
                self._index._index.add(
                    __import__("numpy").array([vector], dtype="float32")
                )
                self._index._paths.append(path)

        return removed

    def _remove_path_from_index(self, path_str: str) -> None:
        """
        Remove a single path from the in-memory index before re-adding
        an updated version. Uses the same full-rebuild approach as
        _remove_deleted_files because FAISS IndexFlatIP doesn't support
        deletion.
        """
        if self._index is None or path_str not in self._index._paths:
            return

        import numpy as np

        old_index = self._index
        self._index = SearchIndex(dimension=old_index.dimension)

        for i, p in enumerate(old_index._paths):
            if p == path_str:
                continue
            vector = old_index._index.reconstruct(i).tolist()
            self._index._index.add(np.array([vector], dtype="float32"))
            self._index._paths.append(p)

    def _record_embedding(self, path_str: str, dimension: int) -> None:
        """
        Write or update the embeddings table row for this file, and
        clear the is_dirty flag.

        Uses the active DB singleton. Silently skips if the file isn't
        in the database (shouldn't happen, but defensive).
        """
        try:
            conn = DB._require_connection()

            # Get the file's ID
            row = conn.execute(
                "SELECT id FROM files WHERE path = ?", (path_str,)
            ).fetchone()

            if row is None:
                logger.warning(
                    "Tried to record embedding for unknown path: %s", path_str
                )
                return

            file_id = row["id"]

            # Get model name from the active provider (for logging)
            try:
                from infrastructure.ai.gateway import AIGateway
                model = AIGateway.get_provider().provider_name
            except Exception:
                model = "unknown"

            conn.execute(
                """
                INSERT INTO embeddings (file_id, model, dimension, is_dirty, embedded_at)
                VALUES (?, ?, ?, 0, datetime('now', 'utc'))
                ON CONFLICT(file_id) DO UPDATE SET
                    model       = excluded.model,
                    dimension   = excluded.dimension,
                    is_dirty    = 0,
                    embedded_at = excluded.embedded_at
                """,
                (file_id, model, dimension),
            )
            conn.commit()

        except Exception as exc:
            # Embedding tracking failure shouldn't crash the index build
            logger.warning("Could not record embedding in DB for %s: %s", path_str, exc)