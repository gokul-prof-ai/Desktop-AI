"""
DesktopAI v2.0 — Unified Application Entry Point
File: src/main.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ── Path bootstrap ─────────────────────────────────────────────────────────
_SRC_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _SRC_DIR.parent

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# ── Version ────────────────────────────────────────────────────────────────
__version__ = "2.0.0"
__app_name__ = "DesktopAI"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="desktop-ai",
        description=f"{__app_name__} v{__version__} — Local AI-powered file organizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py                  Launch the GUI
  python src/main.py --debug          Launch with verbose logging
  python src/main.py --cli            Headless mode (Phase 3)
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


def _launch_gui(args: argparse.Namespace) -> int:
    from core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Launching DesktopAI v%s in GUI mode", __version__)

    print(f"\n  {__app_name__} v{__version__}")
    print("  ─────────────────────────────")
    print("  Mode    : GUI")
    print(f"  Debug   : {'ON' if args.debug else 'OFF'}")
    print(f"  Config  : {args.config or 'default (config/app.toml)'}")
    print("  Status  : Milestone 2 complete — Core layer active")
    print("  Logger  : logs/desktop_ai.log")
    print("  Next    : Milestone 3 — Settings service + TOML config")
    print()
    return 0


def _launch_cli(args: argparse.Namespace) -> int:
    from core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("CLI mode requested — not yet implemented")
    print(f"\n  {__app_name__} v{__version__} — CLI mode")
    print("  CLI mode is implemented in Phase 3.\n")
    return 0


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Configure logging FIRST — before any other import that might log.
    from core.logger import configure
    configure(debug=args.debug)

    if args.cli:
        exit_code = _launch_cli(args)
    else:
        exit_code = _launch_gui(args)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()