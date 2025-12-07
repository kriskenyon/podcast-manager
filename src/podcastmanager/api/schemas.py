"""
Pydantic schemas for API request and response models.

These schemas define the structure of data sent to and received from the API,
providing automatic validation and documentation.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


# ============================================================================
# Podcast Schemas
# ============================================================================


class PodcastBase(BaseModel):
    """Base schema for podcast data."""

    title: str = Field(..., description="Podcast title")
    description: Optional[str] = Field(None, description="Podcast description")
    author: Optional[str] = Field(None, description="Podcast author/creator")


class PodcastCreate(BaseModel):
    """Schema for creating a new podcast."""

    rss_url: str = Field(..., description="RSS feed URL")
    max_episodes_to_keep: int = Field(
        default=3,
        ge=1,
        le=100,
        description="Maximum number of episodes to keep",
    )
    auto_download: bool = Field(
        default=True,
        description="Automatically download new episodes",
    )


class PodcastUpdate(BaseModel):
    """Schema for updating podcast settings."""

    max_episodes_to_keep: Optional[int] = Field(
        None,
        ge=1,
        le=100,
        description="Maximum number of episodes to keep",
    )
    auto_download: Optional[bool] = Field(
        None,
        description="Automatically download new episodes",
    )


class PodcastResponse(PodcastBase):
    """Schema for podcast response data."""

    id: int = Field(..., description="Podcast ID")
    rss_url: str = Field(..., description="RSS feed URL")
    image_url: Optional[str] = Field(None, description="Podcast artwork URL")
    website_url: Optional[str] = Field(None, description="Podcast website URL")
    category: Optional[str] = Field(None, description="Podcast category")
    language: Optional[str] = Field(None, description="Podcast language code")
    max_episodes_to_keep: int = Field(..., description="Maximum episodes to keep")
    auto_download: bool = Field(..., description="Auto-download enabled")
    download_path: Optional[str] = Field(None, description="Download folder path")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_checked: Optional[datetime] = Field(None, description="Last feed check timestamp")

    class Config:
        from_attributes = True


class PodcastListResponse(BaseModel):
    """Schema for paginated podcast list."""

    podcasts: List[PodcastResponse] = Field(..., description="List of podcasts")
    total: int = Field(..., description="Total number of podcasts")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items returned")


# ============================================================================
# Episode Schemas
# ============================================================================


class EpisodeBase(BaseModel):
    """Base schema for episode data."""

    title: str = Field(..., description="Episode title")
    description: Optional[str] = Field(None, description="Episode description")


class EpisodeResponse(EpisodeBase):
    """Schema for episode response data."""

    id: int = Field(..., description="Episode ID")
    podcast_id: int = Field(..., description="Parent podcast ID")
    guid: str = Field(..., description="Episode unique identifier")
    pub_date: Optional[datetime] = Field(None, description="Publication date")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    audio_url: str = Field(..., description="Audio file URL")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_type: Optional[str] = Field(None, description="MIME type")
    episode_number: Optional[int] = Field(None, description="Episode number")
    season_number: Optional[int] = Field(None, description="Season number")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class EpisodeListResponse(BaseModel):
    """Schema for paginated episode list."""

    episodes: List[EpisodeResponse] = Field(..., description="List of episodes")
    total: int = Field(..., description="Total number of episodes")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items returned")


class PodcastWithEpisodesResponse(PodcastResponse):
    """Schema for podcast with episodes included."""

    episodes: List[EpisodeResponse] = Field(..., description="List of episodes")


# ============================================================================
# Download Schemas
# ============================================================================


class DownloadResponse(BaseModel):
    """Schema for download status response."""

    id: int = Field(..., description="Download ID")
    episode_id: int = Field(..., description="Episode ID")
    status: str = Field(..., description="Download status")
    file_path: Optional[str] = Field(None, description="Downloaded file path")
    file_size: Optional[int] = Field(None, description="Downloaded file size in bytes")
    progress: float = Field(..., description="Download progress (0.0 to 1.0)")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(..., description="Number of retry attempts")
    started_at: Optional[datetime] = Field(None, description="Download start time")
    completed_at: Optional[datetime] = Field(None, description="Download completion time")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class DownloadListResponse(BaseModel):
    """Schema for paginated download list."""

    downloads: List[DownloadResponse] = Field(..., description="List of downloads")
    total: int = Field(..., description="Total number of downloads")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items returned")


# ============================================================================
# Generic Response Schemas
# ============================================================================


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Operation success status")


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


# ============================================================================
# Health Check Schema
# ============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    app: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")


# ============================================================================
# OPML Schemas
# ============================================================================


class OPMLPodcastInfo(BaseModel):
    """Schema for podcast information extracted from OPML."""

    title: str = Field(..., description="Podcast title")
    rss_url: str = Field(..., description="RSS feed URL")
    description: str = Field(default="", description="Podcast description")
    website_url: str = Field(default="", description="Podcast website URL")


class OPMLImportResponse(BaseModel):
    """Schema for OPML import response."""

    podcasts_found: int = Field(..., description="Number of podcasts found in OPML")
    podcasts: List[OPMLPodcastInfo] = Field(..., description="List of podcasts from OPML")
    message: str = Field(..., description="Status message")
