"""
DesktopAI v2.0 — FileInfo Dataclass
File: src/domain/scanner/file_info.py

The fundamental data unit in DesktopAI.

Every file that passes through the system is represented as a FileInfo.
It is created by the Scanner, enriched by the Classifier, and consumed
by the Organizer, Search Engine, and Export Manager.

Design rules:
- FileInfo is IMMUTABLE after creation (frozen=True).
- To enrich a FileInfo (add category, summary, etc.), create a new one
  using dataclasses.replace(file_info, category="Finance").
- No business logic here. Pure data only.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class FileInfo:
    """
    Represents one file on the filesystem.

    Created by: Scanner
    Enriched by: Classifier (adds category, confidence, summary)
    Consumed by: Organizer, SearchEngine, ExportManager

    Attributes:
        path:         Absolute path to the file.
        filename:     File name with extension (e.g. "invoice_jan.pdf").
        extension:    Lowercase file extension (e.g. ".pdf").
        size_bytes:   File size in bytes.
        modified_at:  Last modification time from the filesystem.
        md5_hash:     MD5 hash of file contents (for change detection).
        text_content: Extracted text content (from PDF, DOCX, OCR, etc.).
                      Empty string if not yet extracted or not applicable.
        category:     Category assigned by the classifier (e.g. "Finance").
                      None if not yet classified.
        confidence:   Classifier confidence score from 0.0 to 1.0.
                      None if not yet classified.
        summary:      Short AI-generated summary of the file contents.
                      None if not yet summarized.
    """

    path: Path
    filename: str
    extension: str
    size_bytes: int
    modified_at: datetime | None = None
    md5_hash: str | None = None
    text_content: str = ""
    category: str | None = None
    confidence: float | None = None
    summary: str | None = None

    # ── Computed properties ────────────────────────────────────────────

    @property
    def stem(self) -> str:
        """Filename without extension (e.g. 'invoice_jan' from 'invoice_jan.pdf')."""
        return self.path.stem

    @property
    def parent(self) -> Path:
        """Parent directory of this file."""
        return self.path.parent

    @property
    def size_kb(self) -> float:
        """File size in kilobytes, rounded to 2 decimal places."""
        return round(self.size_bytes / 1024, 2)

    @property
    def size_mb(self) -> float:
        """File size in megabytes, rounded to 2 decimal places."""
        return round(self.size_bytes / (1024 * 1024), 2)

    @property
    def is_classified(self) -> bool:
        """True if this file has been assigned a category."""
        return self.category is not None

    @property
    def has_text(self) -> bool:
        """True if text content was successfully extracted from this file."""
        return bool(self.text_content.strip())

    @property
    def display_size(self) -> str:
        """Human-readable file size (e.g. '1.23 MB', '456.00 KB')."""
        if self.size_bytes >= 1024 * 1024:
            return f"{self.size_mb:.2f} MB"
        return f"{self.size_kb:.2f} KB"

    @property
    def confidence_pct(self) -> str:
        """Confidence as a percentage string (e.g. '94%'). Empty if not classified."""
        if self.confidence is None:
            return ""
        return f"{int(self.confidence * 100)}%"

    def with_category(
        self,
        category: str,
        confidence: float,
    ) -> "FileInfo":
        """
        Return a new FileInfo with category and confidence set.

        This is the V2 replacement for V1's dynamic attribute hack:
            file_info._category = "Finance"   ← V1 (fragile)

        V2 usage:
            classified = file_info.with_category("Finance", 0.94)

        Args:
            category:   The category name (e.g. "Finance").
            confidence: Confidence score from 0.0 to 1.0.

        Returns:
            A new FileInfo instance with the category applied.
            The original FileInfo is unchanged (frozen dataclass).
        """
        import dataclasses
        return dataclasses.replace(
            self,
            category=category,
            confidence=max(0.0, min(1.0, confidence)),
        )

    def with_text(self, text_content: str, summary: str | None = None) -> "FileInfo":
        """
        Return a new FileInfo with extracted text and optional summary.

        Args:
            text_content: The extracted plain text from the file.
            summary:      Optional AI-generated summary.

        Returns:
            A new FileInfo with text_content and summary set.
        """
        import dataclasses
        return dataclasses.replace(
            self,
            text_content=text_content,
            summary=summary,
        )

    def __str__(self) -> str:
        category_str = f" [{self.category} {self.confidence_pct}]" if self.is_classified else ""
        return f"FileInfo({self.filename}{category_str}, {self.display_size})"

    def __repr__(self) -> str:
        return (
            f"FileInfo(path={self.path!r}, "
            f"category={self.category!r}, "
            f"confidence={self.confidence!r})"
        )


@dataclass(frozen=True)
class AnalysisResult:
    """
    The output of the Classifier for a single file.

    This is what V1 tried to express by setting `_category` dynamically
    on FileInfo. V2 wraps it in a proper typed dataclass.

    Attributes:
        file_info:      The enriched FileInfo with category applied.
        category:       The assigned category name.
        confidence:     Confidence score from 0.0 to 1.0.
        method:         How the category was determined.
                        'fast_rule'  — matched a rule in categories.toml
                        'memory'     — matched a user preference in DB
                        'ai'         — classified by the AI model
                        'fallback'   — default when everything else fails
        model_used:     Name of the AI model used (None for non-AI methods).
        skipped:        True if this file was skipped (preference or filter).
        skip_reason:    Why the file was skipped (if skipped=True).
    """

    file_info: FileInfo
    category: str
    confidence: float
    method: str = "ai"
    model_used: str | None = None
    skipped: bool = False
    skip_reason: str | None = None

    @property
    def is_high_confidence(self) -> bool:
        """True if confidence is 80% or above."""
        return self.confidence >= 0.80

    @property
    def is_low_confidence(self) -> bool:
        """True if confidence is below 50% — may need human review."""
        return self.confidence < 0.50

    def __str__(self) -> str:
        if self.skipped:
            return f"AnalysisResult(SKIPPED: {self.skip_reason})"
        return (
            f"AnalysisResult({self.file_info.filename} → "
            f"{self.category} [{int(self.confidence * 100)}%] via {self.method})"
        )