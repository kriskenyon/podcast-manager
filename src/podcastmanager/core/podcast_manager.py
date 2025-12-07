"""
Podcast management service.

This module provides the business logic for managing podcasts and episodes,
including adding podcasts, refreshing feeds, and discovering new episodes.
"""

from datetime import datetime
from typing import List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from podcastmanager.core.rss_parser import get_rss_parser
from podcastmanager.db.models import Episode, Podcast
from podcastmanager.utils.validators import sanitize_folder_name


class PodcastManager:
    """
    Service for managing podcasts and episodes.

    Handles all podcast-related business logic including:
    - Adding podcasts from RSS feeds
    - Refreshing podcast feeds
    - Discovering and storing new episodes
    - Managing podcast metadata
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the podcast manager.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.rss_parser = get_rss_parser()

    async def add_podcast_from_rss(
        self,
        rss_url: str,
        max_episodes_to_keep: int = 3,
        auto_download: bool = True,
    ) -> Optional[Podcast]:
        """
        Add a new podcast from an RSS feed URL.

        This will:
        1. Fetch and parse the RSS feed
        2. Extract podcast metadata
        3. Create a podcast entry in the database
        4. Discover and store initial episodes

        Args:
            rss_url: URL of the podcast RSS feed
            max_episodes_to_keep: Maximum number of episodes to keep
            auto_download: Whether to automatically download new episodes

        Returns:
            Created Podcast object or None if failed
        """
        logger.info(f"Adding podcast from RSS: {rss_url}")

        # Check if podcast already exists
        existing = await self.get_podcast_by_rss_url(rss_url)
        if existing:
            logger.warning(f"Podcast already exists: {existing.title}")
            return existing

        # Fetch and parse the feed
        feed = await self.rss_parser.fetch_feed(rss_url)
        if not feed:
            logger.error(f"Failed to fetch RSS feed: {rss_url}")
            return None

        # Extract podcast metadata
        metadata = self.rss_parser.parse_podcast_metadata(feed, rss_url)

        # Create download path (sanitized folder name)
        download_path = sanitize_folder_name(metadata['title'])

        # Create podcast object
        podcast = Podcast(
            title=metadata['title'],
            description=metadata['description'],
            author=metadata['author'],
            rss_url=metadata['rss_url'],
            image_url=metadata['image_url'],
            website_url=metadata['website_url'],
            category=metadata['category'],
            language=metadata['language'],
            max_episodes_to_keep=max_episodes_to_keep,
            auto_download=auto_download,
            download_path=download_path,
            last_checked=datetime.utcnow(),
        )

        # Add to database
        self.session.add(podcast)
        await self.session.flush()  # Get the podcast ID

        logger.success(f"Created podcast: {podcast.title} (ID: {podcast.id})")

        # Discover and add episodes
        await self._discover_episodes(podcast, feed)

        await self.session.commit()
        return podcast

    async def refresh_podcast(self, podcast_id: int) -> bool:
        """
        Refresh a podcast by fetching the latest feed and discovering new episodes.

        Args:
            podcast_id: ID of the podcast to refresh

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Refreshing podcast ID: {podcast_id}")

        # Get the podcast
        podcast = await self.get_podcast_by_id(podcast_id)
        if not podcast:
            logger.error(f"Podcast not found: {podcast_id}")
            return False

        # Fetch the latest feed
        feed = await self.rss_parser.fetch_feed(podcast.rss_url)
        if not feed:
            logger.error(f"Failed to refresh podcast: {podcast.title}")
            return False

        # Update podcast metadata
        metadata = self.rss_parser.parse_podcast_metadata(feed, podcast.rss_url)
        podcast.title = metadata['title']
        podcast.description = metadata['description']
        podcast.author = metadata['author']
        podcast.image_url = metadata['image_url']
        podcast.website_url = metadata['website_url']
        podcast.category = metadata['category']
        podcast.language = metadata['language']
        podcast.last_checked = datetime.utcnow()

        # Discover new episodes
        new_episodes_count = await self._discover_episodes(podcast, feed)

        await self.session.commit()

        logger.success(f"Refreshed podcast: {podcast.title}, found {new_episodes_count} new episodes")
        return True

    async def _discover_episodes(self, podcast: Podcast, feed) -> int:
        """
        Discover and add episodes from a feed.

        Only adds new episodes (based on GUID) and respects the max_episodes_to_keep limit.

        Args:
            podcast: Podcast object
            feed: Parsed RSS feed

        Returns:
            Number of new episodes added
        """
        # Parse all episodes from feed
        episode_data_list = self.rss_parser.parse_episodes(feed)

        if not episode_data_list:
            logger.info(f"No episodes found in feed for: {podcast.title}")
            return 0

        # Get existing episode GUIDs for this podcast
        result = await self.session.execute(
            select(Episode.guid).where(Episode.podcast_id == podcast.id)
        )
        existing_guids = {row[0] for row in result.fetchall()}

        # Filter out existing episodes
        new_episode_data = [
            ep for ep in episode_data_list if ep['guid'] not in existing_guids
        ]

        if not new_episode_data:
            logger.info(f"No new episodes found for: {podcast.title}")
            return 0

        # Limit to max_episodes_to_keep most recent episodes
        # Sort by pub_date (newest first)
        new_episode_data.sort(
            key=lambda x: x['pub_date'] or datetime.min,
            reverse=True
        )
        new_episode_data = new_episode_data[:podcast.max_episodes_to_keep]

        # Create episode objects
        added_count = 0
        for episode_data in new_episode_data:
            try:
                # Use a savepoint (nested transaction) for each episode
                # This allows us to rollback individual episodes without affecting others
                async with self.session.begin_nested():
                    episode = Episode(
                        podcast_id=podcast.id,
                        title=episode_data['title'],
                        description=episode_data['description'],
                        guid=episode_data['guid'],
                        pub_date=episode_data['pub_date'],
                        duration=episode_data['duration'],
                        audio_url=episode_data['audio_url'],
                        file_size=episode_data['file_size'],
                        file_type=episode_data['file_type'],
                        episode_number=episode_data['episode_number'],
                        season_number=episode_data['season_number'],
                    )
                    self.session.add(episode)
                    await self.session.flush()
                added_count += 1
            except Exception as e:
                # If episode already exists (GUID conflict), skip it and continue
                if "UNIQUE constraint failed" in str(e) or "IntegrityError" in str(type(e).__name__):
                    logger.warning(f"Skipping duplicate episode (GUID: {episode_data['guid']}): {episode_data['title']}")
                    # The nested transaction is automatically rolled back on exception
                    continue
                else:
                    # Re-raise other errors
                    raise

        if added_count > 0:
            logger.success(f"Added {added_count} new episodes for: {podcast.title}")
        else:
            logger.info(f"No new episodes added for: {podcast.title} (all episodes already exist)")
        return added_count

    async def get_podcast_by_id(self, podcast_id: int) -> Optional[Podcast]:
        """
        Get a podcast by ID.

        Args:
            podcast_id: Podcast ID

        Returns:
            Podcast object or None if not found
        """
        result = await self.session.execute(
            select(Podcast).where(Podcast.id == podcast_id)
        )
        return result.scalar_one_or_none()

    async def get_podcast_by_rss_url(self, rss_url: str) -> Optional[Podcast]:
        """
        Get a podcast by RSS URL.

        Args:
            rss_url: RSS feed URL

        Returns:
            Podcast object or None if not found
        """
        result = await self.session.execute(
            select(Podcast).where(Podcast.rss_url == rss_url)
        )
        return result.scalar_one_or_none()

    async def get_all_podcasts(self, skip: int = 0, limit: int = 100) -> List[Podcast]:
        """
        Get all podcasts with pagination.

        Args:
            skip: Number of podcasts to skip
            limit: Maximum number of podcasts to return

        Returns:
            List of Podcast objects
        """
        result = await self.session.execute(
            select(Podcast)
            .order_by(Podcast.title)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_podcast_with_episodes(self, podcast_id: int) -> Optional[Podcast]:
        """
        Get a podcast with all its episodes loaded.

        Args:
            podcast_id: Podcast ID

        Returns:
            Podcast object with episodes or None if not found
        """
        result = await self.session.execute(
            select(Podcast)
            .options(selectinload(Podcast.episodes))
            .where(Podcast.id == podcast_id)
        )
        return result.scalar_one_or_none()

    async def get_podcast_episodes(
        self,
        podcast_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Episode]:
        """
        Get episodes for a podcast with pagination.

        Args:
            podcast_id: Podcast ID
            skip: Number of episodes to skip
            limit: Maximum number of episodes to return

        Returns:
            List of Episode objects
        """
        result = await self.session.execute(
            select(Episode)
            .where(Episode.podcast_id == podcast_id)
            .order_by(Episode.pub_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_podcast(self, podcast_id: int) -> bool:
        """
        Delete a podcast and all its episodes.

        Args:
            podcast_id: Podcast ID

        Returns:
            True if deleted, False if not found
        """
        podcast = await self.get_podcast_by_id(podcast_id)
        if not podcast:
            logger.warning(f"Podcast not found for deletion: {podcast_id}")
            return False

        logger.info(f"Deleting podcast: {podcast.title} (ID: {podcast_id})")

        await self.session.delete(podcast)
        await self.session.commit()

        logger.success(f"Deleted podcast: {podcast.title}")
        return True

    async def update_podcast_settings(
        self,
        podcast_id: int,
        max_episodes_to_keep: Optional[int] = None,
        auto_download: Optional[bool] = None,
    ) -> Optional[Podcast]:
        """
        Update podcast settings.

        Args:
            podcast_id: Podcast ID
            max_episodes_to_keep: New episode limit (optional)
            auto_download: New auto-download setting (optional)

        Returns:
            Updated Podcast object or None if not found
        """
        podcast = await self.get_podcast_by_id(podcast_id)
        if not podcast:
            return None

        if max_episodes_to_keep is not None:
            podcast.max_episodes_to_keep = max_episodes_to_keep
            logger.info(f"Updated max episodes for {podcast.title}: {max_episodes_to_keep}")

        if auto_download is not None:
            podcast.auto_download = auto_download
            logger.info(f"Updated auto-download for {podcast.title}: {auto_download}")

        podcast.updated_at = datetime.utcnow()
        await self.session.commit()

        return podcast
