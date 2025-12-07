# Phase 3 Complete: Download Engine ✅

Podcast episodes can now be downloaded with full progress tracking, retry logic, and organized file storage!

## What's New in Phase 3

### 1. File Manager Service (`services/file_manager.py`)
- Creates podcast-specific directories
- Generates safe filenames with date prefixes (`2025-01-15-Episode-Title.mp3`)
- Validates paths to prevent security issues
- Checks disk space before downloads
- Calculates storage usage by podcast
- Automatic cleanup of empty directories

### 2. Download Service (`services/download_service.py`)
- Async streaming downloads with aiohttp
- Progress tracking (0.0 to 1.0)
- Resume support for partial downloads
- Timeout handling (configurable, default 1 hour)
- Content-type detection and validation
- Error handling with detailed messages

### 3. Download Engine (`core/download_engine.py`)
- Download queue management
- Concurrent download limiting (default: 3 simultaneous)
- Automatic retry logic (max 3 attempts)
- Status tracking (pending → downloading → completed/failed)
- Batch processing of queued downloads

### 4. Download API Endpoints
- `POST /api/episodes/{id}/download` - Queue episode for download
- `GET /api/downloads` - List all downloads (with status filter)
- `GET /api/downloads/{id}` - Get download status and progress
- `DELETE /api/downloads/{id}` - Delete download and file
- `POST /api/downloads/process-queue` - Manually process queue
- `POST /api/downloads/retry-failed` - Retry failed downloads

## File Organization

### Directory Structure
```
downloads/                          # Base directory (configurable)
├── The-Daily/                      # Podcast folder (sanitized name)
│   ├── 2025-01-15-Latest-News.mp3
│   ├── 2025-01-14-Breaking-Story.mp3
│   └── 2025-01-13-Top-Headlines.mp3
├── Reply-All/
│   └── 2025-01-12-Episode-123.mp3
└── Radiolab/
    └── 2025-01-10-Science-Story.mp3
```

### Filename Format
`{YYYY-MM-DD}-{sanitized-episode-title}.{ext}`

- Date from episode pub_date (or current date as fallback)
- Title sanitized (special chars removed, max 150 chars)
- Extension from content-type or URL (.mp3, .m4a, etc.)

### Plex Integration
Point Plex Music library to the `downloads/` directory:
- Each podcast folder = Artist
- Each episode file = Track
- Files are automatically organized and named for Plex

## Download Status Flow

```
pending → downloading → completed
                     ↓
                   failed → (retry) → pending
```

### Status Values
- **pending**: Queued but not started
- **downloading**: Currently downloading (progress 0.0-1.0)
- **completed**: Successfully downloaded
- **failed**: Download failed (see error_message)
- **deleted**: Cancelled or removed

## Testing the Downloads

### Quick Test

```bash
# Run the automated test
./test_downloads.sh
```

This will:
1. Add a test podcast
2. Queue an episode for download
3. Process the download queue
4. Monitor download progress
5. Show completed downloads

### Manual Testing

#### 1. Add a Podcast and Get Episodes

```bash
# Add podcast
curl -X POST http://localhost:8000/api/podcasts \
  -H "Content-Type: application/json" \
  -d '{
    "rss_url": "https://feeds.simplecast.com/54nAGcIl",
    "max_episodes_to_keep": 3
  }'

# List episodes (note the episode ID)
curl http://localhost:8000/api/podcasts/1/episodes | python3 -m json.tool
```

#### 2. Queue a Download

```bash
# Queue episode 1 for download
curl -X POST http://localhost:8000/api/episodes/1/download | python3 -m json.tool
```

Response:
```json
{
  "id": 1,
  "episode_id": 1,
  "status": "pending",
  "file_path": "The-Daily/2025-01-15-Episode-Title.mp3",
  "progress": 0.0,
  "retry_count": 0,
  ...
}
```

#### 3. Process the Download Queue

```bash
# Trigger download processing
curl -X POST http://localhost:8000/api/downloads/process-queue | python3 -m json.tool
```

#### 4. Monitor Download Progress

