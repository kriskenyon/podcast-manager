"""
HTML sanitization utilities for podcast descriptions and show notes.

This module provides safe HTML sanitization to prevent XSS attacks while
preserving basic formatting from podcast RSS feeds.
"""

import bleach
from typing import Optional


# Allowed HTML tags for podcast descriptions
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'a', 'ul', 'ol', 'li',
    'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
]

# Allowed attributes for specific tags
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'title'],
}

# URL protocols that are allowed in links
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(html: Optional[str]) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.

    This function:
    - Removes all dangerous HTML tags and attributes
    - Allows safe formatting tags (p, strong, em, a, ul, ol, etc.)
    - Strips JavaScript and other executable content
    - Validates URLs in links

    Args:
        html: Raw HTML content from RSS feed

    Returns:
        Sanitized HTML safe for display
    """
    if not html:
        return ""

    # Clean the HTML
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,  # Strip disallowed tags instead of escaping
    )

    # Linkify URLs that aren't already in <a> tags
    cleaned = bleach.linkify(
        cleaned,
        parse_email=True,
    )

    return cleaned


def strip_html(html: Optional[str]) -> str:
    """
    Strip all HTML tags and return plain text.

    Use this for previews or when HTML formatting is not needed.

    Args:
        html: HTML content

    Returns:
        Plain text with all HTML removed
    """
    if not html:
        return ""

    # Clean with no allowed tags = strips everything
    return bleach.clean(html, tags=[], strip=True)


def truncate_html(html: Optional[str], max_length: int = 200) -> str:
    """
    Truncate HTML content to a maximum length while preserving tag structure.

    Args:
        html: HTML content
        max_length: Maximum length of plain text (excluding tags)

    Returns:
        Truncated HTML
    """
    if not html:
        return ""

    # First sanitize
    clean = sanitize_html(html)

    # Get plain text length
    plain = strip_html(clean)

    if len(plain) <= max_length:
        return clean

    # Truncate and add ellipsis
    truncated_plain = plain[:max_length].rsplit(' ', 1)[0] + '...'

    return truncated_plain
