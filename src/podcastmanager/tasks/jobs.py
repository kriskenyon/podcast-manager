"""
Background job implementations.

This module contains the actual job functions that are executed
by the task scheduler for automated podcast management.
"""

from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy import select

from podcastmanager.config import get_settings
from podcastmanager.core.download_engine import DownloadEngine
from podcastmanager.core.exceptions import (
    EpisodeNotFoundException,
    InsufficientStorageException,
)
from podcastmanager.core.podcast_manager import PodcastManager
from podcastmanager.db.database import get_db_manager
from podcastmanager.db.models import Download, Episode, Podcast
from podcastmanager.services.file_manager import get_file_manager


async def refresh_all_podcasts_job():
    """
    Background job to refresh all podcast feeds.

    This job:
    1. Fetches the latest RSS feed for each podcast
    2. Discovers new episodes
    3. Queues new episodes for download (if auto_download is enabled)
    """
    logger.info("=== Starting podcast feed refresh job ===")
    settings = get_settings()

    try:
        db_manager = get_db_manager()
        async for session in db_manager.get_session():
            # Get all podcasts
            result = await session.execute(select(Podcast))
            podcasts = list(result.scalars().all())

            if not podcasts:
                logger.info("No podcasts to refresh")
                return

            logger.info(f"Refreshing {len(podcasts)} podcasts...")

            refreshed = 0
            new_episodes_total = 0

            for podcast in podcasts:
                try:
                    logger.debug(f"Refreshing: {podcast.title}")

                    # Create podcast manager for this session
                    podcast_manager = PodcastManager(session)

                    # Refresh the podcast
                    success = await podcast_manager.refresh_podcast(podcast.id)

                    if success:
                        refreshed += 1

                        # If auto-download is enabled, queue new episodes
                        if podcast.auto_download:
                            # Get the N most recent episodes
                            result = await session.execute(
                                select(Episode)
                                .where(Episode.podcast_id == podcast.id)
                                .order_by(Episode.pub_date.desc())
                                .limit(podcast.max_episodes_to_keep)
                            )
                            recent_episodes = list(result.scalars().all())

                            # Only queue episodes that don't have a completed or pending download
                            download_engine = DownloadEngine(session)
                            episodes_to_queue = []

                            for episode in recent_episodes:
                                # Check if this episode already has a download
                                dl_result = await session.execute(
                                    select(Download)
                                    .where(Download.episode_id == episode.id)
                                    .where(Download.status.in_(["completed", "downloading", "pending"]))
                                )
                                existing_download = dl_result.scalar_one_or_none()

                                if not existing_download:
                                    episodes_to_queue.append(episode)

                            if episodes_to_queue:
                                logger.info(
                                    f"Queueing {len(episodes_to_queue)} new episodes from {podcast.title}"
                                )

                                for episode in episodes_to_queue:
                                    try:
                                        await download_engine.queue_episode_download(
                                            episode.id
                                        )
                                        new_episodes_total += 1
                                    except InsufficientStorageException as e:
                                        logger.warning(
                                            f"Skipping {episode.title}: {str(e)}"
                                        )
                                        # Continue to next episode, don't fail the whole job
                                        continue
                                    except EpisodeNotFoundException as e:
                                        logger.error(
                                            f"Episode not found: {str(e)}"
                                        )
                                        continue

                except Exception as e:
                    logger.error(f"Error refreshing {podcast.title}: {e}")
                    continue

            logger.success(
                f"Feed refresh complete: {refreshed}/{len(podcasts)} podcasts refreshed, "
                f"{new_episodes_total} episodes queued"
            )

    except Exception as e:
        logger.error(f"Feed refresh job failed: {e}")

    finally:
        logger.info("=== Podcast feed refresh job finished ===")


async def process_download_queue_job():
    """
    Background job to process pending downloads.

    This job:
    1. Finds all pending downloads
    2. Downloads episodes up to the concurrent limit
    3. Updates download status
    """
    logger.info("=== Starting download queue processor ===")

    try:
        db_manager = get_db_manager()
        async for session in db_manager.get_session():
            # Check for pending downloads
            result = await session.execute(
                select(Download).where(Download.status == "pending")
            )
            pending = list(result.scalars().all())

            if not pending:
                logger.debug("No pending downloads")
                return

            logger.info(f"Processing {len(pending)} pending downloads...")

            # Create download engine
            download_engine = DownloadEngine(session)

            # Process the queue
            processed = await download_engine.process_download_queue()

            logger.success(f"Download queue processed: {processed} downloads")

    except Exception as e:
        logger.error(f"Download queue processor failed: {e}")

    finally:
        logger.info("=== Download queue processor finished ===")


