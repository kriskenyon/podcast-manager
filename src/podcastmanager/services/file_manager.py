"""
File manager service for organizing podcast downloads.

This module handles file system operations for podcast downloads including
creating directories, generating file paths, and managing storage.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from loguru import logger

from podcastmanager.db.models import Episode, Podcast
from podcastmanager.utils.validators import (
    extract_file_extension,
    sanitize_filename,
    sanitize_folder_name,
    validate_download_path,
)


class FileManager:
    """
    Manages file system operations for podcast downloads.

    Handles:
    - Creating podcast-specific directories
    - Generating safe file names
    - Path validation and resolution
    - Disk space checking
    """

    def __init__(self, base_download_path: Path):
        """
        Initialize the file manager.

        Args:
            base_download_path: Base directory for all podcast downloads
        """
        self.base_path = Path(base_download_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"File manager initialized with base path: {self.base_path}")

    def get_podcast_directory(self, podcast: Podcast) -> Path:
        """
        Get or create the directory for a podcast.

        Args:
            podcast: Podcast object

        Returns:
            Path to the podcast directory
        """
        # Use the download_path from podcast (already sanitized)
        # or sanitize the title if download_path is not set
        folder_name = podcast.download_path or sanitize_folder_name(podcast.title)

        podcast_dir = self.base_path / folder_name
        podcast_dir.mkdir(parents=True, exist_ok=True)

        return podcast_dir

    def generate_episode_filename(
        self,
        episode: Episode,
        podcast: Podcast,
        audio_url: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Generate a filename for an episode.

        Format: {YYYY-MM-DD}-{episode-title}.{ext}

        Args:
            episode: Episode object
            podcast: Podcast object (for fallback)
            audio_url: Audio URL for extension extraction
            content_type: MIME type for extension extraction

        Returns:
            Sanitized filename
        """
        # Get publication date or use current date
        if episode.pub_date:
            date_str = episode.pub_date.strftime("%Y-%m-%d")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # Sanitize episode title
        title_part = sanitize_filename(episode.title, max_length=150)

        # Get file extension
        url = audio_url or episode.audio_url
        mime_type = content_type or episode.file_type
        extension = extract_file_extension(url, mime_type)

        # Combine into filename
        filename = f"{date_str}-{title_part}.{extension}"

        return filename

    def get_episode_file_path(
        self,
        episode: Episode,
        podcast: Podcast,
        audio_url: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Tuple[Path, str]:
        """
        Get the full file path for an episode download.

        Args:
            episode: Episode object
            podcast: Podcast object
            audio_url: Audio URL (optional, uses episode.audio_url if not provided)
            content_type: Content type (optional, uses episode.file_type if not provided)

        Returns:
            Tuple of (full_path, relative_path)
        """
        # Get podcast directory
        podcast_dir = self.get_podcast_directory(podcast)

        # Generate filename
        filename = self.generate_episode_filename(
            episode, podcast, audio_url, content_type
        )

        # Full path
        full_path = podcast_dir / filename

        # Relative path (from base download path)
        relative_path = full_path.relative_to(self.base_path)

        return full_path, str(relative_path)

    def validate_path(self, relative_path: str) -> Optional[Path]:
        """
        Validate and resolve a relative download path.

        Prevents path traversal attacks.

        Args:
            relative_path: Relative path from base download directory

        Returns:
            Resolved absolute path if valid, None otherwise
        """
        return validate_download_path(self.base_path, relative_path)

    def get_available_space(self) -> int:
        """
        Get available disk space in bytes.

        Returns:
            Available space in bytes
        """
        import shutil

        stats = shutil.disk_usage(self.base_path)
        return stats.free

    def has_enough_space(self, required_bytes: int, buffer_gb: float = 1.0) -> bool:
        """
        Check if there's enough disk space for a download.

        Args:
            required_bytes: Required space in bytes
            buffer_gb: Additional buffer space to keep free (in GB)

        Returns:
            True if enough space is available
        """
        available = self.get_available_space()
        buffer_bytes = int(buffer_gb * 1024 * 1024 * 1024)
        required_with_buffer = required_bytes + buffer_bytes

        return available >= required_with_buffer

    def get_file_size(self, path: Path) -> Optional[int]:
        """
        Get the size of a file in bytes.

        Args:
            path: File path

        Returns:
            File size in bytes or None if file doesn't exist
        """
        try:
            if path.exists() and path.is_file():
                return path.stat().st_size
            return None
        except Exception as e:
            logger.error(f"Error getting file size for {path}: {e}")
            return None

    def delete_file(self, path: Path) -> bool:
        """
        Delete a file safely.

        Args:
            path: File path to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if path.exists() and path.is_file():
                path.unlink()
                logger.info(f"Deleted file: {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
            return False

    def cleanup_empty_directories(self):
        """
        Remove empty podcast directories.

        Useful after deleting episodes or podcasts.
        """
        try:
            for podcast_dir in self.base_path.iterdir():
                if podcast_dir.is_dir():
                    # Check if directory is empty
                    if not any(podcast_dir.iterdir()):
                        podcast_dir.rmdir()
                        logger.info(f"Removed empty directory: {podcast_dir}")
        except Exception as e:
            logger.error(f"Error during directory cleanup: {e}")

    def get_podcast_storage_size(self, podcast: Podcast) -> int:
        """
        Calculate total storage used by a podcast.

        Args:
            podcast: Podcast object

        Returns:
            Total size in bytes
        """
        podcast_dir = self.get_podcast_directory(podcast)
        total_size = 0

        try:
            for file_path in podcast_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.error(f"Error calculating storage for {podcast.title}: {e}")

        return total_size

    def format_file_size(self, bytes: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            bytes: Size in bytes

        Returns:
            Formatted string (e.g., "45.2 MB")
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} PB"


# Global file manager instance
_file_manager: Optional[FileManager] = None


def get_file_manager(base_path: Optional[Path] = None) -> FileManager:
    """
    Get the global file manager instance.

    Args:
        base_path: Base download path (required on first call)

    Returns:
        FileManager instance

    Raises:
        RuntimeError: If file manager not initialized and base_path not provided
    """
    global _file_manager

    if _file_manager is None:
        if base_path is None:
            from podcastmanager.config import get_settings

            settings = get_settings()
            base_path = settings.download_base_path

        _file_manager = FileManager(base_path)

    return _file_manager


def init_file_manager(base_path: Path) -> FileManager:
    """
    Initialize the global file manager.

    Args:
        base_path: Base download path

    Returns:
        FileManager instance
    """
    global _file_manager
    _file_manager = FileManager(base_path)
    return _file_manager
