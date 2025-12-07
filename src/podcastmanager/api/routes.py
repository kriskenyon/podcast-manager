"""
API routes for the Podcast Manager.

This module defines all REST API endpoints for managing podcasts, episodes,
and downloads.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import Response
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from podcastmanager.api.dependencies import get_podcast_manager
from podcastmanager.api.schemas import (
    DownloadListResponse,
    DownloadResponse,
    EpisodeListResponse,
    EpisodeResponse,
    ErrorResponse,
    MessageResponse,
    OPMLImportResponse,
    OPMLPodcastInfo,
    PodcastCreate,
    PodcastListResponse,
    PodcastResponse,
    PodcastUpdate,
    PodcastWithEpisodesResponse,
)
from podcastmanager.core.podcast_manager import PodcastManager
from podcastmanager.db.database import get_db
from podcastmanager.db.models import Episode, Podcast
from podcastmanager.services.opml import OPMLService

# Create API router
router = APIRouter(prefix="/api", tags=["api"])


# ============================================================================
# Podcast Endpoints
# ============================================================================


@router.post(
    "/podcasts",
    response_model=PodcastResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new podcast",
    description="Add a new podcast by providing an RSS feed URL",
    responses={
        201: {"description": "Podcast created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid RSS feed or URL"},
        409: {"model": ErrorResponse, "description": "Podcast already exists"},
    },
)
async def create_podcast(
    podcast_data: PodcastCreate,
    podcast_manager: PodcastManager = Depends(get_podcast_manager),
):
    """
    Add a new podcast from an RSS feed.

    This will:
    - Fetch and parse the RSS feed
    - Extract podcast metadata
    - Discover and store the most recent episodes
    """
    try:
        podcast = await podcast_manager.add_podcast_from_rss(
            rss_url=podcast_data.rss_url,
            max_episodes_to_keep=podcast_data.max_episodes_to_keep,
            auto_download=podcast_data.auto_download,
        )

        if not podcast:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch or parse RSS feed. Please check the URL.",
            )

        return podcast

    except Exception as e:
        logger.error(f"Error creating podcast: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create podcast: {str(e)}",
        )


@router.get(
    "/podcasts",
    response_model=PodcastListResponse,
    summary="List all podcasts",
    description="Get a paginated list of all subscribed podcasts",
)
async def list_podcasts(
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(default=100, ge=1, le=100, description="Maximum number of items to return"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get a list of all podcasts with pagination.
    """
    # Get total count
    count_result = await session.execute(select(func.count(Podcast.id)))
    total = count_result.scalar_one()

    # Get podcasts
    result = await session.execute(
        select(Podcast)
        .order_by(Podcast.title)
        .offset(skip)
        .limit(limit)
    )
    podcasts = list(result.scalars().all())

    return PodcastListResponse(
        podcasts=podcasts,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/podcasts/{podcast_id}",
    response_model=PodcastResponse,
    summary="Get podcast details",
    description="Get detailed information about a specific podcast",
    responses={
        404: {"model": ErrorResponse, "description": "Podcast not found"},
    },
)
async def get_podcast(
    podcast_id: int,
    podcast_manager: PodcastManager = Depends(get_podcast_manager),
):
    """
    Get details for a specific podcast.
    """
    podcast = await podcast_manager.get_podcast_by_id(podcast_id)

    if not podcast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Podcast with ID {podcast_id} not found",
        )

    return podcast


@router.put(
    "/podcasts/{podcast_id}",
    response_model=PodcastResponse,
    summary="Update podcast settings",
    description="Update podcast configuration such as episode limits and auto-download",
    responses={
        404: {"model": ErrorResponse, "description": "Podcast not found"},
    },
)
async def update_podcast(
    podcast_id: int,
    podcast_data: PodcastUpdate,
    podcast_manager: PodcastManager = Depends(get_podcast_manager),
):
    """
    Update podcast settings.
    """
    podcast = await podcast_manager.update_podcast_settings(
        podcast_id=podcast_id,
        max_episodes_to_keep=podcast_data.max_episodes_to_keep,
        auto_download=podcast_data.auto_download,
    )

    if not podcast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Podcast with ID {podcast_id} not found",
        )

    return podcast


@router.delete(
    "/podcasts/{podcast_id}",
    response_model=MessageResponse,
    summary="Delete a podcast",
    description="Delete a podcast and all its episodes",
    responses={
        404: {"model": ErrorResponse, "description": "Podcast not found"},
    },
)
async def delete_podcast(
    podcast_id: int,
    podcast_manager: PodcastManager = Depends(get_podcast_manager),
):
    """
    Delete a podcast and all associated episodes.
    """
    success = await podcast_manager.delete_podcast(podcast_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Podcast with ID {podcast_id} not found",
        )

    return MessageResponse(
        message=f"Podcast {podcast_id} deleted successfully",
        success=True,
    )


