"""
src/application/action.py
─────────────────────────
ActionType enum + ActionItem dataclass.
Every filesystem mutation the Organizer can perform is described by one
ActionItem.  The Executor (inside organizer.py) reads these and applies
them; the UndoStack stores them so they can be reversed.

Supported operations
────────────────────
MOVE            – move a file to a new location (includes rename)
DELETE_EMPTY    – delete a folder that is (or has become) empty
MERGE_FOLDER    – merge one folder's contents into another, then remove source
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────

class ActionType(Enum):
    MOVE         = auto()   # Move / rename a file
    DELETE_EMPTY = auto()   # Delete an empty directory
    MERGE_FOLDER = auto()   # Move all files from src_dir → dst_dir, delete src_dir


class ActionStatus(Enum):
    PENDING   = "pending"
    APPLIED   = "applied"
    UNDONE    = "undone"
    FAILED    = "failed"
    SKIPPED   = "skipped"


# ──────────────────────────────────────────────────────────────────────────────
# ActionItem
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ActionItem:
    """
    Describes a single atomic filesystem operation.

    Fields
    ──────
    action_id   : Unique identifier (auto-generated UUID4 hex).
    action_type : What kind of operation this is.
    source      : The file or directory that will be moved / deleted.
    destination : Where it should end up (None for DELETE_EMPTY).
    category    : Human-readable label ("Documents", "Images", …).
    reason      : Why the planner chose this action.
    status      : Current lifecycle state.
    error       : Set if execution failed.
    session_id  : Groups actions that were applied together.
    """

    action_type : ActionType
    source      : Path
    destination : Optional[Path]        = None
    category    : str                   = ""
    reason      : str                   = ""
    status      : ActionStatus          = ActionStatus.PENDING
    error       : Optional[str]         = None
    session_id  : Optional[str]         = None
    action_id   : str                   = field(default_factory=lambda: uuid.uuid4().hex)

    # ── derived helpers ───────────────────────────────────────────────────────

    @property
    def is_reversible(self) -> bool:
        """True when the action can be undone (always, unless it failed)."""
        return self.status == ActionStatus.APPLIED

    @property
    def display_source(self) -> str:
        return str(self.source)

    @property
    def display_destination(self) -> str:
        return str(self.destination) if self.destination else "—"

    @property
    def display_type(self) -> str:
        return {
            ActionType.MOVE:         "Move",
            ActionType.DELETE_EMPTY: "Delete Empty Folder",
            ActionType.MERGE_FOLDER: "Merge Folder",
        }.get(self.action_type, "Unknown")

    def __str__(self) -> str:
        return (
            f"[{self.display_type}] {self.source.name}"
            + (f" → {self.destination}" if self.destination else "")
            + f" ({self.status.value})"
        )


# ──────────────────────────────────────────────────────────────────────────────
# ActionPlan  (thin container – carries a list of ActionItems + metadata)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ActionPlan:
    """
    A complete plan produced by the Planner and consumed by the Organizer.

    items       : Ordered list of ActionItems to execute.
    session_id  : Shared identifier stamped on every item.
    source_dir  : Root directory that was scanned.
    """

    items      : list[ActionItem]  = field(default_factory=list)
    session_id : str               = field(default_factory=lambda: uuid.uuid4().hex)
    source_dir : Optional[Path]    = None

    # ── convenience ──────────────────────────────────────────────────────────

    def stamp_session(self) -> None:
        """Propagate this plan's session_id to every contained item."""
        for item in self.items:
            item.session_id = self.session_id

    @property
    def total(self)   -> int: return len(self.items)
    @property
    def pending(self) -> int: return sum(1 for i in self.items if i.status == ActionStatus.PENDING)
    @property
    def applied(self) -> int: return sum(1 for i in self.items if i.status == ActionStatus.APPLIED)
    @property
    def failed(self)  -> int: return sum(1 for i in self.items if i.status == ActionStatus.FAILED)

    def by_category(self) -> dict[str, list[ActionItem]]:
        """Group items by category label."""
        out: dict[str, list[ActionItem]] = {}
        for item in self.items:
            out.setdefault(item.category, []).append(item)
        return out

    def __len__(self)  -> int: return self.total
    def __iter__(self):        return iter(self.items)
    def __bool__(self) -> bool: return bool(self.items)