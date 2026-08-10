"""
DesktopAI v2.0 — Services Layer
File: src/services/__init__.py

Public application-service API.

GUI and future application entry points should depend on these facades
instead of importing domain/infrastructure implementations directly.
"""
from services.application_services import ApplicationServices
from services.file_service import FileService
from services.watcher_service import WatcherService

__all__ = ["ApplicationServices", "FileService", "WatcherService"]