@router.post(
    "/podcasts/{podcast_id}/refresh",
    response_model=MessageResponse,
    summary="Refresh podcast feed",
    description="Manually refresh a podcast feed to check for new episodes",
    responses={
        404: {"model": ErrorResponse, "description": "Podcast not found"},
    },
)
async def refresh_podcast(
    podcast_id: int,
    podcast_manager: PodcastManager = Depends(get_podcast_manager),
):
    """
    Manually refresh a podcast feed to discover new episodes.
    """
    success = await podcast_manager.refresh_podcast(podcast_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Podcast with ID {podcast_id} not found or refresh failed",
        )

    return MessageResponse(
        message=f"Podcast {podcast_id} refreshed successfully",
        success=True,
    )


# ============================================================================
# Episode Endpoints
# ============================================================================


@router.get(
    "/podcasts/{podcast_id}/episodes",
    response_model=EpisodeListResponse,
    summary="List podcast episodes",
    description="Get a paginated list of episodes for a specific podcast",
    responses={
        404: {"model": ErrorResponse, "description": "Podcast not found"},
    },
)
async def list_episodes(
    podcast_id: int,
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(default=100, ge=1, le=100, description="Maximum number of items to return"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get a list of episodes for a podcast with pagination.
    """
    # Check if podcast exists
    podcast_result = await session.execute(
        select(Podcast).where(Podcast.id == podcast_id)
    )
    podcast = podcast_result.scalar_one_or_none()

    if not podcast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Podcast with ID {podcast_id} not found",
        )

    # Get total count
    count_result = await session.execute(
        select(func.count(Episode.id)).where(Episode.podcast_id == podcast_id)
    )
    total = count_result.scalar_one()

    # Get episodes
    result = await session.execute(
        select(Episode)
        .where(Episode.podcast_id == podcast_id)
        .order_by(Episode.pub_date.desc())
        .offset(skip)
        .limit(limit)
    )
    episodes = list(result.scalars().all())

    return EpisodeListResponse(
        episodes=episodes,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/episodes/{episode_id}",
    response_model=EpisodeResponse,
    summary="Get episode details",
    description="Get detailed information about a specific episode",
    responses={
        404: {"model": ErrorResponse, "description": "Episode not found"},
    },
)
async def get_episode(
    episode_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Get details for a specific episode.
    """
    result = await session.execute(
        select(Episode).where(Episode.id == episode_id)
    )
    episode = result.scalar_one_or_none()

    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with ID {episode_id} not found",
        )

    return episode


# ============================================================================
# Combined Endpoints
# ============================================================================


@router.get(
    "/podcasts/{podcast_id}/with-episodes",
    response_model=PodcastWithEpisodesResponse,
    summary="Get podcast with episodes",
    description="Get podcast details along with all its episodes",
    responses={
        404: {"model": ErrorResponse, "description": "Podcast not found"},
    },
)
async def get_podcast_with_episodes(
    podcast_id: int,
    podcast_manager: PodcastManager = Depends(get_podcast_manager),
):
    """
    Get a podcast with all its episodes loaded.
    """
    podcast = await podcast_manager.get_podcast_with_episodes(podcast_id)

    if not podcast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Podcast with ID {podcast_id} not found",
        )

    return podcast


# ============================================================================
# Download Endpoints
# ============================================================================


