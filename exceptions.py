"""
Custom exceptions for ate-neva-obst SDK.
"""


class ObjectsError(Exception):
    """Base exception for all ate-neva-obst errors."""

    def __init__(self, message: str, code: str = "", original: Exception = None):
        super().__init__(message)
        self.code = code
        self.original = original

    def __str__(self):
        if self.code:
            return f"[{self.code}] {super().__str__()}"
        return super().__str__()


class UploadError(ObjectsError):
    """Raised when a file upload fails."""


class DownloadError(ObjectsError):
    """Raised when generating a download URL fails."""


class ListError(ObjectsError):
    """Raised when listing bucket objects fails."""