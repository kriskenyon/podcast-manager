# Testing Guide - Phase 2: Core Functionality

## Phase 2 Complete! ✅

You can now add podcasts, parse RSS feeds, and discover episodes!

## What's New

### API Endpoints

#### Podcasts
- `POST /api/podcasts` - Add a new podcast from RSS feed
- `GET /api/podcasts` - List all podcasts (paginated)
- `GET /api/podcasts/{id}` - Get podcast details
- `PUT /api/podcasts/{id}` - Update podcast settings
- `DELETE /api/podcasts/{id}` - Delete a podcast
- `POST /api/podcasts/{id}/refresh` - Manually refresh feed

#### Episodes
- `GET /api/podcasts/{id}/episodes` - List episodes for a podcast
- `GET /api/episodes/{id}` - Get episode details
- `GET /api/podcasts/{id}/with-episodes` - Get podcast with all episodes

## Quick Test

### Option 1: Automated Test Script

```bash
./test_api.sh
```

This will:
1. Test the health check
2. Add a test podcast (The Daily from NY Times)
3. List all podcasts
4. Get podcast details
5. List episodes
6. Get podcast with episodes

### Option 2: Manual Testing with curl

#### 1. Add a podcast

```bash
curl -X POST http://localhost:8000/api/podcasts \
  -H "Content-Type: application/json" \
  -d '{
    "rss_url": "https://feeds.simplecast.com/54nAGcIl",
    "max_episodes_to_keep": 3,
    "auto_download": false
  }' | python3 -m json.tool
```

#### 2. List all podcasts

```bash
curl http://localhost:8000/api/podcasts | python3 -m json.tool
```

#### 3. Get podcast details (replace {id} with actual ID)

```bash
curl http://localhost:8000/api/podcasts/1 | python3 -m json.tool
```

#### 4. List episodes for a podcast

```bash
curl http://localhost:8000/api/podcasts/1/episodes | python3 -m json.tool
```

#### 5. Refresh a podcast feed

```bash
curl -X POST http://localhost:8000/api/podcasts/1/refresh | python3 -m json.tool
```

#### 6. Update podcast settings

```bash
curl -X PUT http://localhost:8000/api/podcasts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "max_episodes_to_keep": 5,
    "auto_download": true
  }' | python3 -m json.tool
```

#### 7. Delete a podcast

```bash
curl -X DELETE http://localhost:8000/api/podcasts/1 | python3 -m json.tool
```

### Option 3: Interactive API Documentation

Visit http://localhost:8000/docs for the Swagger UI where you can:
- See all available endpoints
- Try out requests interactively
- View request/response schemas
- Test different parameters

## Test RSS Feeds

Here are some popular podcast RSS feeds you can test with:

### News
- **The Daily (NY Times)**: `https://feeds.simplecast.com/54nAGcIl`
- **NPR News Now**: `https://feeds.npr.org/500005/podcast.xml`

### Technology
- **Reply All**: `https://feeds.gimletmedia.com/hearreplyall`
- **The Vergecast**: `https://feeds.megaphone.fm/vergecast`

### Science
- **Radiolab**: `https://feeds.wnyc.org/radiolab`
- **Science Vs**: `https://feeds.gimletmedia.com/ScienceVs`

### Comedy
- **Conan O'Brien Needs A Friend**: `https://feeds.simplecast.com/dHoohVNH`

## Expected Behavior

When you add a podcast:
1. ✅ RSS feed is fetched and parsed
2. ✅ Podcast metadata is extracted (title, description, author, image)
3. ✅ Most recent episodes are discovered (up to `max_episodes_to_keep`)
4. ✅ Episode metadata is stored (title, description, audio URL, pub date)
5. ✅ A sanitized folder name is created for future downloads

When you refresh a podcast:
1. ✅ Feed is re-fetched
2. ✅ Podcast metadata is updated
3. ✅ New episodes are discovered and added
4. ✅ `last_checked` timestamp is updated

## Database

You can inspect the database directly:

```bash
# Using sqlite3 (if installed)
sqlite3 podcast_manager.db

# View podcasts
SELECT id, title, rss_url, max_episodes_to_keep FROM podcasts;

# View episodes
SELECT e.id, p.title as podcast, e.title as episode, e.pub_date
FROM episodes e
JOIN podcasts p ON e.podcast_id = p.id
ORDER BY e.pub_date DESC;
```

## Troubleshooting

### Podcast won't add
- Check if the RSS URL is valid and accessible
- Look at the server logs for error messages
- Try the URL in a browser to see if it returns XML

### No episodes found
- Some podcasts may have non-standard RSS formats
- Check the server logs for parsing warnings
- Try refreshing the podcast after adding it

### Server errors
- Check that the database is initialized: `./init-db.sh`
- Ensure all dependencies are installed: `pip3 install -r requirements.txt`
- Check server logs for detailed error messages

## Next Steps - Phase 3

The next phase will add:
- ✅ Download engine with progress tracking
- ✅ File organization by podcast
- ✅ Automatic episode downloads
- ✅ Resume failed downloads with retry logic
- ✅ Concurrent download management

Stay tuned!
