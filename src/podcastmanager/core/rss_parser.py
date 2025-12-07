"""
RSS feed parser for podcasts.

This module handles parsing RSS/Atom feeds to extract podcast metadata
and episode information.
"""

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import feedparser
from loguru import logger

from podcastmanager.utils.validators import extract_file_extension
from podcastmanager.utils.html_sanitizer import sanitize_html


class RSSParser:
    """
    Parser for podcast RSS/Atom feeds.

    Uses feedparser to parse RSS feeds and extract podcast and episode metadata.
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize the RSS parser.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    async def fetch_feed(self, rss_url: str) -> Optional[feedparser.FeedParserDict]:
        """
        Fetch and parse an RSS feed from a URL.

        Args:
            rss_url: URL of the RSS feed

        Returns:
            Parsed feed data or None if fetch failed
        """
        try:
            logger.info(f"Fetching RSS feed: {rss_url}")

            # Let feedparser handle the fetching and parsing
            # It handles encoding, redirects, and compression better than doing it manually
            # Set user agent via feedparser
            feed = feedparser.parse(
                rss_url,
                agent="AppleCoreMedia/1.0.0.19H524 (iPhone; U; CPU OS 15_7 like Mac OS X; en_us)"
            )

            if feed.bozo:
                # Feed has errors but might still be parseable
                logger.warning(f"Feed has parsing errors: {feed.get('bozo_exception', 'Unknown error')}")
                # If completely unparseable, return None
                if not hasattr(feed, 'feed') or not feed.feed:
                    logger.error(f"Feed is completely unparseable")
                    logger.debug(f"Response preview: {response.text[:1000]}")
                    return None

            if not feed.entries:
                logger.warning(f"Feed has no entries: {rss_url}")
                # Still return the feed object so we can get metadata
                if hasattr(feed, 'feed') and feed.feed:
                    logger.info(f"Feed has metadata but no episodes")
                else:
                    logger.error(f"Feed parsing failed completely")
                    return None

            logger.success(f"Successfully fetched feed with {len(feed.entries)} entries")
            return feed

        except Exception as e:
            logger.error(f"Error fetching/parsing feed {rss_url}: {e}")
            return None

    def parse_podcast_metadata(self, feed: feedparser.FeedParserDict, rss_url: str) -> Dict:
        """
        Extract podcast metadata from a feed.

        Args:
            feed: Parsed feed data
            rss_url: Original RSS URL

        Returns:
            Dictionary with podcast metadata
        """
        feed_info = feed.get('feed', {})

        # Extract basic metadata
        title = feed_info.get('title', 'Unknown Podcast').strip()
        description = feed_info.get('description') or feed_info.get('subtitle', '')
        # Sanitize HTML in description to prevent XSS
        description = sanitize_html(description) if description else ''
        author = feed_info.get('author') or feed_info.get('itunes_author', '')

        # Get image URL
        image_url = None
        if hasattr(feed_info, 'image'):
            image_url = feed_info.image.get('href') or feed_info.image.get('url')
        if not image_url and hasattr(feed_info, 'itunes_image'):
            image_url = feed_info.itunes_image.get('href')

        # Get website URL
        website_url = feed_info.get('link', '')

        # Get category
        categories = feed_info.get('tags', [])
        category = categories[0].get('term') if categories else None
        if not category and hasattr(feed_info, 'itunes_category'):
            category = feed_info.itunes_category

        # Get language
        language = feed_info.get('language', 'en')

        metadata = {
            'title': title,
            'description': description[:5000] if description else None,  # Limit length
            'author': author[:200] if author else None,
            'rss_url': rss_url,
            'image_url': image_url[:1000] if image_url else None,
            'website_url': website_url[:1000] if website_url else None,
            'category': category[:100] if category else None,
            'language': language[:10] if language else 'en',
        }

        logger.debug(f"Parsed podcast metadata: {metadata['title']}")
        return metadata

    def parse_episodes(self, feed: feedparser.FeedParserDict, limit: Optional[int] = None) -> List[Dict]:
        """
        Extract episode information from a feed.

        Args:
            feed: Parsed feed data
            limit: Maximum number of episodes to return (None for all)

        Returns:
            List of episode dictionaries
        """
        episodes = []
        entries = feed.entries[:limit] if limit else feed.entries

        for entry in entries:
            try:
                episode = self._parse_single_episode(entry)
                if episode:
                    episodes.append(episode)
            except Exception as e:
                logger.warning(f"Error parsing episode: {e}")
                continue

        logger.info(f"Parsed {len(episodes)} episodes from feed")
        return episodes

    def _parse_single_episode(self, entry: feedparser.FeedParserDict) -> Optional[Dict]:
        """
        Parse a single episode entry from the feed.

        Args:
            entry: Feed entry for a single episode

        Returns:
            Episode dictionary or None if parsing failed
        """
        # Extract title
        title = entry.get('title', 'Untitled Episode').strip()

        # Extract GUID (unique identifier)
        guid = entry.get('id') or entry.get('guid') or entry.get('link')
        if not guid:
            logger.warning(f"Episode '{title}' has no GUID, skipping")
            return None

        # Extract description and sanitize HTML to prevent XSS
        description = entry.get('description') or entry.get('summary', '')
        description = sanitize_html(description) if description else ''

        # Parse publication date
        pub_date = None
        if 'published_parsed' in entry and entry.published_parsed:
            try:
                pub_date = datetime(*entry.published_parsed[:6])
            except Exception:
                pass

        if not pub_date and 'published' in entry:
            try:
                pub_date = parsedate_to_datetime(entry.published)
            except Exception:
                pass

        # Extract audio enclosure
        audio_url = None
        file_size = None
        file_type = None

        for enclosure in entry.get('enclosures', []):
            enc_type = enclosure.get('type', '')
            if enc_type.startswith('audio/') or enc_type.startswith('video/'):
                audio_url = enclosure.get('href') or enclosure.get('url')
                file_size = enclosure.get('length')
                file_type = enc_type
                break

        # If no enclosure found, try links
        if not audio_url:
            for link in entry.get('links', []):
                if link.get('type', '').startswith('audio/'):
                    audio_url = link.get('href')
                    file_type = link.get('type')
                    break

        if not audio_url:
            logger.warning(f"Episode '{title}' has no audio URL, skipping")
            return None

        # Parse duration (iTunes extension)
        duration = None
        if hasattr(entry, 'itunes_duration'):
            duration = self._parse_duration(entry.itunes_duration)

        # Parse episode/season numbers (iTunes extension)
        episode_number = None
        season_number = None
        if hasattr(entry, 'itunes_episode'):
            try:
                episode_number = int(entry.itunes_episode)
            except (ValueError, TypeError):
                pass

        if hasattr(entry, 'itunes_season'):
            try:
                season_number = int(entry.itunes_season)
            except (ValueError, TypeError):
                pass

        # Convert file_size to integer
        if file_size:
            try:
                file_size = int(file_size)
            except (ValueError, TypeError):
                file_size = None

        episode = {
            'title': title[:500],  # Limit length
            'description': description[:10000] if description else None,
            'guid': guid[:500],
            'pub_date': pub_date,
            'duration': duration,
            'audio_url': audio_url[:1000],
            'file_size': file_size,
            'file_type': file_type[:50] if file_type else None,
            'episode_number': episode_number,
            'season_number': season_number,
        }

        return episode

    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """
        Parse iTunes duration string to seconds.

        Formats supported:
        - Seconds: "1234"
        - MM:SS: "12:34"
        - HH:MM:SS: "1:23:45"

        Args:
            duration_str: Duration string

        Returns:
            Duration in seconds or None if parsing failed
        """
        if not duration_str:
            return None

        try:
            # If it's just a number, it's already in seconds
            if duration_str.isdigit():
                return int(duration_str)

            # Parse HH:MM:SS or MM:SS format
            parts = duration_str.split(':')
            if len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = parts
                return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = parts
                return int(minutes) * 60 + int(seconds)
            else:
                return None
        except (ValueError, AttributeError):
            return None


# Global parser instance
_rss_parser: Optional[RSSParser] = None


def get_rss_parser(timeout: int = 30) -> RSSParser:
    """
    Get a global RSS parser instance.

    Args:
        timeout: Request timeout in seconds

    Returns:
        RSSParser instance
    """
    global _rss_parser
    if _rss_parser is None:
        _rss_parser = RSSParser(timeout=timeout)
    return _rss_parser
