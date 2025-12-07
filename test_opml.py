#!/usr/bin/env python3
"""
Test script for OPML import/export functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from podcastmanager.services.opml import OPMLService


def test_opml_parsing():
    """Test parsing the sample OPML file."""
    print("Testing OPML Parsing...")
    print("-" * 60)

    # Read test OPML file
    opml_path = Path(__file__).parent / "test_podcasts.opml"

    if not opml_path.exists():
        print(f"❌ Test file not found: {opml_path}")
        return False

    with open(opml_path, 'rb') as f:
        opml_content = f.read()

    # Validate OPML
    print("\n1. Validating OPML...")
    is_valid = OPMLService.validate_opml(opml_content)

    if is_valid:
        print("   ✅ OPML file is valid")
    else:
        print("   ❌ OPML file is invalid")
        return False

    # Count podcasts
    print("\n2. Counting podcasts...")
    count = OPMLService.count_podcasts_in_opml(opml_content)
    print(f"   ✅ Found {count} podcasts")

    # Parse OPML
    print("\n3. Parsing OPML...")
    podcasts = OPMLService.parse_opml(opml_content)

    print(f"   ✅ Parsed {len(podcasts)} podcasts:")
    for i, podcast in enumerate(podcasts, 1):
        print(f"\n   Podcast {i}:")
        print(f"      Title: {podcast['title']}")
        print(f"      RSS URL: {podcast['rss_url']}")
        print(f"      Website: {podcast['website_url']}")
        print(f"      Description: {podcast['description'][:60]}..." if len(podcast['description']) > 60 else f"      Description: {podcast['description']}")

    return True


def test_opml_generation():
    """Test generating OPML from mock data."""
    print("\n" + "=" * 60)
    print("Testing OPML Generation...")
    print("-" * 60)

    # Create mock podcast objects
    from podcastmanager.db.models import Podcast

    mock_podcasts = [
        Podcast(
            id=1,
            title="Test Podcast 1",
            description="A test podcast",
            rss_url="https://example.com/feed1.rss",
            website_url="https://example.com/podcast1",
        ),
        Podcast(
            id=2,
            title="Test Podcast 2",
            description="Another test podcast",
            rss_url="https://example.com/feed2.rss",
            website_url="https://example.com/podcast2",
        ),
    ]

    print("\n1. Generating OPML from mock podcasts...")
    opml_content = OPMLService.generate_opml(
        podcasts=mock_podcasts,
        title="Test Subscriptions"
    )

    print("   ✅ Generated OPML:")
    print("\n" + "-" * 60)
    print(opml_content)
    print("-" * 60)

    # Validate generated OPML
    print("\n2. Validating generated OPML...")
    is_valid = OPMLService.validate_opml(opml_content.encode('utf-8'))

    if is_valid:
        print("   ✅ Generated OPML is valid")
    else:
        print("   ❌ Generated OPML is invalid")
        return False

    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("OPML Service Test Suite")
    print("=" * 60)

    # Run tests
    parsing_ok = test_opml_parsing()
    generation_ok = test_opml_generation()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("-" * 60)
    print(f"OPML Parsing:    {'✅ PASSED' if parsing_ok else '❌ FAILED'}")
    print(f"OPML Generation: {'✅ PASSED' if generation_ok else '❌ FAILED'}")
    print("=" * 60)

    # Exit code
    sys.exit(0 if (parsing_ok and generation_ok) else 1)
