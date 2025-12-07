"""
Database configuration and session management.

This module handles the SQLAlchemy database engine, session factory,
and provides dependency injection for FastAPI routes.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from podcastmanager.db.models import Base


class DatabaseManager:
    """
    Manages database connections and sessions.

    This class provides a centralized way to handle database operations
    throughout the application.
    """

    def __init__(self, database_url: str, echo: bool = False):
        """
        Initialize the database manager.

        Args:
            database_url: SQLAlchemy database URL (e.g., sqlite+aiosqlite:///./podcast_manager.db)
            echo: Whether to log SQL queries (useful for debugging)
        """
        self.database_url = database_url
        self.echo = echo

        # Create async engine
        # For SQLite, we use NullPool to avoid connection pool issues
        self.engine = create_async_engine(
            database_url,
            echo=echo,
            poolclass=NullPool if "sqlite" in database_url else None,
        )

        # Create session factory
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    async def create_tables(self):
        """
        Create all database tables.

        This should only be used for initial setup or testing.
        For production, use Alembic migrations instead.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """
        Drop all database tables.

        WARNING: This will delete all data! Only use for testing.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session.

        This is a dependency for FastAPI routes.

        Yields:
            AsyncSession: Database session
        """
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self):
        """Close the database engine and clean up connections."""
        await self.engine.dispose()


# Global database manager instance (will be initialized in main.py)
db_manager: DatabaseManager = None  # type: ignore


def get_db_manager() -> DatabaseManager:
    """
    Get the global database manager instance.

    Returns:
        DatabaseManager: The database manager instance

    Raises:
        RuntimeError: If database manager hasn't been initialized
    """
    if db_manager is None:
        raise RuntimeError("Database manager not initialized. Call init_db() first.")
    return db_manager


def init_db(database_url: str, echo: bool = False) -> DatabaseManager:
    """
    Initialize the global database manager.

    Args:
        database_url: SQLAlchemy database URL
        echo: Whether to log SQL queries

    Returns:
        DatabaseManager: The initialized database manager
    """
    global db_manager
    db_manager = DatabaseManager(database_url, echo)
    return db_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting a database session.

    Yields:
        AsyncSession: Database session
    """
    async for session in get_db_manager().get_session():
        yield session
