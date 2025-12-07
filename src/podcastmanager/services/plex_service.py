"""
Plex Media Server integration service.

This module provides functionality to interact with Plex Media Server,
allowing the podcast manager to check play status and make smart cleanup decisions.
"""

from pathlib import Path
from typing import Optional

from loguru import logger

try:
    from plexapi.server import PlexServer
    from plexapi.exceptions import PlexApiException
    PLEX_AVAILABLE = True
except ImportError:
    PLEX_AVAILABLE = False
    logger.warning("PlexAPI not installed. Plex integration disabled. Install with: pip install PlexAPI")


class PlexService:
    """
    Service for interacting with Plex Media Server.

    Features:
    - Check if episodes have been played
    - Query play counts and progress
    - Verify Plex connectivity
    """

    def __init__(self, url: str, token: str, library_name: str):
        """
        Initialize Plex service.

        Args:
            url: Plex server URL (e.g., http://192.168.1.100:32400)
            token: Plex authentication token
            library_name: Name of the podcast library in Plex

        Raises:
            Exception: If cannot connect to Plex or library not found
        """
        if not PLEX_AVAILABLE:
            raise ImportError("PlexAPI library not installed")

        self.url = url
        self.token = token
        self.library_name = library_name

        try:
            logger.info(f"Connecting to Plex server: {url}")
            self.plex = PlexServer(url, token)
            logger.info(f"Connected to Plex: {self.plex.friendlyName}")

            # Get the podcast library
            self.library = self.plex.library.section(library_name)
            logger.success(f"Found Plex library: {library_name}")

        except PlexApiException as e:
            logger.error(f"Failed to connect to Plex: {e}")
            raise
        except Exception as e:
            logger.error(f"Plex initialization error: {e}")
            raise

    def is_episode_played(self, file_path: str) -> bool:
        """
        Check if an episode has been played in Plex.

        Args:
            file_path: Relative or absolute path to the episode file

        Returns:
            True if episode has been played, False otherwise
        """
        try:
            # Convert to Path for better handling
            path = Path(file_path)

            # Try searching by filename first (faster)
            filename = path.name
            logger.debug(f"Searching Plex for: {filename}")

            # Search in the library
            results = self.library.search(title=path.stem)

            if not results:
                # Try searching by full path
                results = self.library.searchFiles(file=str(path))

            if not results:
                logger.debug(f"Episode not found in Plex: {filename}")
                return False

            # Check the first match
            episode = results[0]

            # Check if it's been played
            # isPlayed is set when an item has been watched/listened to completion
            # viewCount tracks how many times it's been played
            is_played = episode.isPlayed or (episode.viewCount and episode.viewCount > 0)

            if is_played:
                logger.debug(
                    f"Episode '{filename}' played: viewCount={episode.viewCount}, "
                    f"isPlayed={episode.isPlayed}"
                )
            else:
                logger.debug(f"Episode '{filename}' not yet played")

            return is_played

        except PlexApiException as e:
            logger.error(f"Plex API error checking {file_path}: {e}")
            # If we can't check, assume not played (safer - keeps the file)
            return False
        except Exception as e:
            logger.error(f"Error checking Plex status for {file_path}: {e}")
            return False

    def get_episode_progress(self, file_path: str) -> Optional[float]:
        """
        Get playback progress for an episode.

        Args:
            file_path: Path to the episode file

        Returns:
            Progress as percentage (0.0 to 1.0), or None if not found
        """
        try:
            path = Path(file_path)
            filename = path.name

            results = self.library.search(title=path.stem)
            if not results:
                results = self.library.searchFiles(file=str(path))

            if not results:
                return None

            episode = results[0]

            # Get view offset (position in milliseconds)
            if hasattr(episode, 'viewOffset') and hasattr(episode, 'duration'):
                if episode.duration and episode.duration > 0:
                    progress = episode.viewOffset / episode.duration
                    return min(1.0, max(0.0, progress))

            return None

        except Exception as e:
            logger.error(f"Error getting episode progress for {file_path}: {e}")
            return None

    def test_connection(self) -> bool:
        """
        Test the connection to Plex server.

        Returns:
            True if connection is working
        """
        try:
            # Try to get server info
            _ = self.plex.friendlyName
            _ = self.library.title

            logger.success(f"Plex connection test successful: {self.plex.friendlyName}")
            return True

        except Exception as e:
            logger.error(f"Plex connection test failed: {e}")
            return False

    def get_library_stats(self) -> dict:
        """
        Get statistics about the podcast library.

        Returns:
            Dictionary with library stats
        """
        try:
            total_episodes = len(self.library.all())
            played_count = len([e for e in self.library.all() if e.isPlayed])

            stats = {
                "library_name": self.library.title,
                "total_episodes": total_episodes,
                "played_episodes": played_count,
                "unplayed_episodes": total_episodes - played_count,
            }

            logger.info(f"Plex library stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error getting library stats: {e}")
            return {}


# Global Plex service instance
_plex_service: Optional[PlexService] = None


def get_plex_service(url: str = None, token: str = None, library: str = None) -> Optional[PlexService]:
    """
    Get or create the global Plex service instance.

    Args:
        url: Plex server URL (required on first call)
        token: Plex token (required on first call)
        library: Library name (required on first call)

    Returns:
        PlexService instance or None if Plex is not available/configured
    """
    global _plex_service

    if _plex_service is None and all([url, token, library]):
        try:
            _plex_service = PlexService(url, token, library)
        except Exception as e:
            logger.error(f"Failed to initialize Plex service: {e}")
            return None

    return _plex_service


def is_plex_available() -> bool:
    """
    Check if PlexAPI library is installed.

    Returns:
        True if PlexAPI is available
    """
    return PLEX_AVAILABLE
