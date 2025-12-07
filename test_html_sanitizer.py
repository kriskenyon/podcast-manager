#!/usr/bin/env python3
"""
Test script for HTML sanitization.

Demonstrates how the sanitizer handles various HTML inputs.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from podcastmanager.utils.html_sanitizer import sanitize_html, strip_html


def test_sanitization():
    """Test various HTML sanitization scenarios."""
    print("=" * 70)
    print("HTML Sanitization Tests")
    print("=" * 70)

    test_cases = [
        {
            "name": "Safe HTML (Preserved)",
            "input": '<p>This is <strong>bold</strong> and <em>italic</em> text.</p>',
        },
        {
            "name": "Links (Allowed)",
            "input": '<p>Check out <a href="https://example.com">this link</a>!</p>',
        },
        {
            "name": "Lists (Allowed)",
            "input": '<ul><li>Item 1</li><li>Item 2</li></ul>',
        },
        {
            "name": "XSS Script Tag (Blocked)",
            "input": '<script>alert("XSS")</script><p>Safe content</p>',
        },
        {
            "name": "JavaScript Event Handler (Blocked)",
            "input": '<p onclick="alert(1)">Click me</p>',
        },
        {
            "name": "JavaScript URL (Blocked)",
            "input": '<a href="javascript:alert(1)">Click</a>',
        },
        {
            "name": "Iframe Embed (Blocked)",
            "input": '<iframe src="https://evil.com"></iframe><p>Text</p>',
        },
        {
            "name": "Style Injection (Blocked)",
            "input": '<p style="position:fixed;top:0">Text</p>',
        },
        {
            "name": "Mixed Safe and Unsafe",
            "input": '<p>Safe <strong>text</strong></p><script>evil()</script><p>More safe</p>',
        },
        {
            "name": "Real Podcast Description",
            "input": '''<p>In this episode we discuss:</p>
<ul>
<li><a href="https://example.com/topic1">Topic 1</a></li>
<li><strong>Topic 2</strong> with some details</li>
<li><em>Topic 3</em> and more</li>
</ul>
<p>Subscribe at <a href="https://podcast.example.com">our website</a>!</p>''',
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 70)
        print("INPUT:")
        print(f"  {test['input']}")
        print("\nOUTPUT:")
        sanitized = sanitize_html(test['input'])
        print(f"  {sanitized}")
        print("\nPLAIN TEXT:")
        plain = strip_html(sanitized)
        print(f"  {plain}")

    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)


def test_edge_cases():
    """Test edge cases."""
    print("\n\n" + "=" * 70)
    print("Edge Cases")
    print("=" * 70)

    edge_cases = [
        ("None value", None),
        ("Empty string", ""),
        ("Plain text (no HTML)", "Just plain text"),
        ("Malformed HTML", "<p>Unclosed paragraph"),
        ("Nested tags", "<p><strong><em>Nested</em></strong></p>"),
        ("HTML entities", "AT&amp;T &lt;Company&gt;"),
    ]

    for name, input_val in edge_cases:
        print(f"\n{name}:")
        print(f"  Input:  {repr(input_val)}")
        print(f"  Output: {repr(sanitize_html(input_val))}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_sanitization()
    test_edge_cases()
