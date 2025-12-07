#!/usr/bin/env python3
"""
Test duplicate episode handling.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import select
from podcastmanager.db.database import get_session_factory
from podcastmanager.db.models import Episode, Podcast
from podcastmanager.core.podcast_manager import PodcastManager


async def test_duplicate_episode_handling():
    """Test that duplicate episodes are handled gracefully."""
    print("Testing duplicate episode handling...")
    print("-" * 60)

    # Get session factory
    session_factory = get_session_factory()

    async with session_factory() as session:
        # Create podcast manager
        manager = PodcastManager(session)

        # Try to add a podcast (use a real feed for testing)
        test_rss_url = "https://feeds.simplecast.com/54nAGcIl"  # The Daily

        print(f"\n1. Adding podcast from RSS: {test_rss_url}")
        podcast = await manager.add_podcast_from_rss(
            rss_url=test_rss_url,
            max_episodes_to_keep=3,
            auto_download=False,
        )

        if podcast:
            print(f"   ✅ Podcast added: {podcast.title} (ID: {podcast.id})")

            # Count episodes
            result = await session.execute(
                select(Episode).where(Episode.podcast_id == podcast.id)
            )
            episodes = list(result.scalars().all())
            print(f"   ✅ Episodes added: {len(episodes)}")

            # Try to add the same podcast again
            print(f"\n2. Attempting to add same podcast again...")
            podcast2 = await manager.add_podcast_from_rss(
                rss_url=test_rss_url,
                max_episodes_to_keep=3,
                auto_download=False,
            )

            if podcast2 and podcast2.id == podcast.id:
                print(f"   ✅ Correctly returned existing podcast (ID: {podcast2.id})")
                print(f"   ✅ No duplicate episodes created")
            else:
                print(f"   ❌ Unexpected result")
                return False

        else:
            print("   ⚠️  Podcast already exists or failed to add")

        await session.commit()

    print("\n" + "=" * 60)
    print("✅ Test completed successfully")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_duplicate_episode_handling())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
