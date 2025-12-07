"""
Download service for fetching podcast episodes.

This module handles the actual downloading of podcast audio files with
progress tracking, resume support, and error handling.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
import httpx
from loguru import logger
from sqlalchemy import select

from podcastmanager.db.models import Download, Episode


class DownloadService:
    """
    Service for downloading podcast episodes.

    Features:
    - Async streaming downloads
    - Progress tracking
    - Resume support for partial downloads
    - Timeout handling
    - Content validation
    """

    def __init__(self, timeout: int = 3600, chunk_size: int = 8192):
        """
        Initialize the download service.

        Args:
            timeout: Download timeout in seconds (default: 1 hour)
            chunk_size: Size of download chunks in bytes (default: 8KB)
        """
        self.timeout = timeout  # httpx uses plain timeout value
        self.chunk_size = chunk_size

    async def download_episode(
        self,
        episode: Episode,
        file_path: Path,
        download_record: Download,
        session_factory,
    ) -> bool:
        """
        Download an episode to a file.

        Args:
            episode: Episode to download
            file_path: Destination file path
            download_record: Download database record to update
            session_factory: Async callable that returns a database session

        Returns:
            True if download succeeded, False otherwise
        """
        logger.info(f"Starting download: {episode.title} -> {file_path}")

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Check for partial download
        resume_position = 0
        if file_path.exists():
            resume_position = file_path.stat().st_size
            logger.info(f"Resuming download from byte {resume_position}")

        # Only resolve URL if it's not a signed URL or tracking URL (they're sensitive to HEAD requests)
        is_signed = self._is_signed_url(episode.audio_url)
        if is_signed:
            logger.info(f"Detected signed/tracking URL, using directly without HEAD request")
            final_url = episode.audio_url
        else:
            # Resolve final URL first (follow redirects)
            final_url = await self._resolve_url(episode.audio_url)
            if final_url != episode.audio_url:
                logger.info(f"Resolved URL: {final_url}")

        try:
            # Create HTTP session with httpx (more reliable than aiohttp for redirects)
            # Use podcast app User-Agent (Overcast is widely accepted)
            # Keep headers minimal to match curl behavior
            if is_signed:
                headers = {
                    "User-Agent": "Overcast/1.0 Podcast Sync (1 subscribers; feed-id=12345)",
                }
            else:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "en-US,en;q=0.9",
                }

            if resume_position > 0:
                # Request resume with Range header
                headers["Range"] = f"bytes={resume_position}-"

            logger.info(f"Using User-Agent: {headers['User-Agent'][:50]}...")
            logger.info(f"Requesting URL: {final_url}")

            # Use httpx for downloads (handles redirects better than aiohttp)
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            ) as client:
                async with client.stream('GET', final_url, headers=headers) as response:
                    logger.info(f"Got response status: {response.status_code}")
                    logger.info(f"Final URL: {response.url}")

                    # Check response status
                    if response.status_code == 416:
                        # Range not satisfiable - file already complete
                        logger.info("File already complete")
                        return await self._mark_complete(
                            download_record, file_path, session_factory
                        )

                    if response.status_code not in (200, 206):
                        error_msg = f"HTTP {response.status_code}: {response.reason_phrase}"
                        logger.error(f"Download failed: {error_msg}")
                        logger.error(f"Failed URL: {final_url}")
                        logger.error(f"Original URL: {episode.audio_url}")
                        # Log response headers for debugging
                        logger.debug(f"Response headers: {dict(response.headers)}")
                        await self._mark_failed(
                            download_record, error_msg, session_factory
                        )
                        return False

                    # Get total file size
                    total_size = int(response.headers.get("content-length", 0))
                    if response.status_code == 206:  # Partial content
                        # Add resume position to get actual total
                        total_size += resume_position

                    # Get content type
                    content_type = response.headers.get("content-type")

                    # Update download status
                    await self._update_status(
                        download_record,
                        status="downloading",
                        started_at=datetime.utcnow(),
                        session_factory=session_factory,
                    )

                    # Download the file
                    downloaded_bytes = resume_position
                    mode = "ab" if resume_position > 0 else "wb"

                    # Throttle progress updates (only update every 5% or 5MB)
                    last_progress_update = 0
                    progress_update_threshold = max(total_size * 0.05, 5 * 1024 * 1024)  # 5% or 5MB

                    async with aiofiles.open(file_path, mode) as f:
                        async for chunk in response.aiter_bytes(chunk_size=self.chunk_size):
                            await f.write(chunk)
                            downloaded_bytes += len(chunk)

                            # Update progress only when threshold is reached
                            if total_size > 0:
                                bytes_since_update = downloaded_bytes - last_progress_update
                                if bytes_since_update >= progress_update_threshold:
                                    progress = downloaded_bytes / total_size
                                    await self._update_progress(
                                        download_record, progress, session_factory
                                    )
                                    last_progress_update = downloaded_bytes

                    # Final progress update to ensure we reach 100%
                    if total_size > 0 and downloaded_bytes > last_progress_update:
                        await self._update_progress(
                            download_record, downloaded_bytes / total_size, session_factory
                        )

                    # Verify file size
                    actual_size = file_path.stat().st_size
                    if total_size > 0 and actual_size != total_size:
                        error_msg = (
                            f"Size mismatch: expected {total_size}, got {actual_size}"
                        )
                        logger.warning(error_msg)
                        # Don't fail if close enough (within 1%)
                        if abs(actual_size - total_size) > (total_size * 0.01):
                            await self._mark_failed(
                                download_record, error_msg, session_factory
                            )
                            return False

                    # Mark as complete
                    logger.success(
                        f"Download complete: {episode.title} ({self._format_bytes(actual_size)})"
                    )
                    return await self._mark_complete(
                        download_record, file_path, session_factory
                    )

        except httpx.HTTPError as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(f"Download failed: {error_msg}")
            await self._mark_failed(download_record, error_msg, session_factory)
            return False

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Download failed: {error_msg}")
            await self._mark_failed(download_record, error_msg, session_factory)
            return False

    def _is_signed_url(self, url: str) -> bool:
        """
        Check if URL appears to be a signed/time-limited URL or uses tracking redirects.

        Signed URLs and tracking redirects are sensitive to HEAD requests and should be used directly.

        Args:
            url: URL to check

        Returns:
            True if URL appears to be signed or uses tracking
        """
        # Common signature parameters used by CDNs
        signature_indicators = [
            'Signature=',
            'Expires=',
            'Key-Pair-Id=',
            'Policy=',
            'signature=',
            'expires=',
            'token=',
            'auth=',
            'hmac=',
        ]

        # Common podcast tracking services that generate signed URLs after redirect
        tracking_services = [
            'podtrac.com',
            'mgln.ai',
            'chartable.com',
            'podsights.com',
            'podcorn.com',
            'blubrry.com',
            'feedpress.com',
            'backtracks.fm',
            'claritas.com',
            'podscribe.com',
            'spotify-analytics',
            'art19.com',
            'megaphone.fm',
            'simplecast.com',
        ]

        # Check for signature parameters
        if any(indicator in url for indicator in signature_indicators):
            return True

        # Check for tracking services
        if any(service in url.lower() for service in tracking_services):
            return True

        return False

    async def _resolve_url(self, url: str) -> str:
        """
        Resolve URL by following redirects to get the final destination.

        Args:
            url: Original URL that may have redirects

        Returns:
            Final URL after following all redirects
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }
            async with httpx.AsyncClient(follow_redirects=True) as client:
                # Use HEAD request to follow redirects without downloading content
                response = await client.head(url, headers=headers)
                final_url = str(response.url)
                if final_url != url:
                    logger.debug(f"URL redirected: {url} -> {final_url}")
                return final_url
        except Exception as e:
            logger.warning(f"Could not resolve URL redirects: {e}, using original URL")
            return url

    async def _update_status(
        self,
        download: Download,
        status: str,
        started_at: Optional[datetime] = None,
        session_factory=None,
    ):
        """Update download status in database."""
        download_id = download.id
        async for session in session_factory():
            # Fetch the download fresh from the database
            result = await session.execute(select(Download).where(Download.id == download_id))
            db_download = result.scalar_one()

            db_download.status = status
            if started_at:
                db_download.started_at = started_at
            db_download.updated_at = datetime.utcnow()

            await session.commit()
            break

    async def _update_progress(
        self, download: Download, progress: float, session_factory
    ):
        """Update download progress in database."""
        download_id = download.id
        async for session in session_factory():
            # Fetch the download fresh from the database
            result = await session.execute(select(Download).where(Download.id == download_id))
            db_download = result.scalar_one()

            db_download.progress = min(1.0, max(0.0, progress))
            db_download.updated_at = datetime.utcnow()

            await session.commit()
            break

    async def _mark_complete(
        self, download: Download, file_path: Path, session_factory
    ) -> bool:
        """Mark download as completed."""
        file_size = file_path.stat().st_size
        download_id = download.id

        async for session in session_factory():
            # Fetch the download fresh from the database
            from sqlalchemy import select
            result = await session.execute(select(Download).where(Download.id == download_id))
            db_download = result.scalar_one()

            db_download.status = "completed"
            db_download.progress = 1.0
            db_download.file_size = file_size
            db_download.completed_at = datetime.utcnow()
            db_download.updated_at = datetime.utcnow()
            db_download.error_message = None

            await session.commit()
            break

        return True

    async def _mark_failed(
        self, download: Download, error_message: str, session_factory
    ) -> bool:
        """Mark download as failed."""
        download_id = download.id
        async for session in session_factory():
            # Fetch the download fresh from the database
            result = await session.execute(select(Download).where(Download.id == download_id))
            db_download = result.scalar_one()

            db_download.status = "failed"
            db_download.error_message = error_message
            db_download.retry_count += 1
            db_download.updated_at = datetime.utcnow()

            await session.commit()
            break

        return False

    def _format_bytes(self, bytes: int) -> str:
        """Format bytes in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"


# Global download service instance
_download_service: Optional[DownloadService] = None


def get_download_service(timeout: int = 3600) -> DownloadService:
    """
    Get the global download service instance.

    Args:
        timeout: Download timeout in seconds

    Returns:
        DownloadService instance
    """
    global _download_service
    if _download_service is None:
        _download_service = DownloadService(timeout=timeout)
    return _download_service
