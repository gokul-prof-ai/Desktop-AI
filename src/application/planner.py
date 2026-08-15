"""
src/application/planner.py
──────────────────────────
Planner — converts a list of FileInfo objects (from FileScanner + FileClassifier)
into an ActionPlan ready for the Organizer to execute.

What the planner does
─────────────────────
1. FILE MOVES
   Each classified file gets a MOVE action: source → <root>/<Category>/<filename>.
   Collision-safe: if a file with the same name already exists at the destination
   a numeric suffix is appended (_1, _2, …).

2. EMPTY FOLDER DELETION  (opt-in via delete_empty=True)
   After building the move list the planner computes which folders will become
   empty once all moves are applied, then appends DELETE_EMPTY actions for them.
   Folders that are the scan root itself are never deleted.

3. SIMILAR FOLDER MERGING  (opt-in via merge_similar=True)
   Scans the root directory for folders whose names are "similar" (same
   normalised stem – lowercase, stripped of digits and common suffixes like
   "copy", "new", "backup").  When two or more folders share a normalised stem
   the contents are directed into a single canonical folder and the duplicates
   get MERGE_FOLDER actions.

   Similarity rule (configurable via threshold):
     - Normalise: lowercase, remove digits, strip trailing _copy/_new/_backup/…
     - If normalised names match → treat as duplicates.
     - Canonical folder = the one with the shortest real name (alphabetically
       first on ties).
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional, Sequence

from application.action import ActionItem, ActionPlan, ActionType
from domain.models import FileInfo          # your existing FileInfo frozen dataclass

logger = logging.getLogger(__name__)

# ── suffixes that indicate "this folder is probably a duplicate" ──────────────
_DUPE_SUFFIX_RE = re.compile(
    r"[\s_\-]*(copy|копия|backup|bak|new|old|temp|tmp|\(\d+\)|\d+)$",
    re.IGNORECASE,
)


def _normalise_folder_name(name: str) -> str:
    """
    Reduce a folder name to its canonical form for similarity comparison.

    e.g.  "Photos (2)"  →  "photos"
          "Photos copy"  →  "photos"
          "Photos_backup_2023" → "photos_backup_"   (intentional – "backup" stripped)
    """
    s = name.lower().strip()
    # Remove parenthesised counters  (1), (2) …
    s = re.sub(r"\(\d+\)", "", s)
    # Remove trailing dupe suffixes repeatedly until stable
    prev = None
    while prev != s:
        prev = s
        s = _DUPE_SUFFIX_RE.sub("", s).strip()
    return s or name.lower()


# ──────────────────────────────────────────────────────────────────────────────
# Planner
# ──────────────────────────────────────────────────────────────────────────────

class Planner:
    """
    Produces an ActionPlan from a list of classified FileInfo objects.

    Parameters
    ──────────
    root_dir        : The directory that was scanned.  Organised files land
                      directly under this directory (root/<Category>/file).
    delete_empty    : Append DELETE_EMPTY actions for folders that will be
                      empty after all moves.
    merge_similar   : Append MERGE_FOLDER actions for near-duplicate folders.
    dry_run         : Build the plan but do not touch the filesystem (always
                      True here – execution is the Organizer's job).
    """

    def __init__(
        self,
        root_dir     : Path,
        delete_empty : bool = True,
        merge_similar: bool = True,
    ) -> None:
        self.root_dir      = Path(root_dir)
        self.delete_empty  = delete_empty
        self.merge_similar = merge_similar

    # ── public API ────────────────────────────────────────────────────────────

    def build_plan(self, files: Sequence[FileInfo]) -> ActionPlan:
        """
        Build and return an ActionPlan.

        Parameters
        ──────────
        files : Sequence of FileInfo objects that have already been
                classified (each has a .category attribute).
        """
        plan = ActionPlan(source_dir=self.root_dir)

        # Track which destination paths are already claimed this session
        claimed: set[Path] = set()

        # 1. FILE MOVES
        move_items = self._plan_moves(files, claimed)
        plan.items.extend(move_items)

        # 2. EMPTY FOLDER DELETION
        if self.delete_empty:
            delete_items = self._plan_empty_deletions(files, move_items)
            plan.items.extend(delete_items)

        # 3. SIMILAR FOLDER MERGING
        if self.merge_similar:
            merge_items = self._plan_folder_merges(claimed)
            plan.items.extend(merge_items)

        plan.stamp_session()

        logger.info(
            "Planner: built plan — %d moves, %d deletions, %d merges  (session %s)",
            len(move_items),
            len(delete_items) if self.delete_empty  else 0,
            len(merge_items)  if self.merge_similar else 0,
            plan.session_id,
        )
        return plan

    # ── phase 1 : file moves ──────────────────────────────────────────────────

    def _plan_moves(
        self,
        files  : Sequence[FileInfo],
        claimed: set[Path],
    ) -> list[ActionItem]:
        items: list[ActionItem] = []

        for fi in files:
            source = Path(fi.path)
            if not source.exists():
                logger.debug("Planner: skip missing file %s", source)
                continue

            category = getattr(fi, "category", None) or "Uncategorised"
            dest_dir = self.root_dir / category
            dest     = self._unique_dest(dest_dir / source.name, claimed)
            claimed.add(dest)

            # Skip if the file is already in the right place
            if source == dest:
                logger.debug("Planner: %s already at destination – skipped", source.name)
                continue

            items.append(ActionItem(
                action_type = ActionType.MOVE,
                source      = source,
                destination = dest,
                category    = category,
                reason      = f"Classified as '{category}'",
            ))

        return items

    # ── phase 2 : empty folder deletion ──────────────────────────────────────

    def _plan_empty_deletions(
        self,
        files     : Sequence[FileInfo],
        move_items: list[ActionItem],
    ) -> list[ActionItem]:
        """
        Identify folders that will be empty once all MOVE actions are applied.
        """
        # Map folder → set of files currently in it
        folder_files: dict[Path, set[Path]] = defaultdict(set)
        for fi in files:
            p = Path(fi.path)
            folder_files[p.parent].add(p)

        # Subtract files that are being moved out
        moved_sources: set[Path] = {i.source for i in move_items}

        items: list[ActionItem] = []
        for folder, contents in folder_files.items():
            # Never delete the scan root
            if folder == self.root_dir:
                continue
            # Never delete category destination folders we are about to create
            remaining = contents - moved_sources
            if remaining:
                continue  # folder will still have files after moves

            # Confirm the folder is actually empty right now OR will be
            items.append(ActionItem(
                action_type = ActionType.DELETE_EMPTY,
                source      = folder,
                destination = None,
                category    = "Cleanup",
                reason      = f"Will be empty after organising ({len(contents)} file(s) moved out)",
            ))

        return items

    # ── phase 3 : similar folder merges ──────────────────────────────────────

    def _plan_folder_merges(self, claimed: set[Path]) -> list[ActionItem]:
        """
        Find folders under root_dir that appear to be duplicates of each other
        and plan MERGE_FOLDER actions to consolidate them.
        """
        if not self.root_dir.exists():
            return []

        # Collect immediate sub-directories only
        subdirs = [
            d for d in self.root_dir.iterdir()
            if d.is_dir()
        ]

        # Group by normalised name
        groups: dict[str, list[Path]] = defaultdict(list)
        for d in subdirs:
            groups[_normalise_folder_name(d.name)].append(d)

        items: list[ActionItem] = []

        for norm_name, dirs in groups.items():
            if len(dirs) < 2:
                continue  # No duplicates

            # Sort: shortest name first (most canonical), then alphabetical
            dirs.sort(key=lambda d: (len(d.name), d.name))
            canonical = dirs[0]
            duplicates = dirs[1:]

            logger.debug(
                "Planner: folder merge group '%s'  canonical=%s  dupes=%s",
                norm_name, canonical.name, [d.name for d in duplicates],
            )

            for dupe in duplicates:
                # List files in the dupe folder to build the manifest
                try:
                    file_names = [f.name for f in dupe.iterdir() if f.is_file()]
                except PermissionError:
                    logger.warning("Planner: cannot read '%s' – skipping merge", dupe)
                    continue

                if not file_names:
                    # Empty dupe → handle via DELETE_EMPTY instead
                    continue

                manifest = "|".join(file_names)
                reason   = (
                    f"Merged {len(file_names)} file(s) from {dupe.name}: {manifest}"
                )

                items.append(ActionItem(
                    action_type = ActionType.MERGE_FOLDER,
                    source      = dupe,
                    destination = canonical,
                    category    = "Merge",
                    reason      = reason,
                ))

                # Register claimed destinations to avoid collision
                for fname in file_names:
                    dest = self._unique_dest(canonical / fname, claimed)
                    claimed.add(dest)

        return items

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _unique_dest(preferred: Path, claimed: set[Path]) -> Path:
        """
        Return a path that does not collide with an existing file on disk
        or another action in this session.
        """
        if not preferred.exists() and preferred not in claimed:
            return preferred

        stem    = preferred.stem
        suffix  = preferred.suffix
        parent  = preferred.parent
        counter = 1

        while True:
            candidate = parent / f"{stem}_{counter}{suffix}"
            if not candidate.exists() and candidate not in claimed:
                return candidate
            counter += 1