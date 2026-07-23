"""
DesktopAI
Organization Action

Represents a single planned or completed file move: where a file
currently is, and where it should go.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class OrganizationAction:
    """A single file move: source path -> destination path."""

    source: Path
    destination: Path
    status: str = "pending"  # pending, moved, skipped, failed, undone