from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class FileInfo:
    """Stores metadata about a discovered file."""

    name: str
    path: Path
    extension: str
    size: int
    created: datetime
    modified: datetime
    file_hash: str | None = None