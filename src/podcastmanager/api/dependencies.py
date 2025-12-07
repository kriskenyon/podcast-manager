"""
API dependencies for dependency injection.

This module provides FastAPI dependencies for injecting services
and other components into route handlers.
"""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from podcastmanager.core.podcast_manager import PodcastManager
from podcastmanager.db.database import get_db


async def get_podcast_manager(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[PodcastManager, None]:
    """
    Dependency to get a PodcastManager instance.

    Args:
        session: Database session (injected)

    Yields:
        PodcastManager: Podcast manager service
    """
    yield PodcastManager(session)
