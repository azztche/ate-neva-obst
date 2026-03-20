"""
Custom exceptions for neva_obst SDK.
"""


class NevaObjectsError(Exception):
    """Base exception for all neva_obst errors."""

    def __init__(self, message: str, code: str = "", original: Exception = None):
        super().__init__(message)
        self.code = code
        self.original = original

    def __str__(self):
        if self.code:
            return f"[{self.code}] {super().__str__()}"
        return super().__str__()


class UploadError(NevaObjectsError):
    """Raised when a file upload fails."""


class DownloadError(NevaObjectsError):
    """Raised when generating a download URL fails."""


class ListError(NevaObjectsError):
    """Raised when listing bucket objects fails."""