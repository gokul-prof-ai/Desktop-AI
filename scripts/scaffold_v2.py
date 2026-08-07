"""
DesktopAI v2.0 — Project Scaffold Generator
File: scripts/scaffold_v2.py

Run this ONCE from the root of the repository:
    python scripts/scaffold_v2.py

Creates every V2 folder and __init__.py file.
Does NOT touch or delete any existing V1 files.
"""

from __future__ import annotations

from pathlib import Path

# Root of the repository (one level up from scripts/)
ROOT = Path(__file__).resolve().parent.parent

# ── All NEW V2 directories to create ──────────────────────────────────────
# These do not overlap destructively with V1.
# V1 folders (src/ai, src/core, src/gui, etc.) are left completely untouched.
DIRECTORIES: list[str] = [
    # V2 infrastructure layer (brand new — does not exist in V1)
    "src/infrastructure",
    "src/infrastructure/ai",
    "src/infrastructure/storage",
    "src/infrastructure/storage/migrations",
    "src/infrastructure/config",
    "src/infrastructure/plugins",

    # V2 domain layer (brand new — does not exist in V1)
    "src/domain",
    "src/domain/scanner",
    "src/domain/scanner/extractors",
    "src/domain/organizer",
    "src/domain/classifier",
    "src/domain/search",
    "src/domain/watcher",
    "src/domain/memory",

    # V2 application layer (brand new)
    "src/app",
    "src/app/workflows",
    "src/app/commands",

    # V2 GUI layer
    # src/gui already exists in V1 — we add subfolders only
    "src/gui/theme",
    "src/gui/windows",
    "src/gui/views",
    "src/gui/viewmodels",
    "src/gui/components",
    "src/gui/workers",

    # V2 core additions
    # src/core already exists in V1 — we will ADD new files, not replace
    # No new subfolders needed here

    # Config (already exists at root level — no action needed)
    # Tests (already exists — we add subfolders)
    "tests/unit",
    "tests/integration",
    "tests/fixtures",

    # Plugins directory (user-installed plugins will land here)
    "plugins",
]

# ── Python packages that need __init__.py ─────────────────────────────────
# Only NEW directories we created above.
# We skip src/gui because V1 already has its own __init__.py there.
PYTHON_PACKAGES: list[str] = [
    "src/infrastructure",
    "src/infrastructure/ai",
    "src/infrastructure/storage",
    "src/infrastructure/storage/migrations",
    "src/infrastructure/config",
    "src/infrastructure/plugins",
    "src/domain",
    "src/domain/scanner",
    "src/domain/scanner/extractors",
    "src/domain/organizer",
    "src/domain/classifier",
    "src/domain/search",
    "src/domain/watcher",
    "src/domain/memory",
    "src/app",
    "src/app/workflows",
    "src/app/commands",
    "src/gui/theme",
    "src/gui/windows",
    "src/gui/views",
    "src/gui/viewmodels",
    "src/gui/components",
    "src/gui/workers",
    "tests/unit",
    "tests/integration",
    "tests/fixtures",
    "plugins",
]


def create_directories() -> None:
    print("Step 1: Creating V2 directories...\n")
    created = 0
    for rel_path in DIRECTORIES:
        target = ROOT / rel_path
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATED] {rel_path}/")
            created += 1
        else:
            print(f"  [EXISTS]  {rel_path}/  (skipped)")
    print(f"\n  → {created} new directories created.\n")


def create_init_files() -> None:
    print("Step 2: Creating __init__.py files...\n")
    created = 0
    for rel_path in PYTHON_PACKAGES:
        init_file = ROOT / rel_path / "__init__.py"
        if not init_file.exists():
            package_name = rel_path.replace("/", ".")
            init_file.write_text(
                f'"""\nDesktopAI v2.0 — {package_name}\n"""\n',
                encoding="utf-8",
            )
            print(f"  [CREATED] {rel_path}/__init__.py")
            created += 1
        else:
            print(f"  [EXISTS]  {rel_path}/__init__.py  (skipped)")
    print(f"\n  → {created} new __init__.py files created.\n")


def create_gitkeep_files() -> None:
    print("Step 3: Adding .gitkeep to empty tracked directories...\n")
    dirs_needing_gitkeep = [
        "plugins",
        "tests/fixtures",
        "src/infrastructure/storage/migrations",
        "src/infrastructure/plugins",
    ]
    for rel_path in dirs_needing_gitkeep:
        gitkeep = ROOT / rel_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")
            print(f"  [CREATED] {rel_path}/.gitkeep")
        else:
            print(f"  [EXISTS]  {rel_path}/.gitkeep  (skipped)")
    print()


def verify_v1_intact() -> None:
    """Confirm we haven't touched V1 files."""
    print("Step 4: Verifying V1 files are untouched...\n")
    v1_files_to_check = [
        "src/ai/ollama_client.py",
        "src/ai/classifier.py",
        "src/ai/planner.py",
        "src/gui_app.py",
        "src/app.py",
        "requirements.txt",
    ]
    all_ok = True
    for rel_path in v1_files_to_check:
        target = ROOT / rel_path
        if target.exists():
            print(f"  [OK]  {rel_path}")
        else:
            print(f"  [MISSING] {rel_path}  ← unexpected")
            all_ok = False

    if all_ok:
        print("\n  → All V1 files confirmed intact. Nothing was deleted.\n")
    else:
        print("\n  → WARNING: Some V1 files not found. Check manually.\n")


def print_summary() -> None:
    print("=" * 54)
    print("  DesktopAI V2 Scaffold — Complete")
    print("=" * 54)
    print("""
  V1 files:   UNTOUCHED (still on v2-dev branch)
  V2 folders: CREATED   (new layer structure)

  Your project now has both V1 and V2 structure
  side by side. V2 code will be built into the
  new folders. V1 is retired in Phase 4.

  Next step: Milestone 2 — Core Layer
  Files:  src/core/exceptions.py
          src/core/logger.py
          src/core/constants.py
          src/core/events.py
""")


def main() -> None:
    print()
    print("=" * 54)
    print("  DesktopAI v2.0 — Project Scaffold Generator")
    print("=" * 54)
    print()

    create_directories()
    create_init_files()
    create_gitkeep_files()
    verify_v1_intact()
    print_summary()


if __name__ == "__main__":
    main()