```bash
# Check download status
curl http://localhost:8000/api/downloads/1 | python3 -m json.tool
```

Response shows progress:
```json
{
  "id": 1,
  "episode_id": 1,
  "status": "downloading",
  "progress": 0.45,  # 45% complete
  "file_size": 25600000,
  ...
}
```

#### 5. List All Downloads

```bash
# All downloads
curl http://localhost:8000/api/downloads | python3 -m json.tool

# Only completed
curl "http://localhost:8000/api/downloads?status=completed" | python3 -m json.tool

# Only failed
curl "http://localhost:8000/api/downloads?status=failed" | python3 -m json.tool
```

#### 6. Retry Failed Downloads

```bash
curl -X POST http://localhost:8000/api/downloads/retry-failed | python3 -m json.tool
```

#### 7. Delete a Download

```bash
# Delete download and file
curl -X DELETE "http://localhost:8000/api/downloads/1?delete_file=true" | python3 -m json.tool

# Delete download but keep file
curl -X DELETE "http://localhost:8000/api/downloads/1?delete_file=false" | python3 -m json.tool
```

## Configuration

### Environment Variables

```bash
# Download settings
DOWNLOAD_BASE_PATH=/mnt/media/podcasts  # Where to save files
MAX_CONCURRENT_DOWNLOADS=3               # Simultaneous downloads
DOWNLOAD_TIMEOUT=3600                    # Timeout in seconds (1 hour)
```

### Per-Podcast Settings

Each podcast can have custom settings:
- `max_episodes_to_keep` - How many episodes to download (1-100)
- `auto_download` - Automatically download new episodes (true/false)

Update with:
```bash
curl -X PUT http://localhost:8000/api/podcasts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "max_episodes_to_keep": 5,
    "auto_download": true
  }'
```

## Features Implemented

✅ **Async Downloads** - Non-blocking concurrent downloads
✅ **Progress Tracking** - Real-time progress (0-100%)
✅ **Resume Support** - Continue partial downloads
✅ **Retry Logic** - Auto-retry up to 3 times
✅ **Queue Management** - Orderly download processing
✅ **Concurrent Limiting** - Max 3 simultaneous downloads
✅ **File Organization** - Automatic folder/file naming
✅ **Disk Space Checking** - Prevents out-of-space errors
✅ **Error Handling** - Detailed error messages
✅ **Timeout Protection** - Configurable timeout
✅ **Status Tracking** - Full lifecycle monitoring

## Checking Your Downloads

### View Downloaded Files

```bash
# List all podcasts
ls -l downloads/

# List episodes for a podcast
ls -lh downloads/The-Daily/

# See file sizes
du -sh downloads/*
```

### Database Queries

```bash
sqlite3 podcast_manager.db << SQL
-- All downloads with status
SELECT
  d.id,
  d.status,
  ROUND(d.progress * 100, 1) as progress_pct,
  e.title as episode,
  d.file_path
FROM downloads d
JOIN episodes e ON d.episode_id = e.id
ORDER BY d.created_at DESC;
SQL
```

## Troubleshooting

### Download stays in "pending"
- Run: `curl -X POST http://localhost:8000/api/downloads/process-queue`
- Downloads need manual queue processing (automatic processing in Phase 4)

### Download fails immediately
- Check the `error_message` field in the download record
- Common issues:
  - Invalid audio URL
  - Network timeout
  - Insufficient disk space
  - File permissions

### Can't find downloaded files
- Check `DOWNLOAD_BASE_PATH` in your .env file
- Default location: `./downloads/`
- Files organized by podcast name

### Progress stuck at 0%
- Download might be starting (large file)
- Check server logs for errors
- Refresh status after a few seconds

## Next Steps - Phase 4: Background Tasks

Phase 4 will add:
- ✅ Automatic feed refresh (periodic checks for new episodes)
- ✅ Automatic download processing (no manual queue trigger needed)
- ✅ Cleanup job (remove old episodes based on podcast settings)
- ✅ APScheduler integration
- ✅ Configurable job intervals

Coming soon!

## API Documentation

Full interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Try out all the download endpoints directly in your browser!
