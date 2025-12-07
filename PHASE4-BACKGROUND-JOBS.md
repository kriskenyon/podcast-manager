# Phase 4 Complete: Background Tasks ✅

Everything is now automatic! The Podcast Manager runs background jobs to refresh feeds, process downloads, and cleanup old episodes.

## What's New in Phase 4

### 1. Task Scheduler (`tasks/worker.py`)
- **APScheduler** integration with AsyncIO
- Manages all background jobs
- Configurable job intervals
- Job pause/resume capabilities
- Manual job triggering

### 2. Background Jobs (`tasks/jobs.py`)

#### Feed Refresh Job
- **Runs**: Every hour (configurable via `FEED_REFRESH_INTERVAL`)
- **What it does**:
  - Fetches latest RSS feed for each podcast
  - Discovers new episodes
  - Auto-queues downloads if `auto_download=true`
  - Updates `last_checked` timestamp

#### Download Processor Job
- **Runs**: Every 5 minutes
- **What it does**:
  - Processes pending downloads
  - Downloads up to 3 episodes concurrently
  - Updates download status and progress
  - Automatically retries failed downloads

#### Cleanup Job
- **Runs**: Every 24 hours (configurable via `CLEANUP_INTERVAL`)
- **What it does**:
  - Removes episodes beyond `max_episodes_to_keep`
  - Deletes old episode files
  - Frees up disk space
  - Cleans up empty directories

### 3. Job Management API
- `GET /api/jobs` - List all scheduled jobs
- `POST /api/jobs/{id}/trigger` - Run job immediately
- `POST /api/jobs/{id}/pause` - Pause a job
- `POST /api/jobs/{id}/resume` - Resume a paused job

### 4. Lifecycle Integration
- Scheduler starts automatically with the application
- Stops gracefully on shutdown
- Jobs run in the background without blocking requests

## How It Works

### The Automation Flow

```
1. Feed Refresh Job (every hour)
   ↓
   Checks all podcasts for new episodes
   ↓
   If auto_download=true → Queues new episodes
   ↓
2. Download Processor (every 5 minutes)
   ↓
   Processes queued downloads
   ↓
   Downloads episodes to organized folders
   ↓
3. Cleanup Job (every 24 hours)
   ↓
   Removes episodes beyond max_episodes_to_keep
   ↓
   Frees disk space
```

### Job Schedule

| Job | Interval | Runs On Startup | Description |
|-----|----------|----------------|-------------|
| Feed Refresh | 1 hour (3600s) | ✅ Yes | Check for new episodes |
| Download Processor | 5 minutes (300s) | ✅ Yes | Process pending downloads |
| Cleanup | 24 hours (86400s) | ❌ No | Remove old episodes |

## Configuration

### Environment Variables

```bash
# Feed refresh interval (seconds)
FEED_REFRESH_INTERVAL=3600  # 1 hour

# Cleanup settings
AUTO_CLEANUP_ENABLED=true
CLEANUP_INTERVAL=86400  # 24 hours

# Download settings
MAX_CONCURRENT_DOWNLOADS=3
```

### Per-Podcast Settings

When you add a podcast, you can configure:

```bash
curl -X POST http://localhost:8000/api/podcasts \
  -H "Content-Type: application/json" \
  -d '{
    "rss_url": "https://feeds.example.com/podcast.rss",
    "max_episodes_to_keep": 5,    # Keep 5 most recent episodes
    "auto_download": true           # Auto-download new episodes
  }'
```

- **max_episodes_to_keep**: How many episodes to keep (1-100)
- **auto_download**: If `true`, new episodes are automatically queued for download

## Testing Background Jobs

### Quick Test

```bash
./test_background_jobs.sh
```

This will:
1. List all scheduled jobs
2. Add a test podcast with auto_download enabled
3. Manually trigger feed refresh
4. Check for queued downloads
5. Trigger download processor
6. View job statuses

### Manual Testing

#### 1. View All Scheduled Jobs

```bash
curl http://localhost:8000/api/jobs | python3 -m json.tool
```

Response:
```json
{
  "jobs": [
    {
      "id": "refresh_podcasts",
      "name": "Refresh Podcast Feeds",
      "next_run_time": "2025-01-15T14:30:00",
      "trigger": "interval[0:01:00:00]"
    },
    {
      "id": "process_downloads",
      "name": "Process Download Queue",
      "next_run_time": "2025-01-15T13:35:00",
      "trigger": "interval[0:00:05:00]"
    },
    {
      "id": "cleanup_episodes",
      "name": "Cleanup Old Episodes",
      "next_run_time": "2025-01-16T13:30:00",
      "trigger": "interval[1 day, 0:00:00]"
    }
  ]
}
```

