"""
DesktopAI v2.0 — FileService
File: src/services/file_service.py

The ONLY entry point between the GUI (and any future CLI/REST layer)
and the domain/infrastructure layers.

Rules:
- GUI views import FileService, never domain classes directly.
- FileService never imports from gui/.
- Every method returns plain Python types (dict, list, bool, int)
  so callers never depend on domain dataclasses.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from core.logger import get_logger
from domain.scanner.scanner import FileScanner
from domain.scanner.file_info import AnalysisResult, FileInfo
from scanner.file_info import FileInfo as LegacyFileInfo  # used by search engine only
from domain.organizer.planner import OrganizationPlanner
from domain.organizer.organizer import AutoOrganizer
from domain.organizer.action import OrganizationAction
from infrastructure.storage.database import DB
from infrastructure.storage.memory_store import MemoryStore
from search.search_engine import build_search_index, semantic_search

logger = get_logger(__name__)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _action_to_dict(action: OrganizationAction) -> dict:
    """Serialize an OrganizationAction to a plain dict for GUI consumption."""
    return {
        "action_type":   action.action_type,
        "source":        str(action.source_path),
        "destination":   str(action.actual_target_path or action.planned_target_path),
        "category":      action.category,
        "confidence":    round(action.confidence, 4),
        "success":       action.is_success,
        "failed":        action.is_failed,
        "reversed":      action.is_reversed,
        "error":         action.error_message,
    }


def _result_to_dict(result: AnalysisResult) -> dict:
    """Serialize an AnalysisResult to a plain dict for GUI consumption."""
    fi = result.file_info
    return {
        "path":        str(fi.path),
        "filename":    fi.filename,
        "extension":   fi.extension,
        "size_bytes":  fi.size_bytes,
        "category":    result.category,
        "confidence":  round(result.confidence, 4),
        "method":      result.method,
        "skipped":     result.skipped,
        "skip_reason": result.skip_reason,
    }


# ── FileService ───────────────────────────────────────────────────────────────

class FileService:
    """
    Single API surface between the GUI and the domain + infrastructure layers.

    Lifecycle:
        service = FileService()
        service.open()          # call once at app startup
        ...                     # use throughout the app
        service.close()         # call once on shutdown

    Thread safety:
        scan_folder and build_index are designed to be called from
        QThread workers (they accept a progress_callback). All other
        methods are lightweight and safe to call from the main thread.
    """

    def __init__(self) -> None:
        self._scanner   = FileScanner()
        self._planner   = OrganizationPlanner()
        self._organizer = AutoOrganizer()
        # Holds the last batch_id so undo_last() works without extra args.
        self._last_batch_id: str | None = None
        # Cache the last scan so plan_organisation can reference it.
        self._last_scan_results: list[AnalysisResult] = []

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def open(self) -> None:
        """Connect to the database. Call once at application startup."""
        DB.connect()
        logger.info("FileService: database connected.")

    def close(self) -> None:
        """Close the database. Call once on application shutdown."""
        DB.close()
        logger.info("FileService: database closed.")

    # ── 1. Scan ───────────────────────────────────────────────────────────────

    def scan_folder(
        self,
        path: str | Path,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> list[dict]:
        """
        Scan a folder and return file metadata + AI classification.

        Args:
            path: Folder to scan.
            progress_callback: Optional (percent: int, message: str) callable
                               for reporting progress to the GUI.

        Returns:
            List of file dicts. Each dict has: path, filename, extension,
            size_bytes, category, confidence, method, skipped, skip_reason.

        Raises:
            FileNotFoundError: if the folder does not exist.
            NotADirectoryError: if the path is not a folder.
        """
        folder = Path(path)
        logger.info("FileService.scan_folder: %s", folder)

        if progress_callback:
            progress_callback(0, f"Scanning {folder.name}…")

        files: list[FileInfo] = self._scanner.scan(folder)

        if not files:
            self._last_scan_results = []
            return []

        if progress_callback:
            progress_callback(30, f"Classifying {len(files)} files…")

        # Use the domain classifier via planner internals.
        # The classifier lives on the planner; expose it through a batch call.
        from domain.classifier.classifier import FileClassifier
        classifier = FileClassifier()
        results: list[AnalysisResult] = classifier.classify_batch(files)

        self._last_scan_results = results

        if progress_callback:
            progress_callback(100, "Scan complete.")

        return [_result_to_dict(r) for r in results]

    # ── 2. Plan ───────────────────────────────────────────────────────────────

    def plan_organisation(
        self,
        target_folder: str | Path,
        scan_results: Optional[list[dict]] = None,
    ) -> list[dict]:
        """
        Generate a conflict-free organisation plan from the last (or given) scan.

        Args:
            target_folder: Where organised files should land.
            scan_results: Optional list of scan dicts returned by scan_folder().
                          If omitted, uses the most recent scan cached in memory.

        Returns:
            List of action dicts with: action_type, source, destination,
            category, confidence, success, failed, reversed, error.

        Raises:
            ValueError: if there are no scan results to plan from.
        """
        target = Path(target_folder)

        if scan_results is not None:
            # Re-hydrate FileInfo objects from the dicts so the planner can use them.
            files = [
                FileInfo(
                    path=Path(r["path"]),
                    filename=r["filename"],
                    extension=r["extension"],
                    size_bytes=r["size_bytes"],
                    modified_at=datetime.fromtimestamp(Path(r["path"]).stat().st_mtime)
                    if Path(r["path"]).exists() else None,
                )
                for r in scan_results
                if not r.get("skipped")
            ]
        elif self._last_scan_results:
            files = [r.file_info for r in self._last_scan_results if not r.skipped]
        else:
            raise ValueError(
                "No scan results available. Call scan_folder() first, "
                "or pass scan_results explicitly."
            )

        if not files:
            return []

        actions: list[OrganizationAction] = self._planner.create_plan(files, target)
        return [_action_to_dict(a) for a in actions]

    # ── 3. Apply plan ─────────────────────────────────────────────────────────

    def apply_plan(
        self,
        plan: list[dict],
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> dict:
        """
        Execute a plan returned by plan_organisation().

        Args:
            plan: List of action dicts from plan_organisation().
            progress_callback: Optional (percent: int, message: str) callable.

        Returns:
            Summary dict: { success, failed, skipped, batch_id }.
        """
        if not plan:
            return {"success": 0, "failed": 0, "skipped": 0, "batch_id": None}

        # Re-hydrate OrganizationAction objects from the plan dicts.
        actions: list[OrganizationAction] = [
            OrganizationAction(
                action_type=p["action_type"],
                source_path=Path(p["source"]),
                planned_target_path=Path(p["destination"]),
                category=p["category"],
                confidence=p["confidence"],
            )
            for p in plan
        ]

        batch_id = str(uuid.uuid4())
        self._last_batch_id = batch_id

        total = len(actions)
        stats = self._organizer.execute_plan(actions, batch_id=batch_id)

        if progress_callback:
            for i, action in enumerate(actions):
                pct = int((i + 1) / total * 100)
                progress_callback(pct, f"Moving: {action.source_filename}")

        stats["batch_id"] = batch_id
        logger.info(
            "FileService.apply_plan: batch=%s  success=%d  failed=%d  skipped=%d",
            batch_id, stats["success"], stats["failed"], stats["skipped"],
        )
        return stats

    # ── 4. Undo ───────────────────────────────────────────────────────────────

    def undo_last(self, batch_id: Optional[str] = None) -> dict:
        """
        Reverse the last applied batch (or a specific batch by ID).

        Args:
            batch_id: The batch to undo. Defaults to the most recent apply_plan().

        Returns:
            { reversed: int, batch_id: str | None, error: str | None }
        """
        target_batch = batch_id or self._last_batch_id

        if not target_batch:
            return {"reversed": 0, "batch_id": None, "error": "No batch to undo."}

        try:
            count = self._organizer.undo_stack.undo_batch(target_batch)
            if target_batch == self._last_batch_id:
                self._last_batch_id = None
            logger.info("FileService.undo_last: reversed %d for batch %s", count, target_batch)
            return {"reversed": count, "batch_id": target_batch, "error": None}
        except Exception as exc:
            logger.error("FileService.undo_last: %s", exc)
            return {"reversed": 0, "batch_id": target_batch, "error": str(exc)}

    # ── 5. Search ─────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """
        Perform semantic search over the FAISS index.

        Args:
            query:  Plain-language search query.
            top_k:  Maximum number of results to return.

        Returns:
            List of { path: str, score: float } dicts, best match first.
            Empty list if the index hasn't been built or query is blank.
        """
        if not query or not query.strip():
            return []

        results = semantic_search(query, top_k=top_k)
        return [{"path": str(r.path), "score": round(r.score, 4)} for r in results]

    # ── 6. Build index ────────────────────────────────────────────────────────

    def build_index(
        self,
        files: Optional[list[dict]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> dict:
        """
        Build (or rebuild) the FAISS semantic search index.

        Args:
            files: Optional list of scan dicts. Defaults to every file
                   already in the database.
            progress_callback: Optional (percent: int, message: str) callable.

        Returns:
            { indexed: int, error: str | None }
        """
        if progress_callback:
            progress_callback(0, "Building search index…")

        try:
            # Re-hydrate as LegacyFileInfo — the search engine (v1 search module)
            # expects scanner.file_info.FileInfo, not domain.scanner.file_info.FileInfo.
            legacy_files: Optional[list[LegacyFileInfo]] = None
            if files is not None:
                legacy_files = []
                for f in files:
                    p = Path(f["path"])
                    stat = p.stat() if p.exists() else None
                    legacy_files.append(
                        LegacyFileInfo(
                            name=f["filename"],
                            path=p,
                            extension=f["extension"],
                            size=f["size_bytes"],
                            created=datetime.fromtimestamp(stat.st_ctime) if stat else datetime.now(),
                            modified=datetime.fromtimestamp(stat.st_mtime) if stat else datetime.now(),
                        )
                    )

            indexed = build_search_index(files=legacy_files)

            if progress_callback:
                progress_callback(100, f"Indexed {indexed} file(s).")

            logger.info("FileService.build_index: %d files indexed.", indexed)
            return {"indexed": indexed, "error": None}

        except Exception as exc:
            logger.error("FileService.build_index: %s", exc)
            return {"indexed": 0, "error": str(exc)}

    # ── 7. Memory stats ───────────────────────────────────────────────────────

    def get_memory_stats(self) -> dict:
        """
        Return a summary of learned user preferences and database state.

        Returns:
            {
                preferences:      list of { key, folder, confidence, last_used },
                total_files:      int,
                total_operations: int,
                categories:       { category: count },
                recent_sessions:  list,
            }
        """
        try:
            prefs = MemoryStore.get_all()
            db_stats = DB.get_stats()
            return {
                "preferences":      prefs,
                "total_files":      db_stats.get("total_files", 0),
                "total_operations": db_stats.get("total_operations", 0),
                "categories":       db_stats.get("categories", {}),
                "recent_sessions":  db_stats.get("recent_sessions", []),
            }
        except Exception as exc:
            logger.error("FileService.get_memory_stats: %s", exc)
            return {
                "preferences":      [],
                "total_files":      0,
                "total_operations": 0,
                "categories":       {},
                "recent_sessions":  [],
            }
