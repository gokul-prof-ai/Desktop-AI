"""
DesktopAI v2.0 — Exception Hierarchy
File: src/core/exceptions.py

All application-specific exceptions live here.

Why a hierarchy?
    Callers can catch at any level of specificity:
    - except DesktopAIError       → catch everything from this app
    - except AIGatewayError       → catch any AI-related failure
    - except ProviderTimeoutError → catch only timeout failures

Rule: Never raise a plain Exception or RuntimeError from DesktopAI code.
      Always raise one of these — or add a new one here if none fits.
"""

from __future__ import annotations


# ══════════════════════════════════════════════════════════════════════════
# ROOT
# ══════════════════════════════════════════════════════════════════════════

class DesktopAIError(Exception):
    """
    Base class for every DesktopAI exception.
    Catch this to handle any application-level error in one place.
    """


# ══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════

class ConfigError(DesktopAIError):
    """Raised when the settings system encounters a problem."""

class ConfigFileNotFoundError(ConfigError):
    """Raised when app.toml or categories.toml cannot be found."""

class ConfigValidationError(ConfigError):
    """Raised when a config file exists but contains invalid values."""


# ══════════════════════════════════════════════════════════════════════════
# AI GATEWAY
# ══════════════════════════════════════════════════════════════════════════

class AIGatewayError(DesktopAIError):
    """Base class for all AI provider errors."""

class ProviderNotAvailableError(AIGatewayError):
    """
    Raised when the AI provider cannot be reached.
    Example: Ollama is not running, or the host URL is wrong.
    """

class ProviderTimeoutError(AIGatewayError):
    """Raised when the AI provider takes too long to respond."""

class ProviderResponseError(AIGatewayError):
    """
    Raised when the provider responds but the response is malformed
    or cannot be parsed into the expected format.
    """

class ModelNotFoundError(AIGatewayError):
    """
    Raised when the requested model is not available on the provider.
    Example: 'llama3.2' not pulled in Ollama.
    """

class EmbeddingError(AIGatewayError):
    """Raised when generating a vector embedding fails."""


# ══════════════════════════════════════════════════════════════════════════
# STORAGE / DATABASE
# ══════════════════════════════════════════════════════════════════════════

class StorageError(DesktopAIError):
    """Base class for all storage and database errors."""

class DatabaseNotConnectedError(StorageError):
    """
    Raised when a database operation is attempted before connect()
    is called. Kept here for backward compatibility with V1 callers.
    """

class DatabaseMigrationError(StorageError):
    """Raised when a schema migration fails."""

class RecordNotFoundError(StorageError):
    """Raised when a required database record does not exist."""

class DuplicateRecordError(StorageError):
    """Raised when an insert would violate a unique constraint."""


# ══════════════════════════════════════════════════════════════════════════
# FILE SCANNER
# ══════════════════════════════════════════════════════════════════════════

class ScannerError(DesktopAIError):
    """Base class for all file scanning errors."""

class PathNotFoundError(ScannerError):
    """Raised when the folder or file to scan does not exist."""

class PathPermissionError(ScannerError):
    """Raised when DesktopAI lacks permission to read a path."""

class ExtractionError(ScannerError):
    """
    Raised when text extraction from a file fails.
    Example: corrupted PDF, password-protected DOCX.
    """


# ══════════════════════════════════════════════════════════════════════════
# ORGANIZER
# ══════════════════════════════════════════════════════════════════════════

class OrganizerError(DesktopAIError):
    """Base class for all file organization errors."""

class PlanningError(OrganizerError):
    """Raised when the AI planner cannot produce a valid organization plan."""

class ActionExecutionError(OrganizerError):
    """Raised when a file move, rename, or copy operation fails."""

class UndoError(OrganizerError):
    """Raised when an undo operation cannot be completed."""


# ══════════════════════════════════════════════════════════════════════════
# SEARCH
# ══════════════════════════════════════════════════════════════════════════

class SearchError(DesktopAIError):
    """Base class for all search engine errors."""

class IndexNotBuiltError(SearchError):
    """Raised when a search is attempted before the FAISS index is built."""

class IndexCorruptedError(SearchError):
    """Raised when the FAISS index file exists but cannot be loaded."""


# ══════════════════════════════════════════════════════════════════════════
# PLUGINS
# ══════════════════════════════════════════════════════════════════════════

class PluginError(DesktopAIError):
    """Base class for all plugin system errors."""

class PluginLoadError(PluginError):
    """Raised when a plugin file cannot be imported."""

class PluginValidationError(PluginError):
    """Raised when a plugin does not implement the required interface."""

class PluginConflictError(PluginError):
    """Raised when two plugins register the same name or command."""


# ══════════════════════════════════════════════════════════════════════════
# WORKFLOW
# ══════════════════════════════════════════════════════════════════════════

class WorkflowError(DesktopAIError):
    """Raised when an application-layer workflow fails."""

class WorkflowCancelledError(WorkflowError):
    """Raised when a workflow is cancelled by the user."""