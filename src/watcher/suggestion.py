"""
DesktopAI
Watch Suggestion

Represents a single AI-generated suggestion produced for a file
that was just detected by the FolderWatcher: what category it
looks like, and where it might belong. This is a suggestion only
— nothing in this module ever moves or renames a file.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class WatchSuggestion:
    """A suggested category and destination for a newly detected file."""

    path: Path
    category: str | None
    suggested_folder: str | None
    detected_at: datetime