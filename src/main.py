"""
DesktopAI v2.0 — Unified Application Entry Point
File: src/main.py

This is the ONLY entry point for DesktopAI v2.
It replaces all of these V1 files (retired in Phase 4):
    - src/gui_app.py
    - src/search_app.py
    - src/watch_app.py
    - src/app.py
    - src/run.py
    - run.py (root level)

Usage:
    python src/main.py              # Launch GUI (default)
    python src/main.py --cli        # Headless CLI mode (Phase 3+)
    python src/main.py --debug      # GUI with verbose logging
    python src/main.py --version    # Print version and exit
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ── Path bootstrap ─────────────────────────────────────────────────────────
# Ensures Python can find all src/ modules regardless of how main.py
# is invoked (directly, via pyproject.toml script, or via PyInstaller).
_SRC_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _SRC_DIR.parent

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# ── Version ────────────────────────────────────────────────────────────────
__version__ = "2.0.0"
__app_name__ = "DesktopAI"


# ── Argument Parser ────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    """Define all accepted command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="desktop-ai",
        description=f"{__app_name__} v{__version__} — Local AI-powered file organizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py                  Launch the GUI
  python src/main.py --debug          Launch with verbose logging
  python src/main.py --cli            Headless mode (coming in Phase 3)
  python src/main.py --version        Show version number
        """,
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"{__app_name__} v{__version__}",
    )

    parser.add_argument(
        "--cli",
        action="store_true",
        default=False,
        help="Run in headless CLI mode without launching the GUI.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable verbose debug logging to console and log file.",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        metavar="PATH",
        help="Path to a custom app.toml configuration file.",
    )

    return parser


# ── Launch Modes ───────────────────────────────────────────────────────────

def _launch_gui(args: argparse.Namespace) -> int:
    """
    Launch the PySide6 GUI application.

    Phase 1 (now):  Prints confirmation that scaffold is wired correctly.
    Phase 2 (next): Imports and launches the real QApplication + MainWindow.
    """
    # Deferred import — keeps startup fast if --cli is ever used
    # In Phase 2 this becomes:
    #   from gui.app import DesktopAIApp
    #   return DesktopAIApp(args).run()

    print(f"\n  {__app_name__} v{__version__}")
    print("  ─────────────────────────────")
    print("  Mode    : GUI")
    print(f"  Debug   : {'ON' if args.debug else 'OFF'}")
    print(f"  Config  : {args.config or 'default (config/app.toml)'}")
    print("  Status  : Milestone 1 complete — scaffold verified")
    print("  Next    : Milestone 2 will wire the Core layer here")
    print()
    return 0


def _launch_cli(args: argparse.Namespace) -> int:
    """
    Headless CLI mode for scripting and automation.
    Implemented in Phase 3. Reserved here so the argument is never broken.
    """
    print(f"\n  {__app_name__} v{__version__} — CLI mode")
    print("  CLI mode is implemented in Phase 3.")
    print("  Use 'python src/main.py' (without --cli) to launch the GUI.\n")
    return 0


# ── Entry Point ────────────────────────────────────────────────────────────

def main() -> None:
    """
    Primary application entry point.
    Called by: python src/main.py
    Called by: the 'desktop-ai' console script defined in pyproject.toml
    """
    parser = _build_parser()
    args = parser.parse_args()

    if args.cli:
        exit_code = _launch_cli(args)
    else:
        exit_code = _launch_gui(args)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()