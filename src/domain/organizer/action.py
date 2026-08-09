"""
DesktopAI v2.0 — Organization Action
File: src/domain/organizer/action.py
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class OrganizationAction:
    """One file operation. Created by Planner, executed by Organizer, reversed by UndoStack."""
    action_type: str                      # 'move' | 'copy' | 'rename'
    source_path: Path
    planned_target_path: Path
    category: str
    confidence: float
    actual_target_path: Optional[Path] = None
    history_id: Optional[int] = None
    is_reversed: bool = False
    error_message: Optional[str] = None

    @property
    def is_move(self) -> bool:
        return self.action_type == "move"

    @property
    def is_success(self) -> bool:
        return self.error_message is None and self.actual_target_path is not None

    @property
    def is_failed(self) -> bool:
        return self.error_message is not None

    @property
    def source_filename(self) -> str:
        return self.source_path.name

    def mark_success(self, actual_path: Path, history_id: int) -> None:
        self.actual_target_path = actual_path
        self.history_id = history_id
        self.error_message = None

    def mark_failed(self, error: str) -> None:
        self.error_message = error

    def mark_reversed(self) -> None:
        self.is_reversed = True