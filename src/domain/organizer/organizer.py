"""
DesktopAI v2.0 — Auto Organizer
File: src/domain/organizer/organizer.py

Executes plans, writes the audit trail, learns preferences,
and delegates undo to the DB-driven UndoStack.
"""
from __future__ import annotations
import shutil
import uuid
from pathlib import Path

from core.logger import get_logger
from domain.organizer.action import OrganizationAction
from domain.organizer.undo_stack import UndoStack
from infrastructure.config.settings import Settings
from infrastructure.storage.database import DB
from infrastructure.storage.memory_store import MemoryStore

logger = get_logger(__name__)


class AutoOrganizer:
    def __init__(self) -> None:
        self.undo_stack = UndoStack()

    # ── Apply ─────────────────────────────────────────────────────
    def execute_plan(self, actions: list[OrganizationAction], batch_id: str | None = None) -> dict:
        if not actions:
            return {"success": 0, "failed": 0, "skipped": 0}
        if not batch_id:
            batch_id = str(uuid.uuid4())

        stats = {"success": 0, "failed": 0, "skipped": 0}
        for action in actions:
            try:
                self._execute_action(action, batch_id)
                if action.is_success:
                    stats["success"] += 1
                elif action.is_failed:
                    stats["failed"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as exc:
                logger.error("Organizer: unexpected error on %s: %s", action.source_filename, exc)
                action.mark_failed(str(exc))
                self._record_failure(action, batch_id)
                stats["failed"] += 1
        return stats

    def _execute_action(self, action: OrganizationAction, batch_id: str) -> None:
        source = action.source_path
        target = self._resolve_conflicts(source, action.planned_target_path)
        action.actual_target_path = target
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if action.action_type == "move":
                shutil.move(str(source), str(target))
            elif action.action_type == "copy":
                shutil.copy2(str(source), str(target))
            elif action.action_type == "rename":
                source.rename(target)
            else:
                raise ValueError(f"Unknown action type: {action.action_type}")

            history_id = DB.record_history_entry(
                action_type=action.action_type,
                source_path=str(source),
                target_path=str(target),
                category=action.category,
                confidence=action.confidence,
                model=Settings.ai.model,
                status="completed",
                batch_id=batch_id,
            )
            action.mark_success(target, history_id)
            self.undo_stack.push(action)

            if action.confidence >= 0.90:
                MemoryStore.remember_folder(source.suffix, str(target.parent), action.confidence)
        except (PermissionError, FileNotFoundError, OSError) as exc:
            logger.warning("Organizer: %s failed: %s", source.name, exc)
            action.mark_failed(str(exc))
            self._record_failure(action, batch_id)

    def _resolve_conflicts(self, source: Path, target: Path) -> Path:
        if not target.exists():
            return target
        stem, suffix, counter = source.stem, source.suffix, 1
        while target.exists():
            target = target.parent / f"{stem}_{counter}{suffix}"
            counter += 1
        return target

    def _record_failure(self, action: OrganizationAction, batch_id: str) -> None:
        DB.record_history_entry(
            action_type=action.action_type,
            source_path=str(action.source_path),
            target_path=str(action.planned_target_path),
            category=action.category,
            confidence=action.confidence,
            model=Settings.ai.model,
            status="failed",
            error_message=action.error_message,
            batch_id=batch_id,
        )

    # ── Undo ──────────────────────────────────────────────────────
    def undo_last_batch(self, batch_id: str) -> int:
        return self.undo_stack.undo_batch(batch_id)

    def undo_last_action(self) -> bool:
        return self.undo_stack.undo_last_action()