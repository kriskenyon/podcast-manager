# Complete Setup Guide - Podcast Manager with Vue Frontend

## 🚀 Full Stack Podcast Manager

Complete setup guide for running both the Python backend and Vue frontend together.

## Quick Start (Development)

### Terminal 1: Start Backend

```bash
# From project root (pd/)
./run.sh serve
```

Backend runs on: **http://localhost:8000**
- API: http://localhost:8000/api
- API Docs: http://localhost:8000/docs

### Terminal 2: Start Frontend

```bash
# From project root (pd/)
cd frontend
npm install   # First time only
npm run dev
```

Frontend runs on: **http://localhost:5173**
- UI: http://localhost:5173
- Auto-proxies API requests to backend

### Access the Application

Open your browser to: **http://localhost:5173**

You're done! The Vue app will communicate with the Python backend automatically.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (http://localhost:5173)           │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Vue 3 Frontend (Vite Dev Server)             │  │
│  │  • Modern UI with Tailwind CSS                        │  │
│  │  • Vue Router for navigation                          │  │
│  │  • Pinia for state management                         │  │
│  │  • Axios for API calls                                │  │
│  └────────────┬─────────────────────────────────────────┘  │
└───────────────┼─────────────────────────────────────────────┘
                │ HTTP Requests to /api/*
                │ (proxied by Vite)
                ▼
┌─────────────────────────────────────────────────────────────┐
│           FastAPI Backend (http://localhost:8000)            │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    API Layer                          │  │
│  │  • REST endpoints (/api/*)                           │  │
│  │  • Automatic validation (Pydantic)                   │  │
│  │  • Interactive docs (/docs)                          │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               ▼                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 Business Logic                        │  │
│  │  • Podcast Manager (RSS parsing)                     │  │
│  │  • Download Engine (async downloads)                 │  │
│  │  • File Manager (organization)                       │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               ▼                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Background Tasks (APScheduler)             │  │
│  │  • Feed refresh (hourly)                             │  │
│  │  • Download processor (5 min)                        │  │
│  │  • Cleanup (daily)                                   │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               ▼                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           SQLite Database (podcast_manager.db)        │  │
│  │  • Podcasts, Episodes, Downloads, Settings           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              File System (downloads/)                 │  │
│  │  • Organized podcast folders                         │  │
│  │  • Episode files ready for Plex                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Complete Feature List

### Backend (Python/FastAPI)
✅ RSS feed parsing with feedparser
✅ Podcast and episode management
✅ Async downloads with progress tracking
✅ File organization for Plex
✅ Background jobs (APScheduler)
✅ SQLite database with SQLAlchemy
✅ RESTful API with automatic docs
✅ Retry logic and error handling

### Frontend (Vue 3/Vite)
✅ Modern, responsive UI
✅ Podcast grid with artwork
✅ Episode browsing and downloads
✅ Real-time download progress
✅ Background job management
✅ Auto-refresh capability
✅ Mobile-friendly design

## Development Workflow

### 1. Add a Podcast (via UI)

1. Open http://localhost:5173
2. Click "Add Podcast"
3. Enter RSS URL (or select example)
4. Configure settings
5. Click "Add Podcast"

**What happens**:
- Frontend → POST /api/podcasts
- Backend parses RSS feed
- Episodes are discovered
- If auto_download=true, episodes are queued
- Background job processes downloads

### 2. Monitor Downloads

1. Click "Downloads" in navigation
2. See all downloads with progress
3. Filter by status
4. Enable auto-refresh for live updates

### 3. Manage Background Jobs

1. Click "Jobs" in navigation
2. View all scheduled tasks
3. Manually trigger jobs
4. Pause/resume as needed

## Configuration

### Backend (.env)

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Database
DATABASE_URL=sqlite+aiosqlite:///./podcast_manager.db

# Downloads
DOWNLOAD_BASE_PATH=/mnt/media/podcasts
MAX_CONCURRENT_DOWNLOADS=3
DEFAULT_MAX_EPISODES=3

# Jobs
FEED_REFRESH_INTERVAL=3600      # 1 hour
CLEANUP_INTERVAL=86400           # 24 hours
```

### Frontend (vite.config.js)

```javascript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

## Testing the Full Stack

### 1. Backend Health Check

```bash
curl http://localhost:8000/api/health
```

### 2. Frontend Dev Server

```bash
# Should show Vite dev server info
curl http://localhost:5173
```

### 3. Add Podcast via API

```bash
curl -X POST http://localhost:8000/api/podcasts \
  -H "Content-Type: application/json" \
  -d '{
    "rss_url": "https://feeds.simplecast.com/54nAGcIl",
    "max_episodes_to_keep": 3,
    "auto_download": true
  }'
```

### 4. View in Frontend

Open http://localhost:5173 and see the podcast appear!

## Production Deployment

### Option 1: Separate Servers

**Backend**:
```bash
# Install dependencies
pip install -r requirements.txt

# Run with gunicorn/uvicorn
uvicorn podcastmanager.main:app --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
# Build
cd frontend
npm run build

# Serve with nginx/Apache
# Point to frontend/dist/
```

### Option 2: Backend Serves Frontend

1. Build frontend: `cd frontend && npm run build`
2. Configure FastAPI to serve `frontend/dist/` as static files
3. Single server deployment

## Troubleshooting

### Frontend can't connect to backend

**Problem**: Network errors in browser console

**Check**:
1. Backend is running on port 8000
2. Frontend proxy is configured in vite.config.js
3. No firewall blocking localhost

**Solution**:
```bash
# Restart both servers
# Terminal 1
./run.sh serve

# Terminal 2
cd frontend && npm run dev
```

### Database errors

**Problem**: Database not found or locked

**Solution**:
```bash
# Re-initialize database
./init-db.sh
```

### Missing dependencies

**Backend**:
```bash
pip install -r requirements.txt
```

**Frontend**:
```bash
cd frontend
npm install
```

## File Organization

```
pd/
├── src/podcastmanager/        # Python backend
├── frontend/                   # Vue frontend
├── downloads/                  # Downloaded podcasts
├── podcast_manager.db          # SQLite database
├── .env                        # Backend config
├── run.sh                      # Backend start script
└── README.md                   # Main documentation
```

## Common Tasks

### Add a Podcast

**Via UI**: Click "Add Podcast" button

**Via API**:
```bash
curl -X POST http://localhost:8000/api/podcasts \
  -H "Content-Type: application/json" \
  -d '{"rss_url": "https://example.com/feed.rss", "max_episodes_to_keep": 5}'
```

### Trigger Background Job

**Via UI**: Jobs page → Click "Run" button

**Via API**:
```bash
curl -X POST http://localhost:8000/api/jobs/refresh_podcasts/trigger
```

### View Downloads

**Via UI**: Downloads page

**Via API**:
```bash
curl http://localhost:8000/api/downloads
```

## Environment Requirements

### Backend
- Python 3.9+
- pip or pip3
- Virtual environment (recommended)

### Frontend
- Node.js 18+
- npm or yarn

### System
- ~500MB disk space for application
- Additional space for podcast downloads
- Linux, macOS, or Windows

## Performance Tips

1. **Concurrent Downloads**: Adjust `MAX_CONCURRENT_DOWNLOADS` based on network
2. **Feed Refresh**: Increase `FEED_REFRESH_INTERVAL` to reduce API calls
3. **Frontend Build**: Run `npm run build` for production (faster than dev)
4. **Database**: SQLite works well for single-user; consider PostgreSQL for multi-user

## Next Steps

With both frontend and backend running, you can:

1. ✅ Add your favorite podcasts
2. ✅ Browse episodes with beautiful UI
3. ✅ Download episodes automatically
4. ✅ Monitor downloads in real-time
5. ✅ Manage background jobs visually
6. ✅ Point Plex to `downloads/` folder
7. ✅ Enjoy automated podcast management!

## Resources

- Backend API Docs: http://localhost:8000/docs
- Frontend Dev: http://localhost:5173
- Project GitHub: (your repo)

## Support

- Backend issues: Check logs and `/docs` endpoint
- Frontend issues: Check browser console
- General issues: See individual PHASE*.md documentation

Enjoy your complete podcast management solution! 🎉
