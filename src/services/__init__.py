"""
DesktopAI v2.0 — Services Layer
File: src/services/__init__.py

Public API for this package. Import FileService from here.

Usage:
    from services import FileService
    from services import file_service  # module, if needed

Do NOT import domain or infrastructure classes directly in the GUI.
Use FileService exclusively.
"""
from services.file_service import FileService

__all__ = ["FileService"]
