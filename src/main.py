"""
DesktopAI v2.0 — Application Entry Point
File: src/main.py
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _SRC_DIR.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

__version__ = "2.0.0"
__app_name__ = "DesktopAI"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="desktop-ai",
        description=f"{__app_name__} v{__version__} — AI-powered file organizer",
    )
    parser.add_argument("--version", "-v", action="version",
                        version=f"{__app_name__} v{__version__}")
    parser.add_argument("--cli", action="store_true", default=False)
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("--mock-ai", action="store_true", default=False,
                        help="Use MockProvider instead of Ollama.")
    parser.add_argument("--config", type=Path, default=None, metavar="PATH")
    return parser


def _setup_ai_gateway(use_mock: bool) -> None:
    from infrastructure.ai.gateway import AIGateway
    if use_mock:
        from infrastructure.ai.mock_provider import MockProvider
        AIGateway.set_provider(MockProvider(delay_ms=100))
    else:
        from infrastructure.ai.ollama_provider import OllamaProvider
        AIGateway.set_provider(OllamaProvider())


def _launch_gui(args: argparse.Namespace) -> int:
    from core.logger import get_logger, set_debug_mode
    from infrastructure.config.settings import Settings
    from infrastructure.ai.gateway import AIGateway
    from infrastructure.storage.database import DB
    
    logger = get_logger(__name__)
    logger.info("Launching DesktopAI v%s", __version__)
    
    # In mock mode, reduce logging verbosity
    if args.mock_ai:
        set_debug_mode(False)
    
    stats = DB.get_stats()
    provider_name = AIGateway.get_provider().provider_name
    is_healthy = AIGateway.health_check()
    
    print(f"\n{__app_name__} v{__version__}")
    print("  ─────────────────────────────────────────")
    print("  Mode       : GUI")
    print(f"  Debug      : {'ON' if args.debug else 'OFF'}")
    print(f"  AI Model   : {Settings.ai.model}")
    print(f"  Provider   : {provider_name}")
    print(f"  AI Ready   : {'✓ YES' if is_healthy else '✗ NO'}")
    print(f"  Categories : {len(Settings.categories)} rules loaded")
    print(f"  DB Files   : {stats['total_files']} tracked")
    print(f"  DB History : {stats['total_operations']} operations")
    print("  Status     : Milestone 6 complete — Ready for UI development")
    print()
    
    return 0


def _launch_cli(args: argparse.Namespace) -> int:
    print(f"\n{__app_name__} v{__version__} — CLI mode\n")
    return 0


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    
    from core.logger import configure
    configure(debug=args.debug)
    
    from infrastructure.config.settings import Settings
    Settings.load(config_path=args.config)
    
    _setup_ai_gateway(use_mock=args.mock_ai)
    
    from infrastructure.storage.database import DB
    DB.connect()
    
    try:
        if args.cli:
            exit_code = _launch_cli(args)
        else:
            exit_code = _launch_gui(args)
    finally:
        DB.close()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()