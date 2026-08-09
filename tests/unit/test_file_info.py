"""
DesktopAI v2.0 — Unit tests for FileInfo / AnalysisResult
File: tests/unit/test_file_info.py
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from domain.scanner.file_info import AnalysisResult, FileInfo


def _make_file_info() -> FileInfo:
    return FileInfo(
        path=Path("D:/docs/invoice_jan_2026.pdf"),
        filename="invoice_jan_2026.pdf",
        extension=".pdf",
        size_bytes=204_800,
        modified_at=datetime.now(timezone.utc),
    )


def test_display_size_kb():
    fi = _make_file_info()
    assert fi.display_size == "200.00 KB"


def test_with_category_returns_new_instance():
    fi = _make_file_info()
    enriched = fi.with_category("Finance", 0.94)
    assert enriched is not fi
    assert enriched.category == "Finance"
    assert enriched.confidence == 0.94
    assert enriched.confidence_pct == "94%"
    assert fi.category is None  # original untouched (frozen)


def test_with_category_clamps_confidence():
    fi = _make_file_info()
    assert fi.with_category("Finance", 1.7).confidence == 1.0
    assert fi.with_category("Finance", -0.4).confidence == 0.0


def test_analysis_result_confidence_flags():
    fi = _make_file_info()
    high = AnalysisResult(file_info=fi, category="Finance", confidence=0.9)
    low = AnalysisResult(file_info=fi, category="Misc", confidence=0.3)
    assert high.is_high_confidence
    assert not high.is_low_confidence
    assert low.is_low_confidence