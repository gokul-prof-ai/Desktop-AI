"""Tests for the DesktopAI v2 FileService facade."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services.file_service import FileService


@pytest.fixture
def service() -> FileService:
    """Return a FileService without opening the real database."""
    return FileService()


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


def test_plan_organisation_uses_cached_scan(service: FileService, tmp_path: Path) -> None:
    file_info = MagicMock(
        path=tmp_path / "report.pdf",
        filename="report.pdf",
        extension=".pdf",
        size_bytes=256,
    )
    cached_result = MagicMock(file_info=file_info, skipped=False)
    action = MagicMock(
        action_type="move",
        source_path=file_info.path,
        planned_target_path=tmp_path / "Finance" / "report.pdf",
        actual_target_path=None,
        category="Finance",
        confidence=0.95,
        is_success=False,
        is_failed=False,
        is_reversed=False,
        error_message=None,
    )
    service._last_scan_results = [cached_result]

    with patch.object(service._planner, "create_plan", return_value=[action]) as create_plan:
        output = service.plan_organisation(tmp_path / "Organized")

    create_plan.assert_called_once_with([file_info], tmp_path / "Organized")
    assert output[0]["action_type"] == "move"
    assert output[0]["source"] == str(file_info.path)
    assert output[0]["category"] == "Finance"
    assert output[0]["confidence"] == 0.95


def test_plan_organisation_requires_scan_results(service: FileService, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No scan results available"):
        service.plan_organisation(tmp_path / "Organized")


def test_apply_plan_returns_batch_id_and_tracks_latest_batch(service: FileService, tmp_path: Path) -> None:
    source = tmp_path / "invoice.pdf"
    destination = tmp_path / "Finance" / "invoice.pdf"
    source.write_text("invoice", encoding="utf-8")

    plan = [
        {
            "action_type": "move",
            "source": str(source),
            "destination": str(destination),
            "category": "Finance",
            "confidence": 0.95,
        }
    ]

    with patch.object(
        service._organizer,
        "execute_plan",
        return_value={"success": 1, "failed": 0, "skipped": 0},
    ) as execute_plan:
        output = service.apply_plan(plan)

    assert output["success"] == 1
    assert output["failed"] == 0
    assert output["skipped"] == 0
    assert output["batch_id"]
    assert service._last_batch_id == output["batch_id"]
    execute_plan.assert_called_once()


def test_apply_plan_empty_plan_is_noop(service: FileService) -> None:
    assert service.apply_plan([]) == {
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "batch_id": None,
    }


def test_undo_last_uses_latest_batch(service: FileService) -> None:
    service._last_batch_id = "batch-123"

    with patch.object(service._organizer.undo_stack, "undo_batch", return_value=2) as undo_batch:
        output = service.undo_last()

    undo_batch.assert_called_once_with("batch-123")
    assert output == {
        "reversed": 2,
        "batch_id": "batch-123",
        "error": None,
    }
    assert service._last_batch_id is None


def test_undo_last_without_batch_returns_safe_error(service: FileService) -> None:
    assert service.undo_last() == {
        "reversed": 0,
        "batch_id": None,
        "error": "No batch to undo.",
    }


def test_search_rejects_blank_queries(service: FileService) -> None:
    with patch("services.file_service.semantic_search") as semantic_search:
        assert service.search("   ") == []
        semantic_search.assert_not_called()


def test_search_returns_plain_dicts(service: FileService) -> None:
    result = MagicMock(path=Path("/docs/invoice.pdf"), score=0.87654)

    with patch("services.file_service.semantic_search", return_value=[result]) as semantic_search:
        output = service.search("finance invoice", top_k=5)

    semantic_search.assert_called_once_with("finance invoice", top_k=5)
    assert output == [{"path": "/docs/invoice.pdf", "score": 0.8765}]


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

    with patch.object(service._organizer, "execute_plan"):
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
