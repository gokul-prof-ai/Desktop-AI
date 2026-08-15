"""
src/application/undo_stack.py
─────────────────────────────
UndoStack — physically reverses applied actions and keeps the history
DB in sync.

Undo logic per ActionType
──────────────────────────
MOVE          : move file from destination back to source
DELETE_EMPTY  : recreate the directory (cannot restore contents – logged as warning)
MERGE_FOLDER  : move all files that came from source_dir back there,
                recreate source_dir if needed, remove destination items
                that originated from the merge (tracked in metadata)
"""

from __future__ import annotations

import logging
import shutil
from collections import deque
from pathlib import Path
from typing import Optional

from application.action import ActionItem, ActionPlan, ActionStatus, ActionType

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class UndoError(Exception):
    """Raised when an undo operation cannot be completed."""


# ──────────────────────────────────────────────────────────────────────────────
# UndoStack
# ──────────────────────────────────────────────────────────────────────────────

class UndoStack:
    """
    Maintains a stack of applied ActionPlans and physically reverses
    them on request.

    Parameters
    ──────────
    db_manager  : Optional DatabaseManager; when provided, history rows
                  are updated to status='undone' after reversal.
    max_depth   : How many sessions to keep on the undo stack (default 20).
    """

    def __init__(self, db_manager=None, max_depth: int = 20) -> None:
        self._db     = db_manager
        self._stack : deque[ActionPlan] = deque(maxlen=max_depth)

    # ── public API ────────────────────────────────────────────────────────────

    def push(self, plan: ActionPlan) -> None:
        """Push a fully-applied plan onto the stack."""
        self._stack.append(plan)
        logger.debug("UndoStack: pushed session %s (%d items)", plan.session_id, len(plan))

    def can_undo(self) -> bool:
        """True when there is at least one session that can be reversed."""
        return bool(self._stack)

    def peek(self) -> Optional[ActionPlan]:
        """Return the most recent plan without removing it."""
        return self._stack[-1] if self._stack else None

    def undo_last(self) -> tuple[int, int]:
        """
        Reverse the most recently applied plan.

        Returns
        ───────
        (succeeded, failed) counts of individual action reversals.
        """
        if not self._stack:
            raise UndoError("Nothing to undo.")

        plan = self._stack.pop()
        logger.info("UndoStack: undoing session %s (%d items)", plan.session_id, len(plan))

        succeeded = 0
        failed    = 0

        # Process in REVERSE order so folder deletes are re-created before
        # files are moved back into them.
        for item in reversed(plan.items):
            if item.status != ActionStatus.APPLIED:
                continue
            try:
                self._reverse_item(item)
                item.status = ActionStatus.UNDONE
                self._db_update(item, "undone")
                succeeded += 1
            except Exception as exc:
                item.error  = str(exc)
                item.status = ActionStatus.FAILED
                self._db_update(item, "undo_failed")
                failed += 1
                logger.error("UndoStack: failed to reverse %s – %s", item, exc)

        logger.info(
            "UndoStack: undo complete – %d reversed, %d failed",
            succeeded, failed,
        )
        return succeeded, failed

    def clear(self) -> None:
        """Wipe the entire stack (e.g. after a new scan session)."""
        self._stack.clear()

    @property
    def depth(self) -> int:
        return len(self._stack)

    # ── reversal logic ────────────────────────────────────────────────────────

    def _reverse_item(self, item: ActionItem) -> None:
        match item.action_type:
            case ActionType.MOVE:
                self._undo_move(item)
            case ActionType.DELETE_EMPTY:
                self._undo_delete_empty(item)
            case ActionType.MERGE_FOLDER:
                self._undo_merge_folder(item)
            case _:
                raise UndoError(f"Unknown action type: {item.action_type}")

    # ── MOVE undo ─────────────────────────────────────────────────────────────

    def _undo_move(self, item: ActionItem) -> None:
        """Move the file from destination back to its original source path."""
        src = item.destination
        dst = item.source

        if src is None or not src.exists():
            raise UndoError(
                f"Cannot undo MOVE: destination '{src}' no longer exists."
            )

        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists():
            # Avoid silent overwrite – rename destination to a .bak copy
            bak = dst.with_suffix(dst.suffix + ".bak")
            logger.warning(
                "UndoStack: '%s' already exists at restore path – renaming to '%s'",
                dst, bak,
            )
            dst.rename(bak)

        shutil.move(str(src), str(dst))
        logger.debug("UndoStack: MOVE undone  %s → %s", src, dst)

        # Clean up empty destination parent folder
        self._remove_if_empty(src.parent)

    # ── DELETE_EMPTY undo ─────────────────────────────────────────────────────

    def _undo_delete_empty(self, item: ActionItem) -> None:
        """Recreate the deleted directory (contents are gone – warn only)."""
        folder = item.source
        if folder.exists():
            logger.debug("UndoStack: DELETE_EMPTY undo – folder already exists: %s", folder)
            return

        folder.mkdir(parents=True, exist_ok=True)
        logger.warning(
            "UndoStack: recreated empty folder '%s' but cannot restore its "
            "original contents (they were already empty at deletion time).",
            folder,
        )

    # ── MERGE_FOLDER undo ─────────────────────────────────────────────────────

    def _undo_merge_folder(self, item: ActionItem) -> None:
        """
        Move files that were merged from source_dir back to source_dir.

        The MERGE action stores the list of moved files in item.reason as
        a newline-separated manifest (written by the Executor).  We parse
        that to know exactly which files to move back.
        """
        src_dir = item.source       # original folder (was merged away)
        dst_dir = item.destination  # folder that received the files

        if dst_dir is None:
            raise UndoError("MERGE_FOLDER item has no destination; cannot undo.")

        # Reconstruct the list of files that were moved
        moved_files = self._parse_merge_manifest(item.reason)

        if not moved_files:
            logger.warning(
                "UndoStack: MERGE_FOLDER undo – no manifest found in item.reason; "
                "attempting to recreate source directory only."
            )
            src_dir.mkdir(parents=True, exist_ok=True)
            return

        src_dir.mkdir(parents=True, exist_ok=True)

        for filename in moved_files:
            src_file = dst_dir / filename
            dst_file = src_dir / filename

            if not src_file.exists():
                logger.warning(
                    "UndoStack: merge undo – '%s' no longer in '%s'; skipping.",
                    filename, dst_dir,
                )
                continue

            if dst_file.exists():
                bak = dst_file.with_suffix(dst_file.suffix + ".bak")
                dst_file.rename(bak)

            shutil.move(str(src_file), str(dst_file))
            logger.debug("UndoStack: merge undo moved  %s → %s", src_file, dst_file)

        # If the merge destination folder is now empty, remove it
        self._remove_if_empty(dst_dir)

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_merge_manifest(reason: str) -> list[str]:
        """
        Extract the file-name list from the reason string.

        The Executor writes:
            "Merged N files from <src>: file1.ext|file2.ext|…"
        We extract everything after the last colon and split on '|'.
        """
        if ":" not in reason:
            return []
        payload = reason.split(":", 1)[-1].strip()
        return [f.strip() for f in payload.split("|") if f.strip()]

    @staticmethod
    def _remove_if_empty(folder: Path) -> None:
        """Remove a directory only if it exists and is empty."""
        try:
            if folder.exists() and not any(folder.iterdir()):
                folder.rmdir()
                logger.debug("UndoStack: removed now-empty folder '%s'", folder)
        except Exception as exc:
            logger.debug("UndoStack: could not remove '%s' – %s", folder, exc)

    def _db_update(self, item: ActionItem, status: str) -> None:
        """Update the history row in the DB if a manager is available."""
        if self._db is None:
            return
        try:
            with self._db.get_connection() as conn:
                conn.execute(
                    "UPDATE history SET status = ? WHERE action_id = ?",
                    (status, item.action_id),
                )
        except Exception as exc:
            logger.warning("UndoStack: DB update failed for %s – %s", item.action_id, exc)