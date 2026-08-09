"""
DesktopAI v2.0 — Unit tests for the 3-stage classifier pipeline
File: tests/unit/test_classifier_pipeline.py
"""
from __future__ import annotations

from pathlib import Path

import pytest

from domain.classifier.classifier import FileClassifier
from domain.scanner.file_info import FileInfo
from infrastructure.ai.gateway import AIGateway
from infrastructure.ai.mock_provider import MockProvider
from infrastructure.config.settings import Settings


@pytest.fixture()
def classifier() -> FileClassifier:
    Settings.load()
    mock = MockProvider(default_response="Documents", delay_ms=0)
    mock.set_response("invoice", "Finance")
    AIGateway.set_provider(mock)
    return FileClassifier()


def _fi(name: str, ext: str) -> FileInfo:
    return FileInfo(
        path=Path(f"D:/docs/{name}"),
        filename=name,
        extension=ext,
        size_bytes=1024,
    )


def test_fast_rule_extension_match(classifier):
    result = classifier.classify(_fi("report.pdf", ".pdf"))
    assert result.method == "fast_rule"
    assert result.category == "PDFs"
    assert result.confidence == 0.95


def test_ai_stage_used_when_no_rule_matches(classifier):
    result = classifier.classify(_fi("zz_mystery.xyz", ".xyz"))
    assert result.method == "ai"
    assert result.category == "Documents"  # MockProvider default


def test_batch_classification_order_preserved(classifier):
    files = [_fi(f"file{i}.pdf", ".pdf") for i in range(3)]
    results = classifier.classify_batch(files)
    assert [r.file_info.filename for r in results] == [f.filename for f in files]
    assert all(r.category == "PDFs" for r in results)