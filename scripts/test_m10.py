"""
DesktopAI v2.0 — Milestone 10 Verification (E2E)
File: scripts/test_m10.py
Run: python scripts/test_m10.py
"""
from __future__ import annotations
import sys
import tempfile
import uuid
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
    AIGateway.set_provider(MockProvider(default_response="Documents", delay_ms=0))

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
        assert len(files) == 3
        results = FileClassifier().classify_batch(files)
        for r in results:
            print(f"    -> {r.file_info.filename}: {r.category} [{r.method}]")
        print("  PASS Scan + Classify\n")

        print("Test 2: Plan + Apply")
        actions = OrganizationPlanner().create_plan([r.file_info for r in results], out_dir)
        assert len(actions) == 3
        batch_id = f"m10-{uuid.uuid4().hex[:8]}"  # unique per run — no history bleed
        stats = AutoOrganizer().execute_plan(actions, batch_id)
        assert stats["success"] == 3
        assert (out_dir / "PDFs" / "invoice_jan.pdf").exists()
        assert (out_dir / "Code" / "script.py").exists()
        print("  PASS Apply — files physically moved\n")

        print("Test 3: History audit trail")
        history = DB.get_history(batch_id=batch_id)
        assert len(history) == 3, f"Expected 3 history rows, got {len(history)}"
        print("  PASS History recorded\n")

        print("Test 4: Undo batch")
        reversed_count = AutoOrganizer().undo_last_batch(batch_id)
        assert reversed_count == 3, f"Expected 3 reversed, got {reversed_count}"
        assert (src_dir / "invoice_jan.pdf").exists()
        assert (src_dir / "script.py").exists()
        undone = DB.get_history(batch_id=batch_id, status="undone")
        assert len(undone) == 3
        print("  PASS Undo — files restored, history marked undone\n")

    DB.close()
    print("=" * 60)
    print("  Milestone 10 — All tests passed")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()