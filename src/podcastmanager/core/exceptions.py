"""
Custom exceptions for podcast manager operations.
"""


class PodcastManagerException(Exception):
    """Base exception for podcast manager errors."""
    pass


class DownloadException(PodcastManagerException):
    """Base exception for download-related errors."""
    pass


class EpisodeNotFoundException(DownloadException):
    """Raised when an episode cannot be found."""
    pass


class InsufficientStorageException(DownloadException):
    """Raised when there is not enough disk space for a download."""

    def __init__(self, required_bytes: int, available_bytes: int, message: str = None):
        self.required_bytes = required_bytes
        self.available_bytes = available_bytes

        if message is None:
            required_mb = required_bytes / (1024 * 1024)
            available_mb = available_bytes / (1024 * 1024)
            message = (
                f"Insufficient disk space. Required: {required_mb:.1f} MB, "
                f"Available: {available_mb:.1f} MB"
            )

        super().__init__(message)


class DownloadAlreadyExistsException(DownloadException):
    """Raised when attempting to queue a download that already exists."""

    def __init__(self, status: str, message: str = None):
        self.status = status

        if message is None:
            message = f"Download already exists with status: {status}"

        super().__init__(message)
