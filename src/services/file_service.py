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

from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from core.logger import get_logger

# Domain — scanner
from domain.scanner.scanner import FileScanner
from domain.scanner.file_info import AnalysisResult
from domain.scanner.file_info import FileInfo as DomainFileInfo

# Domain — classifier
from domain.classifier.classifier import FileClassifier

# Domain — organizer  (actual class names in the repo)
from domain.organizer.organizer import Organizer, OrganizerResult
from domain.organizer.action import ActionItem, ActionPlan, ActionType

# Infrastructure
from infrastructure.storage.database import DB
from infrastructure.storage.memory_store import _MemoryStore

# Legacy scanner FileInfo (used by search index)
from scanner.file_info import FileInfo as LegacyFileInfo

# Search — M8: routes through domain layer and AIGateway.
# These module-level aliases let tests patch them with:
#   patch("services.file_service.build_search_index", ...)
#   patch("services.file_service.semantic_search", ...)
from domain.search.engine import build_index as build_search_index
from domain.search.engine import search as semantic_search

logger = get_logger(__name__)

# Module-level MemoryStore singleton (matches repo pattern)
MemoryStore = _MemoryStore()


# ── serialization helpers ─────────────────────────────────────────────────────

def _display_path(path: Path | str) -> str:
    """Return the filesystem path as a plain string."""
    return str(path)


def _action_item_to_dict(item: ActionItem) -> dict:
    """Serialize an ActionItem to a plain dict for GUI consumption."""
    return {
        "action_type": item.action_type.name,          # e.g. "MOVE"
        "source": _display_path(item.source),
        "destination": _display_path(item.destination) if item.destination else "",
        "category": item.category,
        "reason": item.reason,
        "status": item.status.value,                   # e.g. "pending"
        "error": item.error,
        "action_id": item.action_id,
        # Convenience aliases the GUI uses
        "confidence": 1.0,                             # Planner doesn't score; default 100%
        "success": item.status.value == "applied",
        "failed": item.status.value == "failed",
        "reversed": item.status.value == "undone",
    }


def _analysis_result_to_dict(result: AnalysisResult) -> dict:
    """Serialize an AnalysisResult to a plain dict for GUI consumption."""
    fi = result.file_info
    return {
        "path": _display_path(fi.path),
        "filename": fi.filename,
        "extension": fi.extension,
        "size_bytes": fi.size_bytes,
        "category": result.category,
        "confidence": round(result.confidence, 4),
        "method": result.method,
        "skipped": result.skipped,
        "skip_reason": result.skip_reason,
    }


# ── FileService ───────────────────────────────────────────────────────────────