#### 2. Manually Trigger a Job

```bash
# Trigger feed refresh immediately
curl -X POST http://localhost:8000/api/jobs/refresh_podcasts/trigger | python3 -m json.tool

# Trigger download processor
curl -X POST http://localhost:8000/api/jobs/process_downloads/trigger | python3 -m json.tool

# Trigger cleanup job
curl -X POST http://localhost:8000/api/jobs/cleanup_episodes/trigger | python3 -m json.tool
```

#### 3. Pause/Resume Jobs

```bash
# Pause cleanup job
curl -X POST http://localhost:8000/api/jobs/cleanup_episodes/pause | python3 -m json.tool

# Resume cleanup job
curl -X POST http://localhost:8000/api/jobs/cleanup_episodes/resume | python3 -m json.tool
```

## Watching Background Jobs in Action

### Monitor Server Logs

```bash
# If you set LOG_FILE in .env
tail -f logs/podcast_manager.log

# Or watch the console output when running the server
./run.sh serve
```

You'll see log entries like:

```
2025-01-15 13:30:00 | INFO | === Starting podcast feed refresh job ===
2025-01-15 13:30:02 | INFO | Refreshing 3 podcasts...
2025-01-15 13:30:05 | INFO | Queueing 2 episodes from The Daily
2025-01-15 13:30:07 | SUCCESS | Feed refresh complete: 3/3 podcasts refreshed, 2 episodes queued
2025-01-15 13:30:07 | INFO | === Podcast feed refresh job finished ===

2025-01-15 13:35:00 | INFO | === Starting download queue processor ===
2025-01-15 13:35:01 | INFO | Processing 2 pending downloads...
2025-01-15 13:35:45 | SUCCESS | Download complete: Episode Title (45.2 MB)
2025-01-15 13:36:20 | SUCCESS | Download queue processed: 2 downloads
2025-01-15 13:36:20 | INFO | === Download queue processor finished ===
```

### Check Job Execution

```bash
# View jobs to see next run time
curl -s http://localhost:8000/api/jobs | python3 -c "import sys, json; jobs=json.load(sys.stdin)['jobs']; [print(f\"{j['name']}: next run at {j['next_run_time']}\") for j in jobs]"
```

## Complete Automation Example

### 1. Add a Podcast with Auto-Download

```bash
curl -X POST http://localhost:8000/api/podcasts \
  -H "Content-Type: application/json" \
  -d '{
    "rss_url": "https://feeds.simplecast.com/54nAGcIl",
    "max_episodes_to_keep": 3,
    "auto_download": true
  }'
```

### 2. What Happens Automatically

**Immediately** (on first add):
- RSS feed is parsed
- 3 most recent episodes are discovered
- Episodes are queued for download
- Download processor picks them up within 5 minutes

**Every Hour**:
- Feed is refreshed
- New episodes are discovered
- New episodes are auto-queued (if auto_download=true)

**Every 5 Minutes**:
- Pending downloads are processed
- Files are downloaded to `downloads/{podcast-name}/`
- Progress is tracked in database

**Every 24 Hours**:
- Old episodes beyond max_episodes_to_keep=3 are deleted
- Disk space is freed
- Only 3 most recent episodes remain

### 3. Monitor Progress

```bash
# Check downloads
curl http://localhost:8000/api/downloads | python3 -m json.tool

# Check podcast episodes
curl http://localhost:8000/api/podcasts/1/episodes | python3 -m json.tool

# View downloaded files
ls -lh downloads/The-Daily/
```

## Features Implemented

✅ **Automatic Feed Refresh** - Checks for new episodes hourly
✅ **Automatic Downloads** - Downloads new episodes automatically
✅ **Automatic Cleanup** - Removes old episodes to save space
✅ **Configurable Intervals** - Adjust job frequencies via config
✅ **Manual Triggers** - Run any job on demand
✅ **Job Control** - Pause/resume individual jobs
✅ **Startup Execution** - Important jobs run immediately
✅ **Graceful Shutdown** - Jobs stop cleanly on app shutdown
✅ **Concurrent Limiting** - Max 3 downloads at once
✅ **Error Recovery** - Failed downloads are retried automatically

## Job Details

### Feed Refresh Job

**Purpose**: Keep podcast episodes up to date

**Triggers**:
- Every hour (configurable)
- Runs immediately on app startup
- Can be manually triggered

