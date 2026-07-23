"""
DesktopAI
Desktop GUI Entry Point (Phase 10)

Launches the PySide6 desktop window: Dashboard, Search, AI Chat,
and Settings tabs, all built on top of the same modules the CLI
entry points (app.py, watch_app.py, search_app.py) use.
"""

from gui.main_window import main

if __name__ == "__main__":
    main()