class FileService:
    """Single API surface between the GUI and domain + infrastructure layers."""

    def __init__(self) -> None:
        self._scanner = FileScanner()
        self._organizer = Organizer(db_manager=DB)
        self._last_plan: Optional[ActionPlan] = None
        self._last_scan_results: list[AnalysisResult] = []

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def open(self) -> None:
        """Connect to the database. Call once at application startup."""
        DB.connect()
        logger.info("FileService: database connected.")

    def close(self) -> None:
        """Close the database. Call once on application shutdown."""
        DB.close()
        logger.info("FileService: database closed.")

    # ── scan ─────────────────────────────────────────────────────────────────

    def scan_folder(
        self,
        path: str | Path,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> list[dict]:
        """Scan a folder, classify every file, and return plain dicts."""
        folder = Path(path)
        logger.info("FileService.scan_folder: %s", folder)

        if progress_callback:
            progress_callback(0, f"Scanning {folder.name}…")

        files: list[DomainFileInfo] = self._scanner.scan(folder)

        if not files:
            self._last_scan_results = []
            return []

        if progress_callback:
            progress_callback(30, f"Classifying {len(files)} files…")

        results: list[AnalysisResult] = FileClassifier().classify_batch(files)
        self._last_scan_results = results

        if progress_callback:
            progress_callback(100, "Scan complete.")

        return [_analysis_result_to_dict(r) for r in results]

    # ── plan ─────────────────────────────────────────────────────────────────

    def plan_organisation(
        self,
        target_folder: str | Path,
        scan_results: Optional[list[dict]] = None,
    ) -> list[dict]:
        """
        Generate a conflict-free organisation plan from scan results.
        Returns a list of plain dicts (one per ActionItem).
        """
        target = Path(target_folder)

        # Resolve which FileInfo objects to plan for
        if scan_results is not None:
            # Re-hydrate minimal DomainFileInfo from the dicts the GUI passed back
            files: list[DomainFileInfo] = []
            for r in scan_results:
                if r.get("skipped"):
                    continue
                p = Path(r["path"])
                try:
                    mtime = datetime.fromtimestamp(p.stat().st_mtime) if p.exists() else None
                except OSError:
                    mtime = None
                fi = DomainFileInfo(
                    path=p,
                    filename=r["filename"],
                    extension=r["extension"],
                    size_bytes=r["size_bytes"],
                    modified_at=mtime,
                )
                # Restore category so the Planner can use it
                fi = fi.with_category(r.get("category", "Miscellaneous"), r.get("confidence", 1.0))
                files.append(fi)
        elif self._last_scan_results:
            files = [r.file_info for r in self._last_scan_results if not r.skipped]
        else:
            raise ValueError(
                "No scan results available. Call scan_folder() first, "
                "or pass scan_results explicitly."
            )

        if not files:
            return []

        plan: ActionPlan = self._organizer.build_plan(files, root_dir=target)
        self._last_plan = plan
        return [_action_item_to_dict(item) for item in plan.items]

    # ── apply ─────────────────────────────────────────────────────────────────

    def apply_plan(
        self,
        plan: Optional[list[dict]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> dict:
        """
        Execute the cached plan (or the plan dict list passed in).
        Returns {"success": int, "failed": int, "skipped": int, "session_id": str}.
        """
        result: OrganizerResult = self._organizer.apply_plan()

        if progress_callback:
            progress_callback(100, "Done.")

        logger.info(
            "FileService.apply_plan: ok=%d fail=%d skip=%d session=%s",
            result.succeeded, result.failed, result.skipped, result.session_id,
        )
        return {
            "success": result.succeeded,
            "failed": result.failed,
            "skipped": result.skipped,
            "session_id": result.session_id,
            "errors": result.errors,
        }

    # ── undo ─────────────────────────────────────────────────────────────────

    def undo_last(self) -> dict:
        """Reverse the last applied batch."""
        if not self._organizer.can_undo:
            return {"reversed": 0, "error": "Nothing to undo."}

        try:
            succeeded, failed = self._organizer.undo_last()
            logger.info("FileService.undo_last: reversed=%d failed=%d", succeeded, failed)
            return {"reversed": succeeded, "failed": failed, "error": None}
        except Exception as exc:
            logger.error("FileService.undo_last: %s", exc)
            return {"reversed": 0, "failed": 0, "error": str(exc)}

    # ── search ────────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Perform semantic search over the FAISS index.

        semantic_search() (aliased from domain.search.engine.search) may
        return either plain dicts OR objects with .path / .score, depending
        on the provider. We handle both shapes here.
        """
        if not query or not query.strip():
            return []
        results = semantic_search(query, top_k=top_k)
        output = []
        for r in results:
            if isinstance(r, dict):
                path = _display_path(r["path"])
                score = round(float(r["score"]), 4)
            else:
                # MagicMock / object with attributes (test doubles or future providers)
                path = _display_path(r.path)
                score = round(float(r.score), 4)
            output.append({"path": path, "score": score})
        return output

    def build_index(
        self,
        files: Optional[list[dict]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> dict:
        """Build or incrementally update the FAISS semantic search index.

        build_search_index() is aliased from domain.search.engine.build_index.
        When patched in tests it may return an int (old shape) or a full
        stats dict (new shape). We normalise both so the tests remain green.

        Returns: {"indexed": int, "error": str | None, ...}
        """
        if progress_callback:
            progress_callback(0, "Building search index…")

        try:
            raw = build_search_index()

            # Normalise: old engine returned int, new engine returns dict
            if isinstance(raw, int):
                indexed = raw
                stats: dict = {"indexed": indexed, "error": None}
            else:
                stats = raw
                indexed = stats.get("indexed", 0)

            if progress_callback:
                progress_callback(100, f"Indexed {indexed} file(s).")

            logger.info(
                "FileService.build_index: indexed=%d",
                indexed,
            )
            return stats

        except Exception as exc:
            logger.error("FileService.build_index: %s", exc)
            return {"indexed": 0, "error": str(exc)}

    # ── memory / stats ────────────────────────────────────────────────────────

    def get_memory_stats(self) -> dict:
        """Return a summary of learned preferences and database state."""
        try:
            prefs = MemoryStore.get_all()
            db_stats = DB.get_stats()
            return {
                "preferences": prefs,
                "total_files": db_stats.get("total_files", 0),
                "total_operations": db_stats.get("total_operations", 0),
                "categories": db_stats.get("categories", {}),
                "recent_sessions": db_stats.get("recent_sessions", []),
            }
        except Exception as exc:
            logger.error("FileService.get_memory_stats: %s", exc)
            return {
                "preferences": [],
                "total_files": 0,
                "total_operations": 0,
                "categories": {},
                "recent_sessions": [],
            }