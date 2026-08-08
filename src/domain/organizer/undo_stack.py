"""
DesktopAI v2.0 — Undo Stack
File: src/domain/organizer/undo_stack.py

Reliable undo management for file organization operations.

Responsibilities:
    - Track successfully executed organization actions.
    - Associate every action with its execution batch.
    - Undo the most recent action.
    - Undo every action belonging to a specific batch.
    - Reverse move, copy, and rename operations.
    - Protect against accidental overwrites during undo.
    - Handle stale/missing files gracefully.
    - Maintain an in-memory undo history for the current process.

Design goals:
    - No dependency on OrganizationAction.source_filename.
    - Works with the existing OrganizationAction model.
    - Explicit batch tracking.
    - Safe Windows filesystem behavior.
    - Reverse operations in LIFO order.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import shutil

from core.logger import get_logger

from domain.organizer.action import OrganizationAction


logger = get_logger(__name__)


@dataclass(slots=True)
class _UndoEntry:
    """
    Internal undo record.

    We intentionally store the batch_id separately instead of assuming
    OrganizationAction contains a batch_id field.

    This makes UndoStack compatible with older/newer OrganizationAction
    implementations.
    """

    action: OrganizationAction
    batch_id: Optional[str]


class UndoStack:
    """
    In-memory LIFO undo manager for organization actions.

    Each successfully completed action is stored together with the batch
    that produced it.

    Example:

        stack = UndoStack()

        stack.push(action, batch_id="batch-123")

        stack.undo_batch("batch-123")

    The stack is intentionally process-local. Persistent history belongs
    to the database layer.
    """

    def __init__(self) -> None:
        self._entries: list[_UndoEntry] = []

        logger.debug("UndoStack: initialized")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Return the number of undoable actions currently stored."""
        return len(self._entries)

    @property
    def is_empty(self) -> bool:
        """Return True when there are no undoable actions."""
        return not self._entries

    # ------------------------------------------------------------------
    # Push
    # ------------------------------------------------------------------

    def push(
        self,
        action: OrganizationAction,
        batch_id: Optional[str] = None,
    ) -> None:
        """
        Add a successfully executed action to the undo stack.

        Parameters
        ----------
        action:
            OrganizationAction that has already been executed successfully.

        batch_id:
            Batch identifier associated with the operation.

        Important:
            The batch ID is stored by UndoStack itself. We do NOT require
            OrganizationAction to have a batch_id attribute.
        """

        if action is None:
            logger.warning("UndoStack: refusing to push None action")
            return

        entry = _UndoEntry(
            action=action,
            batch_id=batch_id,
        )

        self._entries.append(entry)

        logger.debug(
            "UndoStack: added action — %s | batch=%s | size=%d",
            self._action_name(action),
            batch_id,
            len(self._entries),
        )

    # ------------------------------------------------------------------
    # Undo last action
    # ------------------------------------------------------------------

    def undo_last_action(self) -> bool:
        """
        Undo the most recently executed successful action.

        Returns
        -------
        bool
            True when the action was successfully reversed.
            False otherwise.
        """

        if not self._entries:
            logger.info("UndoStack: nothing to undo")
            return False

        entry = self._entries[-1]

        action = entry.action

        logger.info(
            "UndoStack: undoing last action — %s | batch=%s",
            self._action_name(action),
            entry.batch_id,
        )

        try:
            success = self._reverse_action(action)

        except Exception as exc:
            logger.error(
                "UndoStack: unexpected undo error for %s: %s",
                self._action_name(action),
                exc,
                exc_info=True,
            )
            return False

        if success:
            self._entries.pop()

            logger.info(
                "UndoStack: successfully reversed %s",
                self._action_name(action),
            )

            return True

        logger.warning(
            "UndoStack: failed to reverse %s",
            self._action_name(action),
        )

        return False

    # ------------------------------------------------------------------
    # Undo batch
    # ------------------------------------------------------------------

    def undo_batch(self, batch_id: str) -> int:
        """
        Undo every successful action belonging to a batch.

        Actions are reversed in reverse execution order.

        Example:

            Action A
            Action B

        Undo order:

            B
            A

        This is important because organization operations are inherently
        sequential and LIFO reversal is safest.

        Returns
        -------
        int
            Number of successfully reversed actions.
        """

        if not batch_id:
            logger.warning("UndoStack: cannot undo empty batch ID")
            return 0

        logger.info(
            "UndoStack: reversing batch %s",
            batch_id,
        )

        # Collect matching entries in reverse order without mutating the
        # main list until each action has been successfully reversed.
        matching_entries = [
            entry
            for entry in reversed(self._entries)
            if entry.batch_id == batch_id
        ]

        if not matching_entries:
            logger.info(
                "UndoStack: no actions found for batch %s",
                batch_id,
            )
            return 0

        reversed_count = 0

        for entry in matching_entries:
            action = entry.action

            logger.debug(
                "UndoStack: reversing %s from batch %s",
                self._action_name(action),
                batch_id,
            )

            try:
                success = self._reverse_action(action)

            except Exception as exc:
                logger.error(
                    "UndoStack: failed to reverse %s: %s",
                    self._action_name(action),
                    exc,
                    exc_info=True,
                )
                continue

            if success:
                self._remove_entry(entry)
                reversed_count += 1

                logger.debug(
                    "UndoStack: reversed %s",
                    self._action_name(action),
                )
            else:
                logger.warning(
                    "UndoStack: could not reverse %s",
                    self._action_name(action),
                )

        logger.info(
            "UndoStack: batch %s reversed %d action(s)",
            batch_id,
            reversed_count,
        )

        return reversed_count

    # ------------------------------------------------------------------
    # Core reverse dispatcher
    # ------------------------------------------------------------------

    def _reverse_action(
        self,
        action: OrganizationAction,
    ) -> bool:
        """
        Dispatch an action to its appropriate reverse operation.
        """

        action_type = self._action_type(action)

        if action_type == "move":
            return self._reverse_move(action)

        if action_type == "copy":
            return self._reverse_copy(action)

        if action_type == "rename":
            return self._reverse_rename(action)

        logger.error(
            "UndoStack: unsupported action type: %s",
            action_type,
        )

        return False

    # ------------------------------------------------------------------
    # Reverse MOVE
    # ------------------------------------------------------------------

    def _reverse_move(
        self,
        action: OrganizationAction,
    ) -> bool:
        """
        Reverse a MOVE:

            original/source
                    ↓
                organized

        becomes:

            organized
                    ↓
                original/source
        """

        source = self._source_path(action)
        target = self._target_path(action)

        if source is None or target is None:
            logger.error(
                "UndoStack: invalid move paths for %s",
                self._action_name(action),
            )
            return False

        logger.debug(
            "UndoStack: reversing move %s → %s",
            target,
            source,
        )

        # The moved file must currently exist at target.
        if not target.exists():
            logger.warning(
                "UndoStack: target file no longer exists: %s",
                target,
            )
            return False

        # If the original location has somehow been recreated, do not
        # overwrite it.
        if source.exists():
            logger.warning(
                "UndoStack: original location already exists: %s",
                source,
            )

            safe_source = self._find_safe_restore_path(source)

            logger.info(
                "UndoStack: restoring to conflict-safe path: %s",
                safe_source,
            )

            try:
                safe_source.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                shutil.move(
                    str(target),
                    str(safe_source),
                )

                logger.info(
                    "UndoStack: move reversed with conflict-safe restore: %s",
                    safe_source,
                )

                return True

            except Exception as exc:
                logger.error(
                    "UndoStack: conflict-safe move reversal failed: %s",
                    exc,
                    exc_info=True,
                )

                return False

        try:
            source.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.move(
                str(target),
                str(source),
            )

            logger.info(
                "UndoStack: restored %s",
                source,
            )

            return True

        except PermissionError as exc:
            logger.error(
                "UndoStack: permission denied restoring %s: %s",
                source,
                exc,
            )

            return False

        except OSError as exc:
            logger.error(
                "UndoStack: filesystem error restoring %s: %s",
                source,
                exc,
                exc_info=True,
            )

            return False

    # ------------------------------------------------------------------
    # Reverse COPY
    # ------------------------------------------------------------------

    def _reverse_copy(
        self,
        action: OrganizationAction,
    ) -> bool:
        """
        Reverse a COPY by deleting the copied target.

        The original source remains untouched.
        """

        target = self._target_path(action)

        if target is None:
            logger.error(
                "UndoStack: invalid copy target for %s",
                self._action_name(action),
            )
            return False

        logger.debug(
            "UndoStack: reversing copy → deleting %s",
            target,
        )

        if not target.exists():
            logger.warning(
                "UndoStack: copied target already missing: %s",
                target,
            )
            return False

        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

            logger.info(
                "UndoStack: removed copied file %s",
                target,
            )

            return True

        except PermissionError as exc:
            logger.error(
                "UndoStack: permission denied deleting %s: %s",
                target,
                exc,
            )

            return False

        except OSError as exc:
            logger.error(
                "UndoStack: failed deleting copied target %s: %s",
                target,
                exc,
                exc_info=True,
            )

            return False

    # ------------------------------------------------------------------
    # Reverse RENAME
    # ------------------------------------------------------------------

    def _reverse_rename(
        self,
        action: OrganizationAction,
    ) -> bool:
        """
        Reverse a RENAME by moving the target back to the original path.
        """

        source = self._source_path(action)
        target = self._target_path(action)

        if source is None or target is None:
            logger.error(
                "UndoStack: invalid rename paths for %s",
                self._action_name(action),
            )
            return False

        logger.debug(
            "UndoStack: reversing rename %s → %s",
            target,
            source,
        )

        if not target.exists():
            logger.warning(
                "UndoStack: renamed target no longer exists: %s",
                target,
            )
            return False

        if source.exists():
            logger.warning(
                "UndoStack: original rename path already exists: %s",
                source,
            )

            safe_source = self._find_safe_restore_path(source)

            try:
                safe_source.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                target.rename(safe_source)

                logger.info(
                    "UndoStack: rename restored to conflict-safe path %s",
                    safe_source,
                )

                return True

            except OSError as exc:
                logger.error(
                    "UndoStack: rename conflict recovery failed: %s",
                    exc,
                    exc_info=True,
                )

                return False

        try:
            source.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            target.rename(source)

            logger.info(
                "UndoStack: rename reversed %s",
                source,
            )

            return True

        except PermissionError as exc:
            logger.error(
                "UndoStack: permission denied reversing rename: %s",
                exc,
            )

            return False

        except OSError as exc:
            logger.error(
                "UndoStack: rename reversal failed: %s",
                exc,
                exc_info=True,
            )

            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _source_path(
        action: OrganizationAction,
    ) -> Optional[Path]:
        """
        Safely obtain the original source path.
        """

        value = getattr(action, "source_path", None)

        if value is None:
            return None

        return Path(value)

    @staticmethod
    def _target_path(
        action: OrganizationAction,
    ) -> Optional[Path]:
        """
        Safely obtain the actual target path.

        actual_target_path is preferred because conflict resolution can
        change the final destination.

        planned_target_path is used as a fallback.
        """

        value = getattr(
            action,
            "actual_target_path",
            None,
        )

        if value is None:
            value = getattr(
                action,
                "planned_target_path",
                None,
            )

        if value is None:
            return None

        return Path(value)

    @staticmethod
    def _action_type(
        action: OrganizationAction,
    ) -> str:
        """
        Safely obtain normalized action type.
        """

        value = getattr(
            action,
            "action_type",
            "",
        )

        return str(value).strip().lower()

    @staticmethod
    def _action_name(
        action: OrganizationAction,
    ) -> str:
        """
        Return a human-readable action name without relying on the
        non-existent source_filename property.
        """

        source = getattr(
            action,
            "source_path",
            None,
        )

        if source is not None:
            try:
                return Path(source).name
            except Exception:
                pass

        filename = getattr(
            action,
            "filename",
            None,
        )

        if filename:
            return str(filename)

        return "<unknown file>"

    def _remove_entry(
        self,
        entry: _UndoEntry,
    ) -> None:
        """
        Remove a specific entry from the stack safely.

        We use identity rather than equality so two actions that happen
        to contain identical fields are still treated independently.
        """

        for index, current in enumerate(self._entries):
            if current is entry:
                del self._entries[index]
                return

    @staticmethod
    def _find_safe_restore_path(
        original: Path,
    ) -> Path:
        """
        Find a conflict-free restore path.

        Example:

            invoice.pdf
            invoice_1.pdf
            invoice_2.pdf
        """

        if not original.exists():
            return original

        stem = original.stem
        suffix = original.suffix

        counter = 1

        while True:
            candidate = (
                original.parent
                / f"{stem}_{counter}{suffix}"
            )

            if not candidate.exists():
                return candidate

            counter += 1

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """
        Clear all in-memory undo entries.
        """

        count = len(self._entries)

        self._entries.clear()

        logger.debug(
            "UndoStack: cleared %d action(s)",
            count,
        )

    def get_batch_count(
        self,
        batch_id: str,
    ) -> int:
        """
        Return the number of undoable actions belonging to a batch.
        """

        if not batch_id:
            return 0

        return sum(
            1
            for entry in self._entries
            if entry.batch_id == batch_id
        )

    def get_all_batch_ids(self) -> list[str]:
        """
        Return unique batch IDs currently represented in the stack.
        """

        result: list[str] = []
        seen: set[str] = set()

        for entry in self._entries:
            if entry.batch_id is None:
                continue

            if entry.batch_id in seen:
                continue

            seen.add(entry.batch_id)
            result.append(entry.batch_id)

        return result