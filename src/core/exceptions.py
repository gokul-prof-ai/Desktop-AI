"""
DesktopAI
Custom Exceptions

Application-specific exceptions, so calling code can catch precise
errors instead of relying on generic built-in exceptions.
"""


class DesktopAIError(Exception):
    """Base class for all DesktopAI-specific exceptions."""


class DatabaseNotConnectedError(DesktopAIError):
    """Raised when a database operation is attempted before connect() is called."""