"""
DesktopAI v2.0 — Milestone 10 Verification (End-to-End)
File: scripts/test_m10.py

Headless proof of the full loop:
scan → classify → plan → apply → history → undo → restored.
Run: python scripts/test_m10.py
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_SRC))


def main() -> None:
    print("\n" + "=" * 60)
    print("  DesktopAI v2.0 — Milestone 10 Verification (E2E)")
    print("=" * 60 + "\n")

    from core.logger import configure
    configure(debug=False)

    from infrastructure.config.settings import Settings
    Settings.load()

    from infrastructure.ai.gateway import AIGateway
    from infrastructure.ai.mock_provider import MockProvider
    mock = MockProvider(default_response="Documents", delay_ms=0)
    mock.set_response("invoice", "Finance")
    AIGateway.set_provider(mock)

    from infrastructure.storage.database import DB
    DB.connect()
    from infrastructure.storage.memory_store import MemoryStore
    MemoryStore.clear_all()

    from domain.scanner.scanner import FileScanner
    from domain.classifier.classifier import FileClassifier
    from domain.organizer.planner import OrganizationPlanner
    from domain.organizer.organizer import AutoOrganizer

    with tempfile.TemporaryDirectory() as tmp:
        src_dir = Path(tmp) / "inbox"
        out_dir = Path(tmp) / "organized"
        src_dir.mkdir()
        (src_dir / "invoice_jan.pdf").write_text("invoice")
        (src_dir / "script.py").write_text("print('hi')")
        (src_dir / "notes.txt").write_text("hello")

        print("Test 1: Scan + Classify")
        files = FileScanner().scan(src_dir)
        assert len(files) == 3, f"Expected 3 files, got {len(files)}"
        results = FileClassifier().classify_batch(files)
        for r in results:
            print(f"    → {r.file_info.filename}: {r.category} [{r.method}]")
        print("  ✓ Scan + Classify OK\n")

        print("Test 2: Plan + Apply")
        actions = OrganizationPlanner().create_plan(
            [r.file_info for r in results], out_dir
        )
        assert len(actions) == 3, f"Expected 3 actions, got {len(actions)}"
        batch_id = "m10-e2e-batch"
        stats = AutoOrganizer().execute_plan(actions, batch_id)
        print(f"    success={stats['success']} failed={stats['failed']}")
        assert stats["success"] == 3
        assert (out_dir / "PDFs" / "invoice_jan.pdf").exists()
        assert (out_dir / "Code" / "script.py").exists()
        print("  ✓ Apply OK — files physically moved\n")

        print("Test 3: History audit trail")
        history = DB.get_history(batch_id=batch_id)
        assert len(history) == 3, f"Expected 3 history rows, got {len(history)}"
        print(f"    {len(history)} audit entries recorded")
        print("  ✓ History OK\n")

        print("Test 4: Undo batch")
        reversed_count = AutoOrganizer().undo_last_batch(batch_id)
        assert reversed_count == 3, f"Expected 3 reversed, got {reversed_count}"
        assert (src_dir / "invoice_jan.pdf").exists()
        assert (src_dir / "script.py").exists()
        undone = DB.get_history(batch_id=batch_id, status="undone")
        assert len(undone) == 3
        print(f"    {reversed_count} files restored, history marked undone")
        print("  ✓ Undo OK\n")

    DB.close()
    print("=" * 60)
    print("  Milestone 10 — All tests passed ✓")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()