async def cleanup_old_episodes_job():
    """
    Background job to cleanup old episodes.

    This job:
    1. For each podcast, finds episodes beyond max_episodes_to_keep
    2. If Plex integration enabled, checks play status before deleting
    3. Deletes old episode files and database records
    4. Cleans up empty directories

    With Plex Integration:
    - Always keeps the N most recent episodes
    - For older episodes: only deletes if played in Plex
    - Keeps unplayed episodes until they're watched

    Without Plex Integration:
    - Simply deletes episodes beyond the max_episodes_to_keep limit
    """
    logger.info("=== Starting episode cleanup job ===")

    settings = get_settings()

    # Initialize Plex service if enabled
    plex_service = None
    if settings.plex_enabled:
        try:
            from podcastmanager.services.plex_service import get_plex_service, is_plex_available

            if is_plex_available():
                if settings.plex_token and settings.plex_url and settings.plex_library:
                    plex_service = get_plex_service(
                        settings.plex_url,
                        settings.plex_token,
                        settings.plex_library
                    )
                    if plex_service:
                        logger.success(
                            f"Plex integration enabled - will check play status before cleanup"
                        )
                        # Test connection
                        if not plex_service.test_connection():
                            logger.warning("Plex connection test failed, disabling Plex integration")
                            plex_service = None
                else:
                    logger.warning(
                        "Plex enabled but missing configuration (URL, token, or library). "
                        "Using standard cleanup."
                    )
            else:
                logger.warning(
                    "Plex enabled but PlexAPI not installed. "
                    "Install with: pip install PlexAPI"
                )
        except Exception as e:
            logger.warning(f"Plex integration failed: {e}. Using standard cleanup.")
            plex_service = None

    try:
        db_manager = get_db_manager()
        file_manager = get_file_manager()
        async for session in db_manager.get_session():
            # Get all podcasts
            result = await session.execute(select(Podcast))
            podcasts = list(result.scalars().all())

            if not podcasts:
                logger.info("No podcasts to clean up")
                return

            logger.info(f"Cleaning up episodes for {len(podcasts)} podcasts...")

            total_deleted = 0
            total_kept_unplayed = 0
            total_space_freed = 0

            for podcast in podcasts:
                try:
                    # Get all completed downloads for this podcast, ordered by pub_date
                    result = await session.execute(
                        select(Download, Episode)
                        .join(Episode)
                        .where(Episode.podcast_id == podcast.id)
                        .where(Download.status == "completed")
                        .order_by(Episode.pub_date.desc())
                    )
                    downloads_with_episodes = list(result.all())

                    # Determine which episodes to delete
                    to_delete = []

                    for i, (download, episode) in enumerate(downloads_with_episodes):
                        # Always keep the N most recent episodes
                        if i < podcast.max_episodes_to_keep:
                            logger.debug(
                                f"Keeping (within limit): {episode.title}"
                            )
                            continue

                        # For older episodes, check Plex play status if enabled
                        if plex_service and download.file_path:
                            full_path = str(file_manager.base_path / download.file_path)

                            if plex_service.is_episode_played(full_path):
                                logger.info(
                                    f"Marking for deletion (played in Plex): {episode.title}"
                                )
                                to_delete.append((download, episode))
                            else:
                                logger.info(
                                    f"Keeping (unplayed in Plex): {episode.title}"
                                )
                                total_kept_unplayed += 1
                        else:
                            # No Plex integration - delete based on age only
                            logger.debug(
                                f"Marking for deletion (beyond limit): {episode.title}"
                            )
                            to_delete.append((download, episode))

                    if to_delete:
                        logger.info(
                            f"Deleting {len(to_delete)} old episodes from {podcast.title}"
                        )

                        for download, episode in to_delete:
                            # Get file size before deletion
                            if download.file_path:
                                full_path = file_manager.base_path / download.file_path
                                file_size = file_manager.get_file_size(full_path)
                                if file_size:
                                    total_space_freed += file_size

                                # Delete the file
                                file_manager.delete_file(full_path)

                            # Delete the download record
                            await session.delete(download)
                            total_deleted += 1

                        await session.commit()

                except Exception as e:
                    logger.error(f"Error cleaning up {podcast.title}: {e}")
                    continue

            # Cleanup empty directories
            file_manager.cleanup_empty_directories()

            cleanup_summary = (
                f"Cleanup complete: {total_deleted} episodes deleted, "
                f"{file_manager.format_file_size(total_space_freed)} freed"
            )

            if plex_service:
                cleanup_summary += f", {total_kept_unplayed} unplayed episodes kept"

            logger.success(cleanup_summary)

    except Exception as e:
        logger.error(f"Cleanup job failed: {e}")

    finally:
        logger.info("=== Episode cleanup job finished ===")


async def retry_failed_downloads_job():
    """
    Background job to retry failed downloads.

    This job:
    1. Finds failed downloads that haven't exceeded max retries
    2. Resets them to pending status
    3. They will be picked up by the download queue processor
    """
    logger.info("=== Starting retry failed downloads job ===")

    try:
        db_manager = get_db_manager()
        async for session in db_manager.get_session():
            download_engine = DownloadEngine(session)
            retried = await download_engine.retry_failed_downloads()

            if retried > 0:
                logger.success(f"Retried {retried} failed downloads")
            else:
                logger.debug("No failed downloads to retry")

    except Exception as e:
        logger.error(f"Retry failed downloads job failed: {e}")

    finally:
        logger.info("=== Retry failed downloads job finished ===")


async def check_disk_space_job():
    """
    Background job to check available disk space.

    This job:
    1. Checks available disk space
    2. Logs a warning if space is low
    3. Can pause downloads if critically low
    """
    logger.info("=== Starting disk space check ===")

    try:
        file_manager = get_file_manager()
        available = file_manager.get_available_space()
        available_gb = available / (1024**3)

        logger.info(f"Available disk space: {available_gb:.2f} GB")

        # Warning thresholds
        if available_gb < 1:
            logger.error(
                "CRITICAL: Less than 1 GB free space! Downloads may fail."
            )
        elif available_gb < 5:
            logger.warning("WARNING: Less than 5 GB free space remaining")
        elif available_gb < 10:
            logger.info("INFO: Less than 10 GB free space remaining")

    except Exception as e:
        logger.error(f"Disk space check failed: {e}")

    finally:
        logger.info("=== Disk space check finished ===")
