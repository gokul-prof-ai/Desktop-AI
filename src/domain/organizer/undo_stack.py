"""
DesktopAI v2.0 — Undo Stack
File: src/domain/organizer/undo_stack.py

DB-driven undo: any batch can be reversed, even after a restart,
because the source/target paths come from the history table.
"""
from __future__ import annotations
from pathlib import Path

from core.logger import get_logger
from domain.organizer.action import OrganizationAction
from infrastructure.storage.database import DB

logger = get_logger(__name__)


class UndoStack:
    def __init__(self) -> None:
        self._stack: list[OrganizationAction] = []

    # ── In-memory (current session) ───────────────────────────────
    def push(self, action: OrganizationAction) -> None:
        if action.is_success:
            self._stack.append(action)

    def pop(self) -> OrganizationAction | None:
        return self._stack.pop() if self._stack else None

    def clear(self) -> None:
        self._stack.clear()

    def undo_last_action(self) -> bool:
        action = self.pop()
        if not action or action.is_reversed:
            return False
        return self._reverse_action(action)

    # ── DB-driven (any batch, any session) ────────────────────────
    def undo_batch(self, batch_id: str) -> int:
        entries = DB.get_history(batch_id=batch_id, status="completed")
        if not entries:
            logger.warning("UndoStack: no completed actions for batch %s", batch_id)
            return 0

        reversed_count = 0
        for entry in reversed(entries):  # newest first
            action = OrganizationAction(
                action_type=entry["action_type"],
                source_path=Path(entry["source_path"]),
                planned_target_path=Path(entry["target_path"]),
                actual_target_path=Path(entry["target_path"]),
                category=entry["category"] or "Unknown",
                confidence=entry["confidence"] or 0.0,
                history_id=entry["id"],
            )
            if self._reverse_action(action):
                reversed_count += 1

        logger.info(
            "UndoStack: reversed %d/%d for batch %s",
            reversed_count, len(entries), batch_id,
        )
        return reversed_count

    # ── Core reversal ─────────────────────────────────────────────
    def _reverse_action(self, action: OrganizationAction) -> bool:
        if not action.actual_target_path:
            return False
        try:
            if action.action_type in ("move", "rename"):
                if not action.actual_target_path.exists():
                    logger.warning("UndoStack: target missing: %s", action.actual_target_path)
                    return False
                action.source_path.parent.mkdir(parents=True, exist_ok=True)
                action.actual_target_path.rename(action.source_path)
            elif action.action_type == "copy":
                if action.actual_target_path.exists():
                    action.actual_target_path.unlink()
            else:
                return False

            if action.history_id:
                DB.mark_history_undone(action.history_id)
            action.mark_reversed()
            return True
        except OSError as exc:
            logger.error("UndoStack: reverse failed for %s: %s", action.source_filename, exc)
            return False