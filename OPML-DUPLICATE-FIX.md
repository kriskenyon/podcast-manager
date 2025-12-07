# OPML Import Duplicate Episode Fix

## Problem

When importing OPML files, the application would fail with:
```
(sqlite3.IntegrityError) UNIQUE constraint failed: episodes.guid
```

This occurred when:
1. Attempting to re-import the same podcast from OPML
2. Episodes with duplicate GUIDs existed in the database (from previous imports or manual additions)
3. The GUID constraint is global across all episodes, not scoped per podcast

## Root Cause

The `episodes.guid` column has a global UNIQUE constraint. When adding episodes:
- The code checked for existing episodes within the current podcast only
- But if the same GUID existed from another podcast or a previous failed import, the INSERT would fail
- The IntegrityError would cause the entire transaction to fail

## Solution

### 1. Nested Transactions for Episode Insertion

Modified `src/podcastmanager/core/podcast_manager.py` in the `_discover_episodes` method:

```python
# Use savepoints (nested transactions) for each episode
async with self.session.begin_nested():
    episode = Episode(...)
    self.session.add(episode)
    await self.session.flush()
```

**Benefits:**
- If an episode insertion fails, only that specific episode's transaction is rolled back
- Other episodes can still be added successfully
- The podcast remains committed to the database

### 2. Graceful Error Handling

Added try/except around each episode insertion:

```python
try:
    async with self.session.begin_nested():
        # Add episode
except Exception as e:
    if "UNIQUE constraint failed" in str(e) or "IntegrityError" in str(type(e).__name__):
        logger.warning(f"Skipping duplicate episode (GUID: {guid}): {title}")
        continue
    else:
        raise
```

**Benefits:**
- Duplicate episodes are logged as warnings but don't stop the import
- Other errors are still raised for proper debugging
- Import process continues with remaining episodes

### 3. Improved OPML Import Reporting

Updated `src/podcastmanager/api/routes.py` to properly count skipped vs. added podcasts:

```python
# Check if podcast already exists BEFORE attempting to add
existing = await podcast_manager.get_podcast_by_rss_url(rss_url)
if existing:
    skipped += 1
    continue

# Only add new podcasts
podcast = await podcast_manager.add_podcast_from_rss(...)
if podcast:
    added += 1
```

**Benefits:**
- Existing podcasts are correctly counted as "skipped"
- Clearer reporting: "X added, Y skipped, Z errors"
- No wasted processing for podcasts that already exist

## Testing

To test the fix:

1. Import an OPML file with podcasts
2. Import the same OPML file again
3. Expected result:
   - First import: "X added, 0 skipped, 0 errors"
   - Second import: "0 added, X skipped, 0 errors"
   - No IntegrityError exceptions
   - Duplicate episode warnings in logs (if episodes share GUIDs across podcasts)

## Future Improvements

Consider changing the database schema to make GUID unique per podcast instead of globally:

```python
# In models.py
__table_args__ = (
    UniqueConstraint('podcast_id', 'guid', name='uix_podcast_episode_guid'),
)
```

This would require a database migration but would better reflect podcast episode uniqueness semantics.

## Files Modified

1. `src/podcastmanager/core/podcast_manager.py` - Episode insertion with nested transactions
2. `src/podcastmanager/api/routes.py` - OPML import logic improvements
