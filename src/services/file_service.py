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
from domain.classifier.classifier import FileClassifier
from domain.scanner.scanner import FileScanner
from domain.scanner.file_info import AnalysisResult, FileInfo
from scanner.file_info import FileInfo as LegacyFileInfo
from domain.organizer.planner import OrganizationPlanner
from domain.organizer.organizer import AutoOrganizer
from domain.organizer.action import OrganizationAction
from infrastructure.storage.database import DB
from infrastructure.storage.memory_store import MemoryStore
from search.search_engine import build_search_index, semantic_search

logger = get_logger(__name__)


def _display_path(path: Path | str) -> str:
    """Return the filesystem path using the host platform's native format."""
    return str(path)


def _action_to_dict(action: OrganizationAction) -> dict:
    """Serialize an OrganizationAction to a plain dict for GUI consumption."""
    return {
        "action_type": action.action_type,
        "source": _display_path(action.source_path),
        "destination": _display_path(
            action.actual_target_path or action.planned_target_path
        ),
        "category": action.category,
        "confidence": round(action.confidence, 4),
        "success": action.is_success,
        "failed": action.is_failed,
        "reversed": action.is_reversed,
        "error": action.error_message,
    }


def _result_to_dict(result: AnalysisResult) -> dict:
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


class FileService:
    """Single API surface between the GUI and domain + infrastructure layers."""

    def __init__(self) -> None:
        self._scanner = FileScanner()
        self._planner = OrganizationPlanner()
        self._organizer = AutoOrganizer()
        self._last_batch_id: str | None = None
        self._last_scan_results: list[AnalysisResult] = []

    def open(self) -> None:
        """Connect to the database. Call once at application startup."""
        DB.connect()
        logger.info("FileService: database connected.")

    def close(self) -> None:
        """Close the database. Call once on application shutdown."""
        DB.close()
        logger.info("FileService: database closed.")

    def scan_folder(
        self,
        path: str | Path,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> list[dict]:
        """Scan a folder and return file metadata + AI classification."""
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

        results: list[AnalysisResult] = FileClassifier().classify_batch(files)
        self._last_scan_results = results

        if progress_callback:
            progress_callback(100, "Scan complete.")

        return [_result_to_dict(result) for result in results]

    def plan_organisation(
        self,
        target_folder: str | Path,
        scan_results: Optional[list[dict]] = None,
    ) -> list[dict]:
        """Generate a conflict-free organisation plan from scan results."""
        target = Path(target_folder)

        if scan_results is not None:
            files = [
                FileInfo(
                    path=Path(result["path"]),
                    filename=result["filename"],
                    extension=result["extension"],
                    size_bytes=result["size_bytes"],
                    modified_at=(
                        datetime.fromtimestamp(Path(result["path"]).stat().st_mtime)
                        if Path(result["path"]).exists()
                        else None
                    ),
                )
                for result in scan_results
                if not result.get("skipped")
            ]
        elif self._last_scan_results:
            files = [
                result.file_info
                for result in self._last_scan_results
                if not result.skipped
            ]
        else:
            raise ValueError(
                "No scan results available. Call scan_folder() first, "
                "or pass scan_results explicitly."
            )

        if not files:
            return []

        actions: list[OrganizationAction] = self._planner.create_plan(files, target)
        return [_action_to_dict(action) for action in actions]

    def apply_plan(
        self,
        plan: list[dict],
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> dict:
        """Execute a plan returned by plan_organisation()."""
        if not plan:
            return {"success": 0, "failed": 0, "skipped": 0, "batch_id": None}

        actions = [
            OrganizationAction(
                action_type=item["action_type"],
                source_path=Path(item["source"]),
                planned_target_path=Path(item["destination"]),
                category=item["category"],
                confidence=item["confidence"],
            )
            for item in plan
        ]

        batch_id = str(uuid.uuid4())
        self._last_batch_id = batch_id
        total = len(actions)
        stats = self._organizer.execute_plan(actions, batch_id=batch_id)

        if progress_callback:
            for index, action in enumerate(actions):
                progress_callback(
                    int((index + 1) / total * 100),
                    f"Moving: {action.source_filename}",
                )

        stats["batch_id"] = batch_id
        logger.info(
            "FileService.apply_plan: batch=%s success=%d failed=%d skipped=%d",
            batch_id,
            stats["success"],
            stats["failed"],
            stats["skipped"],
        )
        return stats

    def undo_last(self, batch_id: Optional[str] = None) -> dict:
        """Reverse the last applied batch or a specific batch by ID."""
        target_batch = batch_id or self._last_batch_id

        if not target_batch:
            return {"reversed": 0, "batch_id": None, "error": "No batch to undo."}

        try:
            count = self._organizer.undo_stack.undo_batch(target_batch)
            if target_batch == self._last_batch_id:
                self._last_batch_id = None
            logger.info(
                "FileService.undo_last: reversed %d for batch %s",
                count,
                target_batch,
            )
            return {"reversed": count, "batch_id": target_batch, "error": None}
        except Exception as exc:
            logger.error("FileService.undo_last: %s", exc)
            return {"reversed": 0, "batch_id": target_batch, "error": str(exc)}

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Perform semantic search over the FAISS index."""
        if not query or not query.strip():
            return []

        results = semantic_search(query, top_k=top_k)
        return [
            {"path": _display_path(result.path), "score": round(result.score, 4)}
            for result in results
        ]

    def build_index(
        self,
        files: Optional[list[dict]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> dict:
        """Build or rebuild the FAISS semantic search index."""
        if progress_callback:
            progress_callback(0, "Building search index…")

        try:
            legacy_files: Optional[list[LegacyFileInfo]] = None
            if files is not None:
                legacy_files = []
                for file_data in files:
                    path = Path(file_data["path"])
                    stat = path.stat() if path.exists() else None
                    legacy_files.append(
                        LegacyFileInfo(
                            name=file_data["filename"],
                            path=path,
                            extension=file_data["extension"],
                            size=file_data["size_bytes"],
                            created=(
                                datetime.fromtimestamp(stat.st_ctime)
                                if stat
                                else datetime.now()
                            ),
                            modified=(
                                datetime.fromtimestamp(stat.st_mtime)
                                if stat
                                else datetime.now()
                            ),
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
