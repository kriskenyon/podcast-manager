"""
Application configuration management.

This module uses Pydantic Settings to load and validate configuration
from environment variables and .env files.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Settings can be loaded from:
    1. Environment variables
    2. .env file in the project root
    3. Default values defined here
    """

    # Application metadata
    app_name: str = "Podcast Manager"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, description="Enable debug mode")

    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # Database configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./podcast_manager.db",
        description="SQLAlchemy database URL",
    )

    # Download settings
    download_base_path: Path = Field(
        default=Path("./downloads"),
        description="Base directory for podcast downloads",
    )
    max_concurrent_downloads: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of concurrent downloads",
    )
    default_max_episodes: int = Field(
        default=3,
        ge=1,
        description="Default number of episodes to keep per podcast",
    )
    download_timeout: int = Field(
        default=3600,
        description="Download timeout in seconds (1 hour)",
    )

    # Feed refresh settings
    feed_refresh_interval: int = Field(
        default=3600,
        ge=300,
        description="Feed refresh interval in seconds (default: 1 hour, min: 5 minutes)",
    )
    feed_request_timeout: int = Field(
        default=30,
        description="Timeout for feed requests in seconds",
    )

    # Apple Podcast API settings
    apple_podcast_api_base: str = Field(
        default="https://itunes.apple.com/search",
        description="Apple Podcast Search API base URL",
    )
    apple_podcast_search_limit: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Maximum number of search results from Apple Podcasts",
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_file: Optional[Path] = Field(
        default=None,
        description="Log file path (None for console only)",
    )

    # Background tasks
    auto_cleanup_enabled: bool = Field(
        default=True,
        description="Automatically cleanup old episodes based on podcast settings",
    )
    cleanup_interval: int = Field(
        default=86400,
        ge=3600,
        description="Cleanup job interval in seconds (default: 24 hours)",
    )

    # Security settings (for future use)
    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for session management",
    )

    # Plex Integration (optional)
    plex_enabled: bool = Field(
        default=False,
        description="Enable Plex Media Server integration for smart cleanup",
    )
    plex_url: str = Field(
        default="http://localhost:32400",
        description="Plex server URL",
    )
    plex_token: str = Field(
        default="",
        description="Plex authentication token",
    )
    plex_library: str = Field(
        default="Podcasts",
        description="Name of the Plex library containing podcasts",
    )

    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("download_base_path", mode="before")
    @classmethod
    def validate_download_path(cls, v):
        """Ensure download path is a Path object."""
        if isinstance(v, str):
            return Path(v)
        return v

    @field_validator("log_file", mode="before")
    @classmethod
    def validate_log_file(cls, v):
        """Ensure log file is a Path object if provided."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return Path(v)
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v = v.upper()
        if v not in allowed_levels:
            raise ValueError(f"Log level must be one of: {', '.join(allowed_levels)}")
        return v

    def create_directories(self) -> None:
        """
        Create necessary directories if they don't exist.

        This includes:
        - Download base path
        - Log file directory (if log_file is set)
        """
        # Create download directory
        self.download_base_path.mkdir(parents=True, exist_ok=True)

        # Create log directory if log file is specified
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.

    This function creates a singleton Settings instance that is reused
    throughout the application.

    Returns:
        Settings: The application settings
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        # Ensure necessary directories exist
        _settings.create_directories()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment and .env file.

    This is useful for testing or when settings need to be refreshed.

    Returns:
        Settings: The reloaded settings
    """
    global _settings
    _settings = None
    return get_settings()
