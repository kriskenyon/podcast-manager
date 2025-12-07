# HTML Sanitization for Podcast Show Notes

## Security Implementation

This application safely handles HTML content in podcast descriptions and show notes to prevent XSS (Cross-Site Scripting) attacks while preserving basic formatting.

## How It Works

### Backend Sanitization (Primary Defense)

HTML content from RSS feeds is sanitized **on the backend** using the [Bleach](https://bleach.readthedocs.io/) library before being stored in the database.

**Location:** `src/podcastmanager/utils/html_sanitizer.py`

**When:** During RSS feed parsing in `src/podcastmanager/core/rss_parser.py`

**What's Allowed:**
- Safe formatting tags: `<p>`, `<br>`, `<strong>`, `<b>`, `<em>`, `<i>`, `<u>`
- Headings: `<h1>` through `<h6>`
- Links: `<a>` with `href` and `title` attributes
- Lists: `<ul>`, `<ol>`, `<li>`
- Quotes: `<blockquote>`

**What's Blocked:**
- All JavaScript: `<script>`, `onclick`, `onerror`, etc.
- Dangerous tags: `<iframe>`, `<object>`, `<embed>`, `<form>`
- Executable content: `javascript:` URLs, `data:` URLs (except https/http)
- Style injection: inline `<style>` tags, CSS with expressions

### Frontend Display

The frontend uses Vue's `v-html` directive to render the **already sanitized** HTML.

**Files:**
- `frontend/src/components/EpisodeItem.vue`
- `frontend/src/views/PodcastDetailView.vue`

**CSS Styling:**
Scoped styles are applied to format links, bold, italic, and lists appropriately.

## Security Layers

1. **Backend Sanitization** (Primary)
   - Strips dangerous HTML before database storage
   - Uses well-tested Bleach library
   - Validates all URLs in links

2. **Limited Allowed Tags**
   - Whitelist approach - only safe tags allowed
   - All other tags are stripped

3. **Attribute Filtering**
   - Only specific attributes allowed per tag
   - Event handlers (`onclick`, etc.) never allowed

4. **URL Protocol Validation**
   - Only `http`, `https`, and `mailto` links permitted
   - Blocks `javascript:`, `data:`, and other dangerous protocols

## Testing

To verify sanitization works correctly:

```python
from podcastmanager.utils.html_sanitizer import sanitize_html

# Safe HTML - preserved
safe = '<p>This is <strong>bold</strong> and <a href="https://example.com">a link</a></p>'
print(sanitize_html(safe))
# Output: Same as input

# Dangerous HTML - stripped
dangerous = '<script>alert("XSS")</script><p onclick="evil()">Text</p>'
print(sanitize_html(dangerous))
# Output: '<p>Text</p>'

# JavaScript URL - blocked
bad_link = '<a href="javascript:alert(1)">Click</a>'
print(sanitize_html(bad_link))
# Output: '<a>Click</a>'  # href removed
```

## Why This Approach?

**Backend sanitization is superior to client-side sanitization:**

1. **Performance** - Sanitization happens once when parsing the feed, not on every page render
2. **Security** - Can't be bypassed by disabling JavaScript
3. **Consistency** - All clients see the same safe content
4. **Database cleanliness** - Only clean data stored
5. **API safety** - Any API consumers get pre-sanitized data

## Alternative Approaches Considered

### Client-Side Only (DOMPurify)
❌ **Not used** - Requires JavaScript, sanitizes on every render, more CPU usage

### Strip All HTML
❌ **Not used** - Loses all formatting, poor user experience

### Markdown Conversion
❌ **Not used** - Complex, imperfect conversion, not all RSS feeds use standard HTML

## Dependencies

- **bleach** (6.2.0) - HTML sanitization library
  - Well-maintained, used by Mozilla
  - Based on html5lib parser
  - Battle-tested in production environments

## Future Enhancements

Potential improvements:

1. **Content Security Policy (CSP)** - Add CSP headers to further restrict what can execute
2. **Image sanitization** - Add `<img>` support with URL validation
3. **HTML entity decoding** - Better handling of encoded entities
4. **Truncation for previews** - Smart truncation preserving HTML structure

## References

- [Bleach Documentation](https://bleach.readthedocs.io/)
- [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [Vue.js v-html Security](https://vuejs.org/guide/best-practices/security.html#potential-dangers)
