from dataclasses import dataclass
from pathlib import Path

@dataclass
class OrganizationAction:
    """Represents a planned or completed file move with AI context."""
    source: Path
    destination: Path
    status: str = "pending"  # pending, moved, skipped, failed, undone, failed_undo
    category: str = "Unknown"
    confidence: float = 0.0
    reason: str = ""