@router.post(
    "/episodes/{episode_id}/download",
    response_model=DownloadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Queue episode for download",
    description="Add an episode to the download queue",
    responses={
        201: {"description": "Download queued successfully"},
        404: {"model": ErrorResponse, "description": "Episode not found"},
        507: {"model": ErrorResponse, "description": "Insufficient storage"},
    },
)
async def queue_download(
    episode_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Queue an episode for download.
    """
    from podcastmanager.core.download_engine import DownloadEngine
    from podcastmanager.core.exceptions import (
        EpisodeNotFoundException,
        InsufficientStorageException,
    )

    try:
        engine = DownloadEngine(session)
        download = await engine.queue_episode_download(episode_id)
        return download

    except EpisodeNotFoundException as e:
        logger.error(f"Episode not found: {episode_id} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except InsufficientStorageException as e:
        logger.warning(f"Insufficient storage for episode {episode_id}: {str(e)}")
        raise HTTPException(
            status_code=507,  # HTTP 507 Insufficient Storage
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Unexpected error queuing download for episode {episode_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue download: {str(e)}",
        )


@router.get(
    "/downloads",
    response_model=DownloadListResponse,
    summary="List all downloads",
    description="Get a paginated list of all downloads, optionally filtered by status",
)
async def list_downloads(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status (pending, downloading, completed, failed, deleted)",
    ),
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(default=100, ge=1, le=100, description="Maximum number of items to return"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get a list of all downloads with pagination.
    """
    from podcastmanager.core.download_engine import DownloadEngine
    from podcastmanager.db.models import Download

    engine = DownloadEngine(session)

    # Get total count
    query = select(func.count(Download.id))
    if status_filter:
        query = query.where(Download.status == status_filter)
    count_result = await session.execute(query)
    total = count_result.scalar_one()

    # Get downloads
    downloads = await engine.get_all_downloads(
        status=status_filter, skip=skip, limit=limit
    )

    return DownloadListResponse(
        downloads=downloads,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/downloads/{download_id}",
    response_model=DownloadResponse,
    summary="Get download status",
    description="Get the current status and progress of a download",
    responses={
        404: {"model": ErrorResponse, "description": "Download not found"},
    },
)
async def get_download(
    download_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Get the status of a specific download.
    """
    from podcastmanager.core.download_engine import DownloadEngine

    engine = DownloadEngine(session)
    download = await engine.get_download_status(download_id)

    if not download:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Download with ID {download_id} not found",
        )

    return download


@router.delete(
    "/downloads/{download_id}",
    response_model=MessageResponse,
    summary="Delete a download",
    description="Delete a download record and optionally the downloaded file",
    responses={
        404: {"model": ErrorResponse, "description": "Download not found"},
    },
)
async def delete_download(
    download_id: int,
    delete_file: bool = Query(
        default=True,
        description="Whether to delete the actual file",
    ),
    session: AsyncSession = Depends(get_db),
):
    """
    Delete a download and optionally the file.
    """
    from podcastmanager.core.download_engine import DownloadEngine

    engine = DownloadEngine(session)
    success = await engine.delete_download(download_id, delete_file=delete_file)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Download with ID {download_id} not found",
        )

    return MessageResponse(
        message=f"Download {download_id} deleted successfully",
        success=True,
    )


@router.post(
    "/downloads/process-queue",
    response_model=MessageResponse,
    summary="Process download queue",
    description="Manually trigger processing of pending downloads",
)
async def process_queue(
    session: AsyncSession = Depends(get_db),
):
    """
    Process all pending downloads in the queue.
    """
    from podcastmanager.core.download_engine import DownloadEngine

    engine = DownloadEngine(session)
    processed = await engine.process_download_queue()

    return MessageResponse(
        message=f"Processed {processed} downloads from queue",
        success=True,
    )


@router.post(
    "/downloads/retry-failed",
    response_model=MessageResponse,
    summary="Retry failed downloads",
    description="Retry all failed downloads that haven't exceeded max retries",
)
async def retry_failed(
    session: AsyncSession = Depends(get_db),
):
    """
    Retry failed downloads.
    """
    from podcastmanager.core.download_engine import DownloadEngine

    engine = DownloadEngine(session)
    retried = await engine.retry_failed_downloads()

    return MessageResponse(
        message=f"Retried {retried} failed downloads",
        success=True,
    )


# ============================================================================
# OPML Endpoints
# ============================================================================


@router.post(
    "/opml/parse",
    response_model=OPMLImportResponse,
    summary="Parse OPML file",
    description="Upload and parse an OPML file to preview podcasts before importing",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid OPML file"},
    },
)
async def parse_opml(
    file: UploadFile = File(..., description="OPML file to upload"),
):
    """
    Parse an OPML file and return the list of podcasts found.

    This endpoint only parses the file and returns information about the podcasts.
    It does not add them to the database. Use /opml/import to add the podcasts.
    """
    try:
        # Read file contents
        contents = await file.read()

        # Validate OPML
        if not OPMLService.validate_opml(contents):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OPML file format",
            )

        # Parse OPML
        podcasts = OPMLService.parse_opml(contents)

        return OPMLImportResponse(
            podcasts_found=len(podcasts),
            podcasts=[OPMLPodcastInfo(**p) for p in podcasts],
            message=f"Found {len(podcasts)} podcasts in OPML file",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing OPML file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse OPML file: {str(e)}",
        )


@router.post(
    "/opml/import",
    response_model=MessageResponse,
    summary="Import podcasts from OPML",
    description="Upload an OPML file and add all podcasts to the subscription list",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid OPML file"},
    },
)
async def import_opml(
    file: UploadFile = File(..., description="OPML file to upload"),
    max_episodes_to_keep: int = Query(
        default=3,
        ge=1,
        le=100,
        description="Default max episodes to keep for each podcast",
    ),
    auto_download: bool = Query(
        default=True,
        description="Enable auto-download for imported podcasts",
    ),
    podcast_manager: PodcastManager = Depends(get_podcast_manager),
):
    """
    Import podcasts from an OPML file.

    This will:
    - Parse the OPML file
    - Add each podcast to the database
    - Skip podcasts that are already subscribed
    """
    try:
        # Read file contents
        contents = await file.read()

        # Validate OPML
        if not OPMLService.validate_opml(contents):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OPML file format",
            )

        # Parse OPML
        podcasts = OPMLService.parse_opml(contents)

        # Add each podcast
        added = 0
        skipped = 0
        errors = 0

        for podcast_info in podcasts:
            try:
                # Check if podcast already exists
                existing = await podcast_manager.get_podcast_by_rss_url(podcast_info['rss_url'])

                if existing:
                    skipped += 1
                    logger.info(f"Skipped podcast (already exists): {podcast_info['title']}")
                    continue

                # Add new podcast
                podcast = await podcast_manager.add_podcast_from_rss(
                    rss_url=podcast_info['rss_url'],
                    max_episodes_to_keep=max_episodes_to_keep,
                    auto_download=auto_download,
                )

                if podcast:
                    added += 1
                    logger.info(f"Added podcast from OPML: {podcast_info['title']}")
                else:
                    skipped += 1
                    logger.warning(f"Skipped podcast (invalid feed): {podcast_info['title']}")

            except Exception as e:
                errors += 1
                logger.error(f"Error adding podcast {podcast_info['title']}: {e}")

        return MessageResponse(
            message=f"OPML import complete: {added} added, {skipped} skipped, {errors} errors",
            success=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing OPML file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import OPML file: {str(e)}",
        )


@router.get(
    "/opml/export",
    summary="Export podcasts to OPML",
    description="Download an OPML file containing all current podcast subscriptions",
    response_class=Response,
)
async def export_opml(
    session: AsyncSession = Depends(get_db),
):
    """
    Export all subscribed podcasts to an OPML file.

    Returns an OPML XML file that can be imported into other podcast applications.
    """
    try:
        # Get all podcasts
        result = await session.execute(
            select(Podcast).order_by(Podcast.title)
        )
        podcasts = list(result.scalars().all())

        # Generate OPML
        opml_content = OPMLService.generate_opml(
            podcasts=podcasts,
            title="Podcast Manager Subscriptions",
        )

        # Return as downloadable file
        return Response(
            content=opml_content,
            media_type="application/xml",
            headers={
                "Content-Disposition": "attachment; filename=podcast_subscriptions.opml"
            },
        )

    except Exception as e:
        logger.error(f"Error exporting OPML: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export OPML: {str(e)}",
        )


# ============================================================================
# Background Jobs Endpoints
# ============================================================================


@router.get(
    "/jobs",
    summary="List scheduled jobs",
    description="Get information about all scheduled background jobs",
)
async def list_jobs():
    """
    Get information about scheduled background jobs.
    """
    from podcastmanager.tasks.worker import get_scheduler

    try:
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        return {"jobs": jobs}
    except RuntimeError:
        return {"jobs": [], "message": "Scheduler not initialized"}


@router.post(
    "/jobs/{job_id}/trigger",
    response_model=MessageResponse,
    summary="Trigger a job",
    description="Manually trigger a background job to run immediately",
)
async def trigger_job(job_id: str):
    """
    Manually trigger a background job.
    """
    from podcastmanager.tasks.worker import get_scheduler

    try:
        scheduler = get_scheduler()
        success = scheduler.trigger_job(job_id)

        if success:
            return MessageResponse(
                message=f"Job '{job_id}' triggered successfully",
                success=True,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job '{job_id}' not found",
            )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scheduler not initialized",
        )


@router.post(
    "/jobs/{job_id}/pause",
    response_model=MessageResponse,
    summary="Pause a job",
    description="Pause a scheduled background job",
)
async def pause_job(job_id: str):
    """
    Pause a background job.
    """
    from podcastmanager.tasks.worker import get_scheduler

    try:
        scheduler = get_scheduler()
        success = scheduler.pause_job(job_id)

        if success:
            return MessageResponse(
                message=f"Job '{job_id}' paused successfully",
                success=True,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job '{job_id}' not found",
            )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scheduler not initialized",
        )


@router.post(
    "/jobs/{job_id}/resume",
    response_model=MessageResponse,
    summary="Resume a job",
    description="Resume a paused background job",
)
async def resume_job(job_id: str):
    """
    Resume a paused background job.
    """
    from podcastmanager.tasks.worker import get_scheduler

    try:
        scheduler = get_scheduler()
        success = scheduler.resume_job(job_id)

        if success:
            return MessageResponse(
                message=f"Job '{job_id}' resumed successfully",
                success=True,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job '{job_id}' not found",
            )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scheduler not initialized",
        )
