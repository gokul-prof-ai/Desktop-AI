"""Tests for the DesktopAI v2 FileService facade.

These tests verify the FileService against its ACTUAL contract:
- service._organizer is an Organizer instance (owns the Planner internally)
- Organizer.apply_plan() returns an OrganizerResult (succeeded/failed/skipped/session_id/errors)
- Organizer.undo_last() returns a (succeeded, failed) tuple
- Session identifiers are called "session_id" (not batch_id)
- The undo stack is private (_undo_stack) — accessed via Organizer's public API
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services.file_service import FileService
from domain.organizer.action import ActionItem, ActionPlan, ActionStatus, ActionType
from domain.organizer.organizer import OrganizerResult


@pytest.fixture
def service() -> FileService:
    """Return a FileService without opening the real database."""
    return FileService()


# ── Passing tests (unchanged) ─────────────────────────────────────────────────


def test_open_and_close_delegate_to_database(service: FileService) -> None:
    with patch("services.file_service.DB") as db:
        service.open()
        service.close()
        db.connect.assert_called_once_with()
        db.close.assert_called_once_with()


def test_scan_folder_returns_plain_dicts_and_reports_progress(service: FileService, tmp_path: Path) -> None:
    file_info = MagicMock(
        path=tmp_path / "invoice.pdf",
        filename="invoice.pdf",
        extension=".pdf",
        size_bytes=128,
    )
    result = MagicMock(
        file_info=file_info,
        category="Finance",
        confidence=0.95,
        method="fast_rule",
        skipped=False,
        skip_reason=None,
    )
    progress: list[tuple[int, str]] = []

    with patch.object(service._scanner, "scan", return_value=[file_info]), patch(
        "services.file_service.FileClassifier"
    ) as classifier_cls:
        classifier_cls.return_value.classify_batch.return_value = [result]
        output = service.scan_folder(
            tmp_path,
            progress_callback=lambda percent, message: progress.append((percent, message)),
        )

    assert output == [
        {
            "path": str(file_info.path),
            "filename": "invoice.pdf",
            "extension": ".pdf",
            "size_bytes": 128,
            "category": "Finance",
            "confidence": 0.95,
            "method": "fast_rule",
            "skipped": False,
            "skip_reason": None,
        }
    ]
    assert progress[0][0] == 0
    assert progress[-1] == (100, "Scan complete.")
    assert service._last_scan_results == [result]


def test_scan_folder_empty_directory_clears_previous_cache(service: FileService, tmp_path: Path) -> None:
    service._last_scan_results = [MagicMock()]
    with patch.object(service._scanner, "scan", return_value=[]):
        assert service.scan_folder(tmp_path) == []
    assert service._last_scan_results == []


def test_plan_organisation_requires_scan_results(service: FileService, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No scan results available"):
        service.plan_organisation(tmp_path / "Organized")


def test_search_rejects_blank_queries(service: FileService) -> None:
    with patch("services.file_service.semantic_search") as semantic_search:
        assert service.search("   ") == []
        semantic_search.assert_not_called()


def test_search_returns_plain_dicts(service: FileService) -> None:
    result = MagicMock(path=Path("/docs/invoice.pdf"), score=0.87654)
    with patch("services.file_service.semantic_search", return_value=[result]) as semantic_search:
        output = service.search("finance invoice", top_k=5)
    semantic_search.assert_called_once_with("finance invoice", top_k=5)
    assert output == [{"path": str(result.path), "score": 0.8765}]


def test_build_index_success_reports_progress(service: FileService) -> None:
    progress: list[tuple[int, str]] = []
    with patch("services.file_service.build_search_index", return_value=4) as build_index:
        output = service.build_index(
            files=[],
            progress_callback=lambda percent, message: progress.append((percent, message)),
        )
    build_index.assert_called_once()
    assert output == {"indexed": 4, "error": None}
    assert progress[0] == (0, "Building search index…")
    assert progress[-1] == (100, "Indexed 4 file(s).")


def test_build_index_converts_errors_to_result(service: FileService) -> None:
    with patch("services.file_service.build_search_index", side_effect=RuntimeError("index failed")):
        output = service.build_index()
    assert output == {"indexed": 0, "error": "index failed"}


def test_get_memory_stats_returns_database_and_memory_data(service: FileService) -> None:
    preferences = [{"pattern": ".pdf", "value": "/Finance"}]
    db_stats = {
        "total_files": 10,
        "total_operations": 7,
        "categories": {"Finance": 6},
        "recent_sessions": [{"id": "session-1"}],
    }
    with patch("services.file_service.MemoryStore") as memory_store, patch(
        "services.file_service.DB"
    ) as db:
        memory_store.get_all.return_value = preferences
        db.get_stats.return_value = db_stats
        output = service.get_memory_stats()
    assert output == {
        "preferences": preferences,
        "total_files": 10,
        "total_operations": 7,
        "categories": {"Finance": 6},
        "recent_sessions": [{"id": "session-1"}],
    }


# ── Fixed tests (now match the actual service contract) ───────────────────────


def test_plan_organisation_uses_cached_scan(service: FileService, tmp_path: Path) -> None:
    """plan_organisation reads cached scan results and delegates to Organizer.build_plan."""
    file_info = MagicMock(
        path=tmp_path / "report.pdf",
        filename="report.pdf",
        extension=".pdf",
        size_bytes=256,
    )
    cached_result = MagicMock(file_info=file_info, skipped=False)
    service._last_scan_results = [cached_result]

    # Build a real ActionPlan with a real ActionItem so _action_item_to_dict works
    plan = ActionPlan()
    plan.items.append(
        ActionItem(
            action_type=ActionType.MOVE,
            source=file_info.path,
            destination=tmp_path / "Finance" / "report.pdf",
            category="Finance",
            reason="Classified as 'Finance'",
        )
    )

    with patch.object(service._organizer, "build_plan", return_value=plan) as build_plan:
        output = service.plan_organisation(tmp_path / "Organized")

    build_plan.assert_called_once()
    # First arg is the list of FileInfo objects
    files_arg, root_kwarg = build_plan.call_args[0][0], build_plan.call_args.kwargs["root_dir"]
    assert len(files_arg) == 1
    assert root_kwarg == tmp_path / "Organized"

    assert output[0]["action_type"] == "MOVE"
    assert output[0]["source"] == str(file_info.path)
    assert output[0]["destination"] == str(tmp_path / "Finance" / "report.pdf")
    assert output[0]["category"] == "Finance"


def test_apply_plan_returns_session_id_and_tracks_latest_plan(service: FileService, tmp_path: Path) -> None:
    """apply_plan delegates to Organizer and surfaces OrganizerResult as a plain dict."""
    source = tmp_path / "invoice.pdf"
    destination = tmp_path / "Finance" / "invoice.pdf"
    source.write_text("invoice", encoding="utf-8")

    # Seed a cached plan on the Organizer (this is what plan_organisation does)
    plan = ActionPlan()
    plan.items.append(
        ActionItem(
            action_type=ActionType.MOVE,
            source=source,
            destination=destination,
            category="Finance",
        )
    )
    service._organizer._current_plan = plan

    fake_result = OrganizerResult(
        succeeded=1, failed=0, skipped=0, session_id="session-abc", errors=[],
    )

    with patch.object(
        service._organizer, "apply_plan", return_value=fake_result,
    ) as apply_plan:
        output = service.apply_plan()

    apply_plan.assert_called_once()
    assert output["success"] == 1
    assert output["failed"] == 0
    assert output["skipped"] == 0
    assert output["session_id"] == "session-abc"
    assert output["errors"] == []


def test_apply_plan_empty_plan_is_noop(service: FileService) -> None:
    """apply_plan with an empty cached plan returns an all-zero result."""
    service._organizer._current_plan = ActionPlan()

    fake_result = OrganizerResult()  # all zeros, empty session_id, no errors
    with patch.object(service._organizer, "apply_plan", return_value=fake_result):
        output = service.apply_plan()

    assert output == {
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "session_id": "",
        "errors": [],
    }


def test_undo_last_uses_organizer_undo(service: FileService) -> None:
    """undo_last delegates to Organizer.undo_last() (stack is private)."""
    # Seed the Organizer's private undo stack so can_undo is truthy
    plan = ActionPlan()
    plan.session_id = "session-123"
    service._organizer._undo_stack.push(plan)

    with patch.object(
        service._organizer, "undo_last", return_value=(2, 0),
    ) as undo_last:
        output = service.undo_last()

    undo_last.assert_called_once()
    assert output == {"reversed": 2, "failed": 0, "error": None}


def test_undo_last_without_batch_returns_safe_error(service: FileService) -> None:
    """When Organizer.undo_last reports nothing to reverse, FileService surfaces it safely."""
    # Stack is empty → Organizer returns (0, 0)
    with patch.object(service._organizer, "undo_last", return_value=(0, 0)):
        output = service.undo_last()

    assert output["reversed"] == 0
    assert output["error"] is None  # no exception, just nothing reversed