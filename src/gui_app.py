"""
DesktopAI
Desktop GUI Entry Point (Phase 10)

Launches the PySide6 desktop window (see gui/main_window.py).
Run this to use DesktopAI as a graphical application instead of
the command-line entry points (app.py, search_app.py, watch_app.py).
"""

import sys

from PySide6.QtWidgets import QApplication

from core.logger import get_logger
from gui.main_window import MainWindow

logger = get_logger("gui")


def main():
    logger.info("Launching DesktopAI GUI.")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    exit_code = app.exec()

    logger.info("DesktopAI GUI closed.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()