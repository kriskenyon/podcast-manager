"""
Download engine for managing podcast episode downloads.

This module provides the core download orchestration including queue management,
concurrent downloads, retry logic, and status tracking.
"""

import asyncio
from datetime import datetime
from typing import List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from podcastmanager.core.exceptions import (
    EpisodeNotFoundException,
    InsufficientStorageException,
)
from podcastmanager.db.models import Download, Episode, Podcast
from podcastmanager.services.download_service import get_download_service
from podcastmanager.services.file_manager import get_file_manager


class DownloadEngine:
    """
    Engine for managing podcast episode downloads.

    Features:
    - Download queue management
    - Concurrent download limiting
    - Automatic retry for failed downloads
    - Progress tracking
    - File organization
    """

    def __init__(
        self,
        session: AsyncSession,
        max_concurrent: int = 3,
        max_retries: int = 3,
    ):
        """
        Initialize the download engine.

        Args:
            session: SQLAlchemy async session
            max_concurrent: Maximum concurrent downloads
            max_retries: Maximum retry attempts for failed downloads
        """
        self.session = session
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.download_service = get_download_service()
        self.file_manager = get_file_manager()

        # Semaphore to limit concurrent downloads
        self.download_semaphore = asyncio.Semaphore(max_concurrent)

    async def queue_episode_download(self, episode_id: int) -> Download:
        """
        Queue an episode for download.

        Creates a download record in the database with status 'pending'.

        Args:
            episode_id: ID of the episode to download

        Returns:
            Download record

        Raises:
            EpisodeNotFoundException: If episode not found
            InsufficientStorageException: If not enough disk space
        """
        # Get the episode with podcast
        result = await self.session.execute(
            select(Episode)
            .options(selectinload(Episode.podcast))
            .where(Episode.id == episode_id)
        )
        episode = result.scalar_one_or_none()

        if not episode:
            logger.error(f"Episode {episode_id} not found")
            raise EpisodeNotFoundException(f"Episode with ID {episode_id} not found")

        # Check if already downloaded or queued
        result = await self.session.execute(
            select(Download).where(Download.episode_id == episode_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            if existing.status == "completed":
                logger.info(f"Episode already downloaded: {episode.title}")
                return existing
            elif existing.status in ("pending", "downloading"):
                logger.info(f"Episode already queued: {episode.title}")
                return existing
            else:
                # Failed or deleted - reset for retry
                logger.info(f"Retrying download for: {episode.title}")
                existing.status = "pending"
                existing.progress = 0.0
                existing.updated_at = datetime.utcnow()
                await self.session.commit()
                return existing

        # Generate file path
        full_path, relative_path = self.file_manager.get_episode_file_path(
            episode, episode.podcast
        )

        # Check disk space
        if episode.file_size:
            available_space = self.file_manager.get_available_space()
            buffer_bytes = int(1.0 * 1024 * 1024 * 1024)  # 1GB buffer
            required_with_buffer = episode.file_size + buffer_bytes

            if available_space < required_with_buffer:
                logger.error(
                    f"Insufficient disk space for: {episode.title} "
                    f"(required: {required_with_buffer / (1024*1024):.1f} MB, "
                    f"available: {available_space / (1024*1024):.1f} MB)"
                )
                raise InsufficientStorageException(
                    required_bytes=required_with_buffer,
                    available_bytes=available_space,
                )

        # Create download record
        download = Download(
            episode_id=episode_id,
            status="pending",
            file_path=str(relative_path),
            progress=0.0,
            retry_count=0,
        )

        self.session.add(download)
        await self.session.commit()

        logger.info(f"Queued download: {episode.title}")
        return download

    async def download_episode(self, download_id: int) -> bool:
        """
        Download a single episode.

        Args:
            download_id: Download record ID

        Returns:
            True if download succeeded, False otherwise
        """
        async with self.download_semaphore:
            # Get download with episode and podcast
            result = await self.session.execute(
                select(Download)
                .options(
                    selectinload(Download.episode).selectinload(Episode.podcast)
                )
                .where(Download.id == download_id)
            )
            download = result.scalar_one_or_none()

            if not download:
                logger.error(f"Download {download_id} not found")
                return False

            episode = download.episode
            podcast = episode.podcast

            # Get full file path
            full_path = self.file_manager.base_path / download.file_path

            logger.info(
                f"Downloading [{podcast.title}] {episode.title} -> {full_path}"
            )

            # Perform the download
            success = await self.download_service.download_episode(
                episode=episode,
                file_path=full_path,
                download_record=download,
                session_factory=self._get_session,
            )

            return success

    async def process_download_queue(self) -> int:
        """
        Process all pending downloads in the queue.

        Downloads episodes concurrently up to max_concurrent limit.

        Returns:
            Number of episodes processed
        """
        logger.info("Processing download queue...")

        # Get all pending downloads
        result = await self.session.execute(
            select(Download)
            .where(Download.status == "pending")
            .order_by(Download.created_at)
        )
        pending = list(result.scalars().all())

        if not pending:
            logger.info("No pending downloads")
            return 0

        logger.info(f"Found {len(pending)} pending downloads")

        # Create download tasks
        tasks = [self.download_episode(d.id) for d in pending]

        # Execute downloads concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes
        successful = sum(1 for r in results if r is True)

        logger.info(
            f"Download queue processed: {successful}/{len(pending)} successful"
        )

        return len(pending)

    async def retry_failed_downloads(self) -> int:
        """
        Retry failed downloads that haven't exceeded max_retries.

        Returns:
            Number of downloads retried
        """
        logger.info("Retrying failed downloads...")

        # Get failed downloads that can be retried
        result = await self.session.execute(
            select(Download)
            .where(Download.status == "failed")
            .where(Download.retry_count < self.max_retries)
            .order_by(Download.updated_at)
        )
        failed = list(result.scalars().all())

        if not failed:
            logger.info("No failed downloads to retry")
            return 0

        logger.info(f"Found {len(failed)} failed downloads to retry")

        # Reset to pending for retry
        for download in failed:
            download.status = "pending"
            download.progress = 0.0
            download.error_message = None
            download.updated_at = datetime.utcnow()

        await self.session.commit()

        # Process the retries
        await self.process_download_queue()

        return len(failed)

    async def cancel_download(self, download_id: int) -> bool:
        """
        Cancel a pending or active download.

        Args:
            download_id: Download record ID

        Returns:
            True if cancelled, False if not found or already completed
        """
        result = await self.session.execute(
            select(Download).where(Download.id == download_id)
        )
        download = result.scalar_one_or_none()

        if not download:
            return False

        if download.status == "completed":
            logger.warning(f"Cannot cancel completed download: {download_id}")
            return False

        download.status = "deleted"
        download.updated_at = datetime.utcnow()
        await self.session.commit()

        logger.info(f"Cancelled download: {download_id}")
        return True

    async def delete_download(self, download_id: int, delete_file: bool = True) -> bool:
        """
        Delete a download record and optionally the file.

        Args:
            download_id: Download record ID
            delete_file: Whether to delete the actual file

        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            select(Download).where(Download.id == download_id)
        )
        download = result.scalar_one_or_none()

        if not download:
            return False

        # Delete file if requested and it exists
        if delete_file and download.file_path:
            full_path = self.file_manager.base_path / download.file_path
            self.file_manager.delete_file(full_path)

        # Delete download record
        await self.session.delete(download)
        await self.session.commit()

        logger.info(f"Deleted download: {download_id}")
        return True

    async def get_download_status(self, download_id: int) -> Optional[Download]:
        """
        Get the current status of a download.

        Args:
            download_id: Download record ID

        Returns:
            Download record or None if not found
        """
        result = await self.session.execute(
            select(Download).where(Download.id == download_id)
        )
        return result.scalar_one_or_none()

    async def get_all_downloads(
        self, status: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[Download]:
        """
        Get all downloads, optionally filtered by status.

        Args:
            status: Filter by status (pending, downloading, completed, failed, deleted)
            skip: Number to skip for pagination
            limit: Maximum number to return

        Returns:
            List of Download records
        """
        query = select(Download).order_by(Download.created_at.desc())

        if status:
            query = query.where(Download.status == status)

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _get_session(self):
        """Helper to get a new session for download service."""
        # This is a simplified version - in practice, you'd want to use
        # the database manager's session factory
        from podcastmanager.db.database import get_db

        async for session in get_db():
            yield session
