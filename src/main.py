"""
DesktopAI v2.0
Application entry point.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


__version__ = "2.0.0"
__app_name__ = "DesktopAI"


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="desktop-ai",
        description=(
            f"{__app_name__} v{__version__} "
            "— Local AI file organizer"
        ),
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"{__app_name__} v{__version__}",
    )

    parser.add_argument(
        "--cli",
        action="store_true",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
    )

    parser.add_argument(
        "--mock-ai",
        action="store_true",
        help="Use MockProvider instead of Ollama.",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=None,
    )

    return parser


def _setup_ai_gateway(use_mock: bool):
    from infrastructure.ai.gateway import AIGateway

    if use_mock:
        from infrastructure.ai.mock_provider import MockProvider

        AIGateway.set_provider(
            MockProvider(delay_ms=100)
        )
    else:
        from infrastructure.ai.ollama_provider import OllamaProvider

        AIGateway.set_provider(
            OllamaProvider()
        )


def _launch_gui(args) -> int:
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication

    from core.logger import get_logger
    from gui.dialogs.setup_wizard import SetupWizard
    from gui.theme.app_shell import apply_theme
    from gui.windows.main_window import MainWindow
    from infrastructure.config.settings import Settings
    from services import ApplicationServices

    logger = get_logger(__name__)

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setFont(QFont("Segoe UI", 10))

    theme = (
        Settings.app.theme
        if Settings.app.theme in {"light", "dark"}
        else "dark"
    )
    apply_theme(app, theme)

    # Application-level services are created once for the whole GUI session.
    services = ApplicationServices()
    services.start()

    # First-run onboarding.
    if Settings.app.first_run:
        wizard = SetupWizard(
            services,
            allow_offline=args.mock_ai,
        )
        result = wizard.exec()

        # If the user closes/cancels setup, do not silently mark first-run
        # complete. The wizard will appear again on the next launch.
        if result != SetupWizard.Accepted:
            logger.warning(
                "Setup wizard was cancelled. First-run setup remains pending."
            )

    window = MainWindow(services)
    window.show()

    logger.info(
        "DesktopAI GUI launched successfully."
    )

    return app.exec()


def _launch_cli(args) -> int:
    print(
        f"{__app_name__} v{__version__}"
    )
    return 0


def main():
    parser = _build_parser()
    args = parser.parse_args()

    from core.logger import configure

    configure(
        debug=args.debug
    )

    from infrastructure.config.settings import Settings

    Settings.load(
        config_path=args.config
    )

    _setup_ai_gateway(
        args.mock_ai
    )

    from infrastructure.storage.database import DB

    DB.connect()

    try:
        if args.cli:
            exit_code = _launch_cli(args)
        else:
            exit_code = _launch_gui(args)

    except Exception:
        sys.stdout.write(
            "\n"
            + "=" * 60
            + "\n"
        )
        sys.stdout.write(
            "FATAL GUI CRASH DETECTED\n"
        )
        sys.stdout.write(
            "=" * 60
            + "\n"
        )
        traceback.print_exc(
            file=sys.stdout
        )
        sys.stdout.write(
            "=" * 60
            + "\n\n"
        )
        sys.stdout.flush()
        exit_code = 1

    finally:
        try:
            DB.close()
        except Exception:
            pass

    sys.exit(exit_code)


if __name__ == "__main__":
    main()