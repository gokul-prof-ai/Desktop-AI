"""
DesktopAI v2.0 — Application Event Bus
File: src/core/events.py

Defines Qt signals that allow different layers to communicate
without importing each other directly.

The Problem This Solves:
    Without an event bus, the GUI would have to import from domain/
    and domain/ would have to import from infrastructure/ — creating
    a tangled web of cross-layer dependencies.

How It Works:
    1. Any module can emit a signal:
           AppEvents.scan_completed.emit(result)

    2. Any other module can listen to that signal:
           AppEvents.scan_completed.connect(self.on_scan_done)

    3. The two modules never import each other.

Rule: Only ADD signals here. Never remove them once published —
      other modules may depend on them. Mark deprecated ones
      with a comment instead of deleting them.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class _AppEventBus(QObject):
    """
    Singleton Qt signal bus for application-wide events.

    Access via the module-level `AppEvents` instance — do not
    instantiate this class yourself.

    Example:
        from core.events import AppEvents

        # Emit (from domain layer):
        AppEvents.scan_completed.emit(file_count)

        # Connect (from GUI layer):
        AppEvents.scan_completed.connect(self.update_status_bar)
    """

    # ── Scanner events ─────────────────────────────────────────────────
    # Emitted when a folder scan starts. Carries the folder path as str.
    scan_started: Signal = Signal(str)

    # Emitted after each file is processed. Carries files done (int)
    # and total files (int) for progress bar updates.
    scan_progress: Signal = Signal(int, int)

    # Emitted when a scan finishes successfully. Carries total file count.
    scan_completed: Signal = Signal(int)

    # Emitted when a scan fails. Carries the error message as str.
    scan_failed: Signal = Signal(str)

    # ── Organizer / Planner events ─────────────────────────────────────
    # Emitted when AI analysis of a file completes.
    # Carries: file path (str), category (str), confidence (float).
    file_classified: Signal = Signal(str, str, float)

    # Emitted when the full organization plan is ready to preview.
    plan_ready: Signal = Signal(object)   # carries OrganizationPlan

    # Emitted as files are being moved/renamed during apply.
    # Carries: files done (int), total files (int).
    apply_progress: Signal = Signal(int, int)

    # Emitted when apply finishes. Carries count of successful operations.
    apply_completed: Signal = Signal(int)

    # Emitted when apply fails partway. Carries error message.
    apply_failed: Signal = Signal(str)

    # ── Search events ──────────────────────────────────────────────────
    # Emitted when the FAISS index rebuild starts.
    index_build_started: Signal = Signal()

    # Emitted when the index rebuild finishes.
    index_build_completed: Signal = Signal()

    # Emitted when search results are ready.
    # Carries a list of result objects.
    search_results_ready: Signal = Signal(object)

    # ── AI Gateway events ──────────────────────────────────────────────
    # Emitted when the Ollama connection status changes.
    # Carries: is_connected (bool).
    ai_connection_changed: Signal = Signal(bool)

    # Emitted when a model is being loaded (cold start).
    # Carries: model name (str).
    ai_model_loading: Signal = Signal(str)

    # ── Settings events ────────────────────────────────────────────────
    # Emitted when the user saves settings. Carries nothing —
    # listeners should re-read the Settings service directly.
    settings_changed: Signal = Signal()

    # ── Watcher events ─────────────────────────────────────────────────
    # Emitted when the filesystem watcher detects a new or changed file.
    # Carries the file path as str.
    watcher_file_detected: Signal = Signal(str)

    # ── Toast / Notification events ────────────────────────────────────
    # Emitted when any layer wants to show a non-blocking notification.
    # Carries: message (str), level (str) — "info", "success", "warning", "error"
    toast_requested: Signal = Signal(str, str)

    # ── Application lifecycle ──────────────────────────────────────────
    # Emitted just before the application shuts down.
    app_shutting_down: Signal = Signal()


# ── Singleton instance ─────────────────────────────────────────────────────
# Import and use this everywhere. Never instantiate _AppEventBus yourself.
#
# Usage:
#   from core.events import AppEvents
#   AppEvents.toast_requested.emit("Scan complete", "success")
#
AppEvents = _AppEventBus()