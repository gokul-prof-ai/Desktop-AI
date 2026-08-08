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
    parser.add_argument("--version", "-v", action="version",
                        version=f"{__app_name__} v{__version__}")
    parser.add_argument("--cli", action="store_true", default=False,
                        help="Run in headless CLI mode.")
    parser.add_argument("--debug", action="store_true", default=False,
                        help="Enable verbose debug logging.")
    parser.add_argument("--config", type=Path, default=None,
                        metavar="PATH", help="Path to a custom app.toml.")
    return parser


def _launch_gui(args: argparse.Namespace) -> int:
    from core.logger import get_logger
    from infrastructure.config.settings import Settings

    logger = get_logger(__name__)
    logger.info("Launching DesktopAI v%s in GUI mode", __version__)

    print(f"\n  {__app_name__} v{__version__}")
    print("  ─────────────────────────────────────────")
    print("  Mode      : GUI")
    print(f"  Debug     : {'ON' if args.debug else 'OFF'}")
    print(f"  AI Model  : {Settings.ai.model}")
    print(f"  AI Host   : {Settings.ai.host}")
    print(f"  Workers   : {Settings.scanner.max_workers}")
    print(f"  Theme     : {Settings.app.theme}")
    print(f"  Categories: {len(Settings.categories)} rules loaded")
    print("  Status    : Milestone 3 complete — Settings service active")
    print()
    return 0


def _launch_cli(args: argparse.Namespace) -> int:
    from core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("CLI mode requested — not yet implemented")
    print(f"\n  {__app_name__} v{__version__} — CLI mode (Phase 3)\n")
    return 0


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Step 1 — Configure logging first (so config errors are logged)
    from core.logger import configure
    configure(debug=args.debug)

    # Step 2 — Load settings (creates TOML files if they don't exist)
    from infrastructure.config.settings import Settings
    Settings.load(config_path=args.config)

    # Step 3 — Launch the appropriate mode
    if args.cli:
        exit_code = _launch_cli(args)
    else:
        exit_code = _launch_gui(args)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()