**Actions**:
1. Gets all podcasts from database
2. Fetches latest RSS feed for each
3. Compares with existing episodes (by GUID)
4. Adds new episodes to database
5. If `auto_download=true`, queues new episodes
6. Updates `last_checked` timestamp

**Configuration**:
```bash
FEED_REFRESH_INTERVAL=3600  # seconds (1 hour)
```

### Download Processor Job

**Purpose**: Process queued downloads

**Triggers**:
- Every 5 minutes
- Runs immediately on app startup
- Can be manually triggered

**Actions**:
1. Finds all pending downloads
2. Processes up to max_concurrent downloads
3. Downloads files asynchronously
4. Updates progress in real-time
5. Marks as completed or failed

**Respects**:
- `MAX_CONCURRENT_DOWNLOADS=3` setting
- Download timeouts
- Disk space limits

### Cleanup Job

**Purpose**: Manage disk space

**Triggers**:
- Every 24 hours (configurable)
- Does NOT run on startup
- Can be manually triggered

**Actions**:
1. For each podcast, finds completed downloads
2. Sorts by publication date (newest first)
3. Keeps `max_episodes_to_keep` episodes
4. Deletes older episodes and files
5. Cleans up empty directories
6. Logs space freed

**Configuration**:
```bash
AUTO_CLEANUP_ENABLED=true
CLEANUP_INTERVAL=86400  # seconds (24 hours)
```

## API Reference

### List Jobs
```http
GET /api/jobs
```

Returns information about all scheduled jobs including next run times.

### Trigger Job
```http
POST /api/jobs/{job_id}/trigger
```

Job IDs:
- `refresh_podcasts` - Feed refresh job
- `process_downloads` - Download processor
- `cleanup_episodes` - Cleanup job

### Pause Job
```http
POST /api/jobs/{job_id}/pause
```

Prevents the job from running until resumed.

### Resume Job
```http
POST /api/jobs/{job_id}/resume
```

Resumes a paused job.

## Troubleshooting

### Jobs not running

**Check scheduler status:**
```bash
curl http://localhost:8000/api/jobs
```

If empty or error, restart the server:
```bash
./run.sh serve
```

### Feed refresh not finding new episodes

**Manually trigger:**
```bash
curl -X POST http://localhost:8000/api/jobs/refresh_podcasts/trigger
```

**Check podcast last_checked:**
```bash
curl http://localhost:8000/api/podcasts/1 | python3 -c "import sys, json; print(json.load(sys.stdin).get('last_checked'))"
```

### Downloads not processing

**Check pending count:**
```bash
curl "http://localhost:8000/api/downloads?status=pending" | python3 -c "import sys, json; print(f\"Pending: {json.load(sys.stdin)['total']}\")"
```

**Manually trigger processor:**
```bash
curl -X POST http://localhost:8000/api/jobs/process_downloads/trigger
```

### Too much disk usage

**Trigger cleanup immediately:**
```bash
curl -X POST http://localhost:8000/api/jobs/cleanup_episodes/trigger
```

**Reduce episode limits:**
```bash
curl -X PUT http://localhost:8000/api/podcasts/1 \
  -H "Content-Type: application/json" \
  -d '{"max_episodes_to_keep": 2}'
```

## What's Next?

With Phase 4 complete, your Podcast Manager is fully automated! Future enhancements could include:

### Phase 5 - Apple Podcast Search (Optional)
- Search iTunes Podcast directory
- Add podcasts from search results
- Browse by category

### Phase 6 - OPML Import/Export (Optional)
- Import podcast subscriptions from other apps
- Export your subscriptions
- Share podcast lists

### Phase 7 - Web Interface (Optional)
- Modern web UI for browsing
- Visual podcast management
- Download progress visualization
- Settings management

### Phase 8 - Production Features (Optional)
- User authentication
- Multi-user support
- Webhooks for notifications
- Statistics and analytics
- Docker compose setup

## Summary

🎉 **Your Podcast Manager is now fully automated!**

- ✅ Automatically checks for new episodes
- ✅ Automatically downloads new episodes
- ✅ Automatically cleans up old episodes
- ✅ Organizes files perfectly for Plex
- ✅ Runs in the background
- ✅ No manual intervention needed

Just add podcasts and let it run!

```bash
# Add a podcast
curl -X POST http://localhost:8000/api/podcasts \
  -H "Content-Type: application/json" \
  -d '{
    "rss_url": "https://feeds.example.com/podcast.rss",
    "max_episodes_to_keep": 5,
    "auto_download": true
  }'

# That's it! Everything else is automatic.
```

Point Plex to `downloads/` and enjoy your podcasts! 🎧
