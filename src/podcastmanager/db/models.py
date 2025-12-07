"""
Database models for the Podcast Manager application.

This module defines the SQLAlchemy ORM models for podcasts, episodes,
downloads, and application settings.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Podcast(Base):
    """
    Represents a podcast subscription.

    A podcast contains multiple episodes and tracks metadata like the RSS feed URL,
    download settings, and last check time.
    """

    __tablename__ = "podcasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # RSS Feed information
    rss_url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False, index=True)

    # Media assets
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Apple Podcast integration
    apple_podcast_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    # Categorization
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Download settings
    max_episodes_to_keep: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    auto_download: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    download_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    episodes: Mapped[List["Episode"]] = relationship(
        "Episode", back_populates="podcast", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Podcast(id={self.id}, title='{self.title}')>"


class Episode(Base):
    """
    Represents a single podcast episode.

    Episodes belong to a podcast and can have associated download records.
    """

    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    podcast_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("podcasts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Episode metadata
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    guid: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)

    # Publication info
    pub_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in seconds

    # Media file info
    audio_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in bytes
    file_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Episode numbering (optional, not all podcasts provide this)
    episode_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    season_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    podcast: Mapped["Podcast"] = relationship("Podcast", back_populates="episodes")
    download: Mapped[Optional["Download"]] = relationship(
        "Download", back_populates="episode", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Episode(id={self.id}, title='{self.title}', podcast_id={self.podcast_id})>"


# Composite index for efficient episode queries
Index("idx_episodes_podcast_pub_date", Episode.podcast_id, Episode.pub_date.desc())


class Download(Base):
    """
    Tracks the download status of a podcast episode.

    This model maintains the state of episode downloads including progress,
    file paths, and error information for failed downloads.
    """

    __tablename__ = "downloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    episode_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Download status: pending, downloading, completed, failed, deleted
    status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("status IN ('pending', 'downloading', 'completed', 'failed', 'deleted')"),
        nullable=False,
        index=True,
    )

    # File information
    file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # actual downloaded size

    # Progress tracking (0.0 to 1.0)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    episode: Mapped["Episode"] = relationship("Episode", back_populates="download")

    def __repr__(self) -> str:
        return f"<Download(id={self.id}, episode_id={self.episode_id}, status='{self.status}')>"


class Setting(Base):
    """
    Application-wide settings stored in the database.

    This model allows for dynamic configuration without requiring application restarts.
    """

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Setting(key='{self.key}', value='{self.value}')>"
