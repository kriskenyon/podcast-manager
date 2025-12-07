# Podcast Manager for Plex

A modern, standalone Python application for managing podcast downloads and organizing them for Plex Media Server.

## Features

- 🎙️ **Podcast Management** - Add podcasts via RSS feeds or Apple Podcast search
- 📥 **Smart Downloads** - Configurable episode limits with automatic downloads
- 📁 **Organized Storage** - Automatic folder organization by podcast name
- 🔄 **OPML Support** - Import and export podcast subscriptions
- 🍎 **Apple Podcast Integration** - Search and discover podcasts via iTunes API
- 🌐 **Web Interface** - Modern web UI for easy management
- 🔄 **Background Processing** - Automatic feed refresh and download management
- 🐳 **Docker Ready** - Easy deployment with Docker support

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Linux/macOS/Windows

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pd
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (especially DOWNLOAD_BASE_PATH)
   ```

5. **Initialize database**
   ```bash
   python -m podcastmanager.main init-db
   ```

6. **Start the server**
   ```bash
   python -m podcastmanager.main serve
   ```

7. **Access the application**
   - Open your browser to `http://localhost:8000`
   - API documentation at `http://localhost:8000/docs`

## Configuration

All configuration is done via environment variables or the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DOWNLOAD_BASE_PATH` | `./downloads` | Directory where podcasts will be downloaded |
| `DATABASE_URL` | `sqlite+aiosqlite:///./podcast_manager.db` | Database connection string |
| `MAX_CONCURRENT_DOWNLOADS` | `3` | Maximum simultaneous downloads |
| `DEFAULT_MAX_EPISODES` | `3` | Default number of episodes to keep per podcast |
| `FEED_REFRESH_INTERVAL` | `3600` | Feed check interval in seconds (1 hour) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

See `.env.example` for all available options.

## Plex Integration

### Setting up Plex

1. Configure your download path in `.env`:
   ```
   DOWNLOAD_BASE_PATH=/mnt/media/podcasts
   ```

2. In Plex, create a new **Music** library

3. Point the library to your download path (`/mnt/media/podcasts`)

4. Plex will organize podcasts as:
   - Each podcast = Artist
   - Each episode = Track

### File Organization

Podcasts are organized as:
```
/mnt/media/podcasts/
├── The Daily/
│   ├── 2025-01-15-Episode-Title.mp3
│   ├── 2025-01-14-Another-Episode.mp3
│   └── 2025-01-13-Previous-Episode.mp3
├── Reply All/
│   └── 2025-01-12-Episode-123.mp3
└── Radiolab/
    └── 2025-01-10-Science-Story.mp3
```

## OPML Import/Export

### Import Podcasts from OPML

Import your podcast subscriptions from other apps (Apple Podcasts, Overcast, Pocket Casts, etc.):

1. Export OPML from your current podcast app
2. Open Podcast Manager web interface
3. Navigate to **OPML** page
4. Click **Choose File** and select your OPML file
5. Optionally preview podcasts before importing
6. Click **Import All Podcasts**

**API Usage:**
```bash
curl -X POST http://localhost:8000/api/opml/import \
  -F "file=@subscriptions.opml" \
  -F "max_episodes_to_keep=3" \
  -F "auto_download=true"
```

### Export Podcasts to OPML

Export your current subscriptions to move to another app:

1. Open Podcast Manager web interface
2. Navigate to **OPML** page
3. Click **Download OPML File**
4. Import the file in your target podcast app

**API Usage:**
```bash
curl http://localhost:8000/api/opml/export > subscriptions.opml
```

## Development

### Install development dependencies

```bash
pip install -r requirements-dev.txt
```

### Run tests

```bash
pytest
```

### Code formatting

```bash
black src/ tests/
```

### Linting

```bash
ruff check src/ tests/
```

## CLI Commands

```bash
# Start the web server
python -m podcastmanager.main serve

# Start with auto-reload (development)
python -m podcastmanager.main serve --reload

# Initialize database
python -m podcastmanager.main init-db

# Reset database (WARNING: Deletes all data!)
python -m podcastmanager.main reset-db
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Deployment

### Rocky Linux (Production)

**Quick Setup:**
```bash
# Clone and install
sudo git clone https://github.com/YOUR_USERNAME/podcast-manager.git /opt/podcast-manager
cd /opt/podcast-manager
sudo bash install-rocky-linux.sh
```

**Easy Updates:**
```bash
# Pull latest changes and restart
cd /opt/podcast-manager
sudo ./update.sh
```

See `GIT-QUICK-START.md` for details.

### Docker Deployment

(Coming soon)

```bash
docker-compose up -d
```

## Project Structure

```
pd/
├── src/podcastmanager/      # Main application code
│   ├── api/                  # API routes and schemas
│   ├── core/                 # Core business logic
│   ├── db/                   # Database models and migrations
│   ├── services/             # Service layer (OPML, downloads, etc.)
│   ├── tasks/                # Background jobs
│   └── utils/                # Utilities and helpers
├── frontend/                 # Web UI templates and static files
├── tests/                    # Test suite
├── docker/                   # Docker configuration
└── requirements.txt          # Python dependencies
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and feature requests, please use the GitHub issue tracker.

## Roadmap

- [x] Phase 1: Foundation (database, config, FastAPI app)
- [x] Phase 2: Core functionality (RSS parsing, podcast management)
- [x] Phase 3: Download engine
- [x] Phase 4: Background tasks with Plex integration
- [ ] Phase 5: Apple Podcast search
- [x] Phase 6: OPML support
- [x] Phase 7: Web interface (Vue 3)
- [x] Phase 8: Production readiness (Rocky Linux deployment)

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [feedparser](https://feedparser.readthedocs.io/) - RSS parsing
- [APScheduler](https://apscheduler.readthedocs.io/) - Background jobs
