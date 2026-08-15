"""
src/application/organizer.py
─────────────────────────────
Organizer — the single public façade for the entire file-organisation
pipeline.  The GUI talks to this class only; it never touches the Planner,
UndoStack, or filesystem directly.

Responsibilities
────────────────
1. Receive a list of FileInfo objects (emitted by HomeView via scan_ready).
2. Delegate to Planner to build an ActionPlan.
3. Expose the plan to the GUI for user confirmation.
4. On user confirmation, execute the plan (MOVE / DELETE_EMPTY / MERGE_FOLDER).
5. Write every applied action to the history DB.
6. Push the plan onto the UndoStack.
7. Expose undo_last() so the GUI's Undo button works.
8. Emit Qt-compatible signals (progress, completed, failed, undo_completed).

Qt integration
──────────────
Organizer inherits from QObject so it can emit signals.  Run
apply_plan() / undo_last() from a worker thread (QThread) to keep the
GUI responsive — the Organizer itself is thread-safe for single-session
use (no shared mutable state between concurrent calls).
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Optional, Sequence

from PySide6.QtCore import QObject, Signal

from application.action import ActionItem, ActionPlan, ActionStatus, ActionType
from application.planner import Planner
from application.undo_stack import UndoStack, UndoError
from domain.models import FileInfo

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# OrganizerResult  – returned from apply_plan / undo_last
# ──────────────────────────────────────────────────────────────────────────────

class OrganizerResult:
    def __init__(
        self,
        succeeded : int = 0,
        failed    : int = 0,
        skipped   : int = 0,
        session_id: str = "",
        errors    : Optional[list[str]] = None,
    ) -> None:
        self.succeeded  = succeeded
        self.failed     = failed
        self.skipped    = skipped
        self.session_id = session_id
        self.errors     = errors or []

    @property
    def total(self) -> int:
        return self.succeeded + self.failed + self.skipped

    def __repr__(self) -> str:
        return (
            f"OrganizerResult(ok={self.succeeded}, fail={self.failed}, "
            f"skip={self.skipped}, session={self.session_id!r})"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Organizer
# ──────────────────────────────────────────────────────────────────────────────

class Organizer(QObject):
    """
    Orchestrates the full file-organisation pipeline.

    Signals
    ───────
    progress_updated(current: int, total: int)
        Emitted after each action is processed.
    plan_ready(plan: ActionPlan)
        Emitted when a new plan has been built (GUI shows it for confirmation).
    apply_completed(result: OrganizerResult)
        Emitted when apply_plan() finishes.
    undo_completed(succeeded: int, failed: int)
        Emitted when undo_last() finishes.
    error_occurred(message: str)
        Emitted on a non-fatal error during execution.
    """

    progress_updated = Signal(int, int)         # current, total
    plan_ready       = Signal(object)           # ActionPlan
    apply_completed  = Signal(object)           # OrganizerResult
    undo_completed   = Signal(int, int)         # succeeded, failed
    error_occurred   = Signal(str)              # message

    def __init__(
        self,
        db_manager=None,
        delete_empty : bool = True,
        merge_similar: bool = True,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._db           = db_manager
        self.delete_empty  = delete_empty
        self.merge_similar = merge_similar
        self._undo_stack   = UndoStack(db_manager=db_manager)
        self._current_plan : Optional[ActionPlan] = None

    # ── pipeline entry point ──────────────────────────────────────────────────

    def build_plan(
        self,
        files   : Sequence[FileInfo],
        root_dir: Path,
    ) -> ActionPlan:
        """
        Build an ActionPlan from classified FileInfo objects and cache it.
        Emits plan_ready so the GUI can display the plan for confirmation.

        Call this from a worker thread.
        """
        planner = Planner(
            root_dir      = root_dir,
            delete_empty  = self.delete_empty,
            merge_similar = self.merge_similar,
        )
        plan = planner.build_plan(files)
        self._current_plan = plan
        self.plan_ready.emit(plan)
        return plan

    # ── execution ─────────────────────────────────────────────────────────────

    def apply_plan(self, plan: Optional[ActionPlan] = None) -> OrganizerResult:
        """
        Execute every PENDING action in the plan.

        If *plan* is None, uses the most recently built plan.
        Emits progress_updated after each item and apply_completed when done.

        Safe to call from a QThread worker.
        """
        if plan is None:
            plan = self._current_plan
        if plan is None or not plan.items:
            result = OrganizerResult()
            self.apply_completed.emit(result)
            return result

        total     = sum(1 for i in plan if i.status == ActionStatus.PENDING)
        current   = 0
        succeeded = 0
        failed    = 0
        skipped   = 0
        errors    : list[str] = []

        logger.info(
            "Organizer: applying plan %s  (%d actions)",
            plan.session_id, total,
        )

        for item in plan:
            if item.status != ActionStatus.PENDING:
                skipped += 1
                continue

            try:
                self._execute_item(item)
                item.status = ActionStatus.APPLIED
                self._db_write(item)
                succeeded += 1
            except Exception as exc:
                item.status = ActionStatus.FAILED
                item.error  = str(exc)
                self._db_write(item, status_override="failed")
                failed += 1
                msg = f"{item.display_type} failed: {item.source.name} — {exc}"
                errors.append(msg)
                self.error_occurred.emit(msg)
                logger.error("Organizer: %s", msg)

            current += 1
            self.progress_updated.emit(current, total)

        # Only push to undo stack if at least some actions succeeded
        if succeeded > 0:
            self._undo_stack.push(plan)

        result = OrganizerResult(
            succeeded  = succeeded,
            failed     = failed,
            skipped    = skipped,
            session_id = plan.session_id,
            errors     = errors,
        )
        logger.info("Organizer: %r", result)
        self.apply_completed.emit(result)
        return result

    # ── undo ──────────────────────────────────────────────────────────────────

    def undo_last(self) -> tuple[int, int]:
        """
        Physically reverse the most recently applied session.
        Emits undo_completed(succeeded, failed).
        """
        if not self._undo_stack.can_undo():
            self.error_occurred.emit("Nothing to undo.")
            self.undo_completed.emit(0, 0)
            return 0, 0

        try:
            succeeded, failed = self._undo_stack.undo_last()
        except UndoError as exc:
            self.error_occurred.emit(str(exc))
            self.undo_completed.emit(0, 0)
            return 0, 0

        self.undo_completed.emit(succeeded, failed)
        return succeeded, failed

    # ── state helpers ─────────────────────────────────────────────────────────

    def can_undo(self) -> bool:
        return self._undo_stack.can_undo()

    def undo_depth(self) -> int:
        return self._undo_stack.depth

    def set_options(self, delete_empty: bool, merge_similar: bool) -> None:
        """Allow the GUI Settings view to update options at runtime."""
        self.delete_empty  = delete_empty
        self.merge_similar = merge_similar

    # ── item execution ────────────────────────────────────────────────────────

    def _execute_item(self, item: ActionItem) -> None:
        match item.action_type:
            case ActionType.MOVE:
                self._exec_move(item)
            case ActionType.DELETE_EMPTY:
                self._exec_delete_empty(item)
            case ActionType.MERGE_FOLDER:
                self._exec_merge_folder(item)
            case _:
                raise ValueError(f"Unknown ActionType: {item.action_type}")

    def _exec_move(self, item: ActionItem) -> None:
        src = item.source
        dst = item.destination

        if not src.exists():
            raise FileNotFoundError(f"Source not found: {src}")

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        logger.debug("Organizer: MOVE  %s → %s", src.name, dst)

    def _exec_delete_empty(self, item: ActionItem) -> None:
        folder = item.source

        if not folder.exists():
            logger.debug("Organizer: DELETE_EMPTY – already gone: %s", folder)
            item.status = ActionStatus.SKIPPED
            return

        # Safety check: only delete if genuinely empty
        contents = list(folder.iterdir())
        if contents:
            raise OSError(
                f"Refused to delete non-empty folder: {folder}  "
                f"({len(contents)} items remain)"
            )

        folder.rmdir()
        logger.debug("Organizer: DELETE_EMPTY  %s", folder)

    def _exec_merge_folder(self, item: ActionItem) -> None:
        src_dir = item.source
        dst_dir = item.destination

        if not src_dir.exists():
            raise FileNotFoundError(f"Source folder not found: {src_dir}")
        if dst_dir is None:
            raise ValueError("MERGE_FOLDER item has no destination.")

        dst_dir.mkdir(parents=True, exist_ok=True)

        moved: list[str] = []
        for child in list(src_dir.iterdir()):
            if child.is_file():
                dest_file = dst_dir / child.name
                # Collision guard
                if dest_file.exists():
                    stem    = child.stem
                    suffix  = child.suffix
                    counter = 1
                    while dest_file.exists():
                        dest_file = dst_dir / f"{stem}_{counter}{suffix}"
                        counter  += 1

                shutil.move(str(child), str(dest_file))
                moved.append(dest_file.name)  # record the final name used
                logger.debug("Organizer: MERGE  %s → %s", child.name, dest_file)

        # Rewrite reason with the actual manifest so UndoStack can reverse it
        item.reason = (
            f"Merged {len(moved)} file(s) from {src_dir.name}: "
            + "|".join(moved)
        )

        # Remove the now-empty source folder
        try:
            remaining = list(src_dir.iterdir())
            if not remaining:
                src_dir.rmdir()
                logger.debug("Organizer: MERGE removed empty source dir %s", src_dir)
            else:
                logger.warning(
                    "Organizer: source dir '%s' not empty after merge "
                    "(%d sub-items remain – sub-directories are not merged).",
                    src_dir, len(remaining),
                )
        except Exception as exc:
            logger.warning("Organizer: could not remove source dir '%s' – %s", src_dir, exc)

    # ── DB persistence ────────────────────────────────────────────────────────

    def _db_write(self, item: ActionItem, status_override: Optional[str] = None) -> None:
        """Insert or update the history row for this action."""
        if self._db is None:
            return
        status = status_override or item.status.value
        try:
            with self._db.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO history
                        (action_id, session_id, action_type, source, destination,
                         category, reason, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(action_id) DO UPDATE SET status = excluded.status
                    """,
                    (
                        item.action_id,
                        item.session_id,
                        item.action_type.name,
                        str(item.source),
                        str(item.destination) if item.destination else None,
                        item.category,
                        item.reason,
                        status,
                    ),
                )
        except Exception as exc:
            logger.warning(
                "Organizer: DB write failed for action %s – %s",
                item.action_id, exc,
            )