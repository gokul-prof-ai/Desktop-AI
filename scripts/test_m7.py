"""
DesktopAI v2.0 — Milestone 7 Verification Script
File: scripts/test_m7.py
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_SRC))


def main() -> None:
    print("\n" + "=" * 60)
    print("  DesktopAI v2.0 — Milestone 7 Verification")
    print("=" * 60 + "\n")
    
    from core.logger import configure
    configure(debug=True)  # Keep debug on to see planner decisions
    
    from infrastructure.config.settings import Settings
    Settings.load()
    
    from infrastructure.ai.gateway import AIGateway
    from infrastructure.ai.mock_provider import MockProvider
    mock = MockProvider(default_response="Documents", delay_ms=0)
    mock.set_response("invoice", "Finance")
    mock.set_response(".py", "Code")
    AIGateway.set_provider(mock)
    
    from infrastructure.storage.database import DB
    DB.connect()
    
    from infrastructure.storage.memory_store import MemoryStore
    # CRITICAL: Clear any lingering preferences from previous test runs
    # so this test starts with a completely clean state.
    MemoryStore.clear_all()
    
    from domain.scanner.file_info import FileInfo
    from domain.organizer.planner import OrganizationPlanner
    from domain.organizer.organizer import AutoOrganizer
    
    print("Test 1: Planner generates conflict-free actions")
    with tempfile.TemporaryDirectory() as tmpdir:
        base_folder = Path(tmpdir) / "organized"
        
        # Create test files
        file1 = Path(tmpdir) / "invoice_test.pdf"
        file1.write_text("dummy invoice")
        file2 = Path(tmpdir) / "script.py"
        file2.write_text("dummy code")
        
        # Create a pre-existing file to test conflict resolution
        # Note: .pdf files go to "PDFs" category via fast rule
        conflict_file = base_folder / "PDFs" / "invoice_test.pdf"
        conflict_file.parent.mkdir(parents=True, exist_ok=True)
        conflict_file.write_text("existing file")
        
        print(f"  Conflict file created: {conflict_file}")
        print(f"  Conflict file exists: {conflict_file.exists()}")
        
        files = [
            FileInfo(path=file1, filename="invoice_test.pdf", extension=".pdf", size_bytes=13),
            FileInfo(path=file2, filename="script.py", extension=".py", size_bytes=10),
        ]
        
        planner = OrganizationPlanner()
        actions = planner.create_plan(files, base_folder)
        
        print(f"\n  Files processed: {len(files)}")
        print(f"  Actions generated: {len(actions)}")
        for a in actions:
            print(f"    → {a.source_path.name} to {a.planned_target_path.parent.name}/{a.planned_target_path.name} ({a.category})")
        
        assert len(actions) == 2, f"Expected 2 actions, got {len(actions)}"
        
        invoice_action = next(a for a in actions if "invoice" in a.source_path.name)
        print(f"\n  Invoice action target: {invoice_action.planned_target_path.name}")
        print(f"  Expected '_1' in name: {'_1' in invoice_action.planned_target_path.name}")
        
        assert "_1" in invoice_action.planned_target_path.name, \
            f"Conflict resolution failed. Got: {invoice_action.planned_target_path.name}"
        print("  ✓ Planner & Conflict Resolution OK\n")
        
        print("Test 2: Organizer executes plan and handles conflicts")
        organizer = AutoOrganizer()
        batch_id = "test-batch-m7-conflict"
        stats = organizer.execute_plan(actions, batch_id=batch_id)
        
        print(f"  Success: {stats['success']}")
        print(f"  Failed: {stats['failed']}")
        
        assert stats['success'] == 2, f"Expected 2 successful moves, got {stats['success']}"
        assert (base_folder / "PDFs" / "invoice_test_1.pdf").exists(), "Conflict file not renamed"
        assert (base_folder / "Code" / "script.py").exists(), "Code file not moved"
        assert not file1.exists(), "Original file 1 still exists"
        assert not file2.exists(), "Original file 2 still exists"
        print("  ✓ Organizer execution & Conflict handling OK\n")
        
        print("Test 3: Undo functionality restores original state")
        reversed_count = organizer.undo_last_batch(batch_id)
        print(f"  Reversed actions: {reversed_count}")
        
        assert reversed_count == 2, f"Expected 2 reversed actions, got {reversed_count}"
        assert file1.exists(), "Original file 1 not restored"
        assert file2.exists(), "Original file 2 not restored"
        assert not (base_folder / "PDFs" / "invoice_test_1.pdf").exists(), "Moved file not removed"
        print("  ✓ Undo OK\n")
    
    DB.close()
    print("=" * 60)
    print("  Milestone 7 — All tests passed ✓")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()