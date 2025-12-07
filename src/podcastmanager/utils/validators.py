"""
Input validation utilities.

This module provides helper functions for validating user input,
URLs, file paths, and other data.
"""

import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from slugify import slugify


def is_valid_url(url: str) -> bool:
    """
    Check if a string is a valid URL.

    Args:
        url: URL string to validate

    Returns:
        bool: True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_rss_url(url: str) -> bool:
    """
    Check if a URL looks like a valid RSS feed URL.

    This is a basic check - actual validation happens when parsing the feed.

    Args:
        url: RSS feed URL to validate

    Returns:
        bool: True if it looks like a valid RSS URL
    """
    if not is_valid_url(url):
        return False

    # Common RSS feed patterns
    rss_patterns = [
        r"\.rss$",
        r"\.xml$",
        r"/feed/?$",
        r"/rss/?$",
        r"/podcast/?$",
        r"/atom/?$",
    ]

    url_lower = url.lower()
    return any(re.search(pattern, url_lower) for pattern in rss_patterns) or "rss" in url_lower


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize a filename to be filesystem-safe.

    Removes or replaces characters that are invalid in filenames across
    different operating systems.

    Args:
        filename: Original filename
        max_length: Maximum length of the sanitized filename

    Returns:
        str: Sanitized filename safe for use on filesystems
    """
    # Use slugify to create a safe filename
    # This will:
    # - Convert to lowercase
    # - Replace spaces with hyphens
    # - Remove invalid characters
    # - Handle unicode properly
    safe_name = slugify(filename, max_length=max_length)

    # If slugify returns empty string, use a default
    if not safe_name:
        safe_name = "unnamed"

    return safe_name


def sanitize_folder_name(folder_name: str) -> str:
    """
    Sanitize a folder name to be filesystem-safe.

    Similar to sanitize_filename but preserves more characters
    and doesn't force lowercase.

    Args:
        folder_name: Original folder name

    Returns:
        str: Sanitized folder name
    """
    # Replace invalid filesystem characters
    invalid_chars = r'[<>:"/\\|?*]'
    safe_name = re.sub(invalid_chars, "-", folder_name)

    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(". ")

    # Collapse multiple hyphens/spaces
    safe_name = re.sub(r"[-\s]+", "-", safe_name)

    # If empty after sanitization, use default
    if not safe_name:
        safe_name = "unnamed"

    return safe_name


def validate_download_path(base_path: Path, relative_path: str) -> Optional[Path]:
    """
    Validate and resolve a download path.

    Ensures the path is within the base download directory (prevents path traversal).

    Args:
        base_path: Base download directory
        relative_path: Relative path to validate

    Returns:
        Path: Resolved absolute path if valid, None otherwise
    """
    try:
        # Resolve the full path
        full_path = (base_path / relative_path).resolve()

        # Check if the resolved path is within base_path
        # This prevents path traversal attacks (e.g., ../../etc/passwd)
        if base_path.resolve() in full_path.parents or full_path == base_path.resolve():
            return full_path

        return None
    except Exception:
        return None


def validate_episode_limit(limit: int) -> int:
    """
    Validate episode download limit.

    Args:
        limit: Number of episodes to keep

    Returns:
        int: Validated limit (clamped to valid range)
    """
    # Clamp between 1 and 100
    return max(1, min(100, limit))


def extract_file_extension(url: str, content_type: Optional[str] = None) -> str:
    """
    Extract file extension from URL or content type.

    Args:
        url: File URL
        content_type: MIME content type (optional)

    Returns:
        str: File extension (e.g., "mp3", "m4a") or "mp3" as default
    """
    # Try to get extension from URL first
    path = urlparse(url).path
    if path:
        ext = Path(path).suffix.lstrip(".")
        if ext:
            return ext.lower()

    # Try to get from content type
    if content_type:
        content_type_map = {
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3",
            "audio/mp4": "m4a",
            "audio/m4a": "m4a",
            "audio/x-m4a": "m4a",
            "audio/aac": "aac",
            "audio/ogg": "ogg",
            "audio/wav": "wav",
            "audio/webm": "webm",
        }
        return content_type_map.get(content_type.lower(), "mp3")

    # Default to mp3
    return "mp3"
