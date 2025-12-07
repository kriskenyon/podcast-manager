# Plex Integration for Smart Episode Cleanup

## Overview

Instead of blindly deleting old episodes, check Plex to see which episodes have been played before deleting them.

## Requirements

1. **Plex Server Connection**
   - Plex server URL (e.g., `http://192.168.1.100:32400`)
   - Plex authentication token
   - Podcast library name (e.g., "Podcasts")

2. **Python Library**
   - `python-plexapi` - Official Plex API library

## Configuration

Add to `.env`:
```bash
# Plex Integration (optional)
PLEX_URL=http://localhost:32400
PLEX_TOKEN=your-plex-token-here
PLEX_LIBRARY=Podcasts
PLEX_ENABLED=true
```

## How to Get Plex Token

1. Log into Plex Web App
2. Play any media
3. Click the three dots → "Get Info"
4. View XML
5. Copy the `X-Plex-Token` from the URL

## Implementation Plan

### 1. Add Plex Service (`src/podcastmanager/services/plex_service.py`)

```python
from plexapi.server import PlexServer
from loguru import logger

class PlexService:
    """Service for interacting with Plex Media Server."""

    def __init__(self, url: str, token: str, library_name: str):
        self.plex = PlexServer(url, token)
        self.library = self.plex.library.section(library_name)

    def is_episode_played(self, file_path: str) -> bool:
        """
        Check if an episode has been played in Plex.

        Args:
            file_path: Path to the episode file

        Returns:
            True if episode has been played
        """
        try:
            # Search for the file in Plex library
            episodes = self.library.search(filepath=file_path)

            if not episodes:
                logger.warning(f"Episode not found in Plex: {file_path}")
                return False

            episode = episodes[0]

            # Check if it's been played
            # viewCount > 0 or isPlayed == True
            is_played = episode.isPlayed or (episode.viewCount > 0)

            logger.debug(f"Episode {file_path}: played={is_played}, viewCount={episode.viewCount}")
            return is_played

        except Exception as e:
            logger.error(f"Error checking Plex status for {file_path}: {e}")
            # If we can't check, assume not played (safer)
            return False
```

### 2. Update Cleanup Job (`src/podcastmanager/tasks/jobs.py`)

```python
async def cleanup_old_episodes_job():
    """
    Cleanup old episodes, respecting Plex play status.

    This job:
    1. For each podcast, finds episodes beyond max_episodes_to_keep
    2. Checks Plex to see which episodes have been played
    3. Deletes only played episodes OR episodes beyond retention limit
    """
    logger.info("=== Starting episode cleanup job ===")

    settings = get_settings()

    # Check if Plex integration is enabled
    plex_enabled = settings.PLEX_ENABLED
    plex_service = None

    if plex_enabled:
        try:
            from podcastmanager.services.plex_service import PlexService
            plex_service = PlexService(
                settings.PLEX_URL,
                settings.PLEX_TOKEN,
                settings.PLEX_LIBRARY
            )
            logger.info("Plex integration enabled - will check play status")
        except Exception as e:
            logger.warning(f"Plex integration failed: {e}. Falling back to standard cleanup")
            plex_service = None

    try:
        db_manager = get_db_manager()
        file_manager = get_file_manager()
        async for session in db_manager.get_session():
            result = await session.execute(select(Podcast))
            podcasts = list(result.scalars().all())

            for podcast in podcasts:
                # Get all completed downloads ordered by pub_date
                result = await session.execute(
                    select(Download, Episode)
                    .join(Episode)
                    .where(Episode.podcast_id == podcast.id)
                    .where(Download.status == "completed")
                    .order_by(Episode.pub_date.desc())
                )
                downloads_with_episodes = list(result.all())

                # Determine which episodes to delete
                to_delete = []

                for i, (download, episode) in enumerate(downloads_with_episodes):
                    # Always keep the N most recent
                    if i < podcast.max_episodes_to_keep:
                        continue

                    # For older episodes, check Plex play status if enabled
                    if plex_service and download.file_path:
                        full_path = str(file_manager.base_path / download.file_path)

                        if plex_service.is_episode_played(full_path):
                            logger.info(f"Marking for deletion (played): {episode.title}")
                            to_delete.append((download, episode))
                        else:
                            logger.info(f"Keeping (unplayed): {episode.title}")
                    else:
                        # No Plex integration - delete based on age only
                        to_delete.append((download, episode))

                # Delete marked episodes
                for download, episode in to_delete:
                    if download.file_path:
                        full_path = file_manager.base_path / download.file_path
                        file_manager.delete_file(full_path)

                    await session.delete(download)

                await session.commit()
```

### 3. Add Configuration (`src/podcastmanager/config.py`)

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Plex Integration (optional)
    PLEX_ENABLED: bool = False
    PLEX_URL: str = "http://localhost:32400"
    PLEX_TOKEN: str = ""
    PLEX_LIBRARY: str = "Podcasts"
```

### 4. Add Dependency (`requirements.txt`)

```
PlexAPI==4.15.0
```

## Behavior

### Without Plex Integration (Current)
- Keep only the 3 most recent episodes
- Delete anything older

### With Plex Integration (Enhanced)
- Always keep the 3 most recent episodes
- For older episodes:
  - If played in Plex → Delete
  - If not played → Keep (until manually removed or played)

## Benefits

1. **Never lose unlistened episodes** - If you haven't listened yet, it stays
2. **Auto-cleanup after listening** - Once played, it gets cleaned up
3. **Respects your listening habits** - Works with how you actually use Plex
4. **Backward compatible** - Works without Plex (just uses age-based cleanup)

## Future Enhancements

- Support for partially played episodes (track progress %)
- Configurable "keep unplayed for X days" policy
- Multiple Plex servers support
- Sync play status back to podcast app

## Installation Steps

1. Install PlexAPI: `pip install PlexAPI==4.15.0`
2. Get your Plex token (see above)
3. Add Plex settings to `.env`
4. Restart the server
5. Cleanup job will now respect Plex play status

## Testing

```bash
# Test Plex connection
python3 -c "from plexapi.server import PlexServer; print(PlexServer('YOUR_URL', 'YOUR_TOKEN').library.sections())"

# Should show your libraries including "Podcasts"
```
