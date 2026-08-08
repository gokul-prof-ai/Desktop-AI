"""
DesktopAI v2.0 — Organization Action
File: src/domain/organizer/action.py
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class OrganizationAction:
    """
    Represents a single file organization operation.
    """
    action_type: str  # 'move', 'copy', 'rename'
    source_path: Path
    planned_target_path: Path
    category: str
    confidence: float
    
    # Populated during execution
    actual_target_path: Path | None = None
    history_id: int | None = None
    is_reversed: bool = False
    error_message: str | None = None

    @property
    def is_move(self) -> bool:
        return self.action_type == "move"

    @property
    def is_success(self) -> bool:
        return self.error_message is None and self.actual_target_path is not None