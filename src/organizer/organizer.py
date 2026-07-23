"""
DesktopAI
Organizer Module

Moves files into suggested destination folders, with a mandatory
preview step and a full undo system. No file is ever moved without
first appearing in a preview, matching the project's core rule of
requiring user approval before any destructive action.
"""

import shutil
from pathlib import Path

from core.logger import get_logger
from organizer.action import OrganizationAction

logger = get_logger("organizer")


class Organizer:
    """Plans, previews, applies, and undoes file organization moves."""

    def __init__(self):
        # Tracks successfully moved files from the most recent
        # apply() call, so undo_last() knows what to reverse.
        self._history: list[OrganizationAction] = []

    def preview(self, actions: list[OrganizationAction]) -> list[str]:
        """
        Produce a human-readable preview of planned moves. This does
        NOT touch the filesystem at all — it's safe to call any time.

        Args:
            actions (list[OrganizationAction]):
                The planned moves to preview.

        Returns:
            list[str]:
                One readable line per planned move, e.g.
                "notes.txt -> Documents/Notes/notes.txt"
        """

        preview_lines = []
        for action in actions:
            preview_lines.append(f"{action.source.name} -> {action.destination}")

        return preview_lines

    def apply(self, actions: list[OrganizationAction]) -> list[OrganizationAction]:
        """
        Actually perform the file moves. Only call this after the
        user has reviewed preview() output and approved it.

        Each action's `status` is updated in place:
        - "moved":   the file was moved successfully
        - "skipped": a file already exists at the destination, so
                      nothing was moved (never overwrites silently)
        - "failed":  the move could not be completed (e.g. source
                      missing, permission denied)

        Successfully moved files are recorded so undo_last() can
        reverse them later.

        Args:
            actions (list[OrganizationAction]):
                The moves to perform (typically the same list
                previously shown via preview()).

        Returns:
            list[OrganizationAction]:
                The same actions, with each one's status updated.
        """

        for action in actions:
            if not action.source.exists():
                logger.warning("Skipping move, source no longer exists: %s", action.source)
                action.status = "failed"
                continue

            if action.destination.exists():
                logger.warning(
                    "Skipping move, destination already exists: %s", action.destination
                )
                action.status = "skipped"
                continue

            try:
                action.destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(action.source), str(action.destination))
            except OSError as error:
                logger.warning("Failed to move %s: %s", action.source, error)
                action.status = "failed"
                continue

            action.status = "moved"
            self._history.append(action)
            logger.info("Moved %s -> %s", action.source, action.destination)

        return actions

    def undo_last(self) -> list[OrganizationAction]:
        """
        Reverse every successfully moved file from the most recent
        apply() call, moving each one back to its original location.

        Returns:
            list[OrganizationAction]:
                The actions that were undone, each with status
                updated to "undone" (or left as "failed" if the
                reversal itself could not be completed).
        """

        undone_actions: list[OrganizationAction] = []

        while self._history:
            action = self._history.pop()

            if not action.destination.exists():
                logger.warning(
                    "Cannot undo, file no longer at expected location: %s",
                    action.destination,
                )
                action.status = "failed"
                continue

            try:
                action.source.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(action.destination), str(action.source))
            except OSError as error:
                logger.warning("Failed to undo move for %s: %s", action.destination, error)
                action.status = "failed"
                continue

            action.status = "undone"
            undone_actions.append(action)
            logger.info("Undid move: %s -> %s", action.destination, action.source)

        return undone_actions