"""
Database initialization script.

This script creates the database tables and optionally seeds initial data.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastmanager.config import get_settings
from podcastmanager.db.database import init_db
from podcastmanager.db.models import Setting
from podcastmanager.utils.logging import setup_logging
from loguru import logger
from sqlalchemy import select


DEFAULT_SETTINGS = {
    "download_path": "/mnt/media/podcasts",
    "max_concurrent_downloads": "3",
    "default_max_episodes": "3",
    "feed_refresh_interval": "3600",
    "auto_cleanup_enabled": "true",
    "apple_podcast_search_limit": "20",
}


async def create_default_settings(db_manager):
    """Create default settings in the database."""
    async for session in db_manager.get_session():
        # Check if settings already exist
        result = await session.execute(select(Setting))
        existing_settings = result.scalars().all()

        if existing_settings:
            logger.info(f"Found {len(existing_settings)} existing settings, skipping defaults")
            return

        # Create default settings
        logger.info("Creating default settings...")
        for key, value in DEFAULT_SETTINGS.items():
            setting = Setting(
                key=key,
                value=value,
                description=f"Default setting for {key.replace('_', ' ')}",
            )
            session.add(setting)

        await session.commit()
        logger.success(f"Created {len(DEFAULT_SETTINGS)} default settings")


async def main():
    """Main initialization function."""
    # Set up logging
    settings = get_settings()
    setup_logging(log_level="INFO")

    logger.info("=" * 60)
    logger.info("Podcast Manager - Database Initialization")
    logger.info("=" * 60)

    # Initialize database manager
    logger.info(f"Database URL: {settings.database_url}")
    db_manager = init_db(settings.database_url, echo=True)

    try:
        # Create all tables
        logger.info("Creating database tables...")
        await db_manager.create_tables()
        logger.success("Database tables created successfully")

        # Create default settings
        await create_default_settings(db_manager)

        logger.info("=" * 60)
        logger.success("Database initialization complete!")
        logger.info("=" * 60)
        logger.info("Next steps:")
        logger.info("  1. Review and update .env file with your settings")
        logger.info("  2. Start the server: python -m podcastmanager.main serve")
        logger.info("  3. Access the app at http://localhost:8000")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
