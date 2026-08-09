"""
DesktopAI
Tests for the Organizer module.
"""

from organizer.action import OrganizationAction
from organizer.organizer import Organizer


def test_preview_does_not_touch_filesystem(tmp_path):
    """preview() should describe planned moves without moving
    anything or creating any folders."""
    source = tmp_path / "notes.txt"
    source.write_text("hello")
    destination = tmp_path / "Documents" / "notes.txt"

    action = OrganizationAction(source=source, destination=destination)

    organizer = Organizer()
    lines = organizer.preview([action])

    assert len(lines) == 1
    assert "notes.txt" in lines[0]
    assert source.exists()  # file was NOT moved
    assert not destination.exists()  # destination was NOT created
    assert action.status == "pending"  # status untouched by preview


def test_apply_moves_file_successfully(tmp_path):
    """apply() should actually move the file and create the
    destination folder if needed."""
    source = tmp_path / "notes.txt"
    source.write_text("hello")
    destination = tmp_path / "Documents" / "Notes" / "notes.txt"

    action = OrganizationAction(source=source, destination=destination)

    organizer = Organizer()
    organizer.apply([action])

    assert action.status == "moved"
    assert not source.exists()
    assert destination.exists()
    assert destination.read_text() == "hello"


def test_apply_skips_when_destination_already_exists(tmp_path):
    """apply() should never silently overwrite an existing file at
    the destination — it should skip instead."""
    source = tmp_path / "notes.txt"
    source.write_text("new content")

    destination = tmp_path / "Documents" / "notes.txt"
    destination.parent.mkdir()
    destination.write_text("existing content, must not be overwritten")

    action = OrganizationAction(source=source, destination=destination)

    organizer = Organizer()
    organizer.apply([action])

    assert action.status == "skipped"
    assert source.exists()  # original file untouched
    assert destination.read_text() == "existing content, must not be overwritten"


def test_apply_fails_gracefully_when_source_missing(tmp_path):
    """If the source file no longer exists (e.g. deleted between
    scan and apply), apply() should mark it failed, not crash."""
    source = tmp_path / "does_not_exist.txt"
    destination = tmp_path / "Documents" / "does_not_exist.txt"

    action = OrganizationAction(source=source, destination=destination)

    organizer = Organizer()
    organizer.apply([action])  # should not raise

    assert action.status == "failed"


def test_undo_last_restores_moved_file(tmp_path):
    """undo_last() should move a previously-moved file back to its
    original location."""
    source = tmp_path / "notes.txt"
    source.write_text("hello")
    destination = tmp_path / "Documents" / "notes.txt"

    action = OrganizationAction(source=source, destination=destination)

    organizer = Organizer()
    organizer.apply([action])
    assert destination.exists()

    organizer.undo_last()

    assert action.status == "undone"
    assert source.exists()
    assert source.read_text() == "hello"
    assert not destination.exists()


def test_undo_last_only_undoes_successfully_moved_files(tmp_path):
    """Skipped or failed actions should not be part of undo history,
    since nothing was actually moved for them."""
    existing_source = tmp_path / "a.txt"
    existing_source.write_text("content A")
    existing_destination = tmp_path / "Dest" / "a.txt"
    existing_destination.parent.mkdir()
    existing_destination.write_text("already there")

    skipped_action = OrganizationAction(
        source=existing_source, destination=existing_destination
    )

    moved_source = tmp_path / "b.txt"
    moved_source.write_text("content B")
    moved_destination = tmp_path / "Dest" / "b.txt"
    moved_action = OrganizationAction(source=moved_source, destination=moved_destination)

    organizer = Organizer()
    organizer.apply([skipped_action, moved_action])

    assert skipped_action.status == "skipped"
    assert moved_action.status == "moved"

    undone = organizer.undo_last()

    # Only the genuinely moved file should have been undone.
    assert len(undone) == 1
    assert undone[0] is moved_action
    assert moved_source.exists()
    assert existing_source.exists()  # was never moved, still where it was