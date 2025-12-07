# Rocky Linux Quick Start Guide

## Installation

### One-Command Install
```bash
sudo bash install-rocky-linux.sh
```

### Manual Install
See `ROCKY-LINUX-INSTALL.md` for detailed steps.

## Service Management

### Using the Management Script (Easiest)

```bash
# Start everything
sudo ./manage.sh start

# Stop everything
sudo ./manage.sh stop

# Restart
sudo ./manage.sh restart

# Check status
sudo ./manage.sh status

# View logs
sudo ./manage.sh logs

# Build frontend for production
sudo ./manage.sh build-frontend
```

### Using systemctl Directly

```bash
# Backend service
sudo systemctl start podcast-manager-backend
sudo systemctl stop podcast-manager-backend
sudo systemctl restart podcast-manager-backend
sudo systemctl status podcast-manager-backend

# Frontend dev service (if not using nginx)
sudo systemctl start podcast-manager-frontend-dev
sudo systemctl stop podcast-manager-frontend-dev
```

## First-Time Setup

1. **Install:**
   ```bash
   sudo bash install-rocky-linux.sh
   ```

2. **Configure:**
   ```bash
   sudo nano /opt/podcast-manager/.env
   ```

   Set:
   - `DOWNLOAD_BASE_PATH=/mnt/media/podcasts`
   - `PLEX_ENABLED=true` (if using Plex)
   - `PLEX_TOKEN=your-token`
   - `PLEX_URL=http://localhost:32400`

3. **Start:**
   ```bash
   sudo ./manage.sh start
   ```

4. **Access:**
   - Frontend: `http://your-server-ip/` (with nginx)
   - Frontend Dev: `http://your-server-ip:5173/` (without nginx)
   - API Docs: `http://your-server-ip:8000/docs`

## Common Tasks

### View Logs in Real-Time
```bash
sudo ./manage.sh logs
# or
sudo journalctl -u podcast-manager-backend -f
```

### Rebuild Frontend
```bash
sudo ./manage.sh build-frontend
sudo systemctl restart nginx
```

### Check What's Running
```bash
sudo ./manage.sh status
# or
sudo netstat -tlnp | grep -E '8000|5173|80'
```

### Restart After Config Changes
```bash
sudo ./manage.sh restart
```

### Enable Auto-Start on Boot
```bash
sudo ./manage.sh enable
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo ./manage.sh logs-backend

# Test manually
sudo ./manage.sh test-backend
```

### Can't Access from Network
```bash
# Check firewall
sudo firewall-cmd --list-all

# Open ports if needed
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

### Permission Errors
```bash
sudo chown -R podcastmgr:podcastmgr /opt/podcast-manager
sudo chown -R podcastmgr:podcastmgr /mnt/media/podcasts
```

### Database Issues
```bash
cd /opt/podcast-manager
sudo rm podcast_manager.db
sudo -u podcastmgr bash -c "source venv/bin/activate && python3 -m podcastmanager.main init-db"
sudo ./manage.sh restart
```

## File Locations

- **Application:** `/opt/podcast-manager/`
- **Config:** `/opt/podcast-manager/.env`
- **Database:** `/opt/podcast-manager/podcast_manager.db`
- **Downloads:** `/mnt/media/podcasts/` (or your configured path)
- **Services:** `/etc/systemd/system/podcast-manager-*.service`
- **Nginx Config:** `/etc/nginx/conf.d/podcast-manager.conf`

## URLs

- **Frontend:** `http://your-server/`
- **API Docs:** `http://your-server:8000/docs`
- **Health Check:** `http://your-server:8000/api/health`

## Service User

All services run as: `podcastmgr`

Switch to this user for debugging:
```bash
sudo -u podcastmgr bash
```

## Quick Commands Reference

| Task | Command |
|------|---------|
| Start | `sudo ./manage.sh start` |
| Stop | `sudo ./manage.sh stop` |
| Restart | `sudo ./manage.sh restart` |
| Status | `sudo ./manage.sh status` |
| Logs | `sudo ./manage.sh logs` |
| Enable auto-start | `sudo ./manage.sh enable` |
| Disable auto-start | `sudo ./manage.sh disable` |
| Build frontend | `sudo ./manage.sh build-frontend` |

## Getting Help

1. Check logs: `sudo ./manage.sh logs`
2. Check status: `sudo ./manage.sh status`
3. Test backend: `sudo ./manage.sh test-backend`
4. See full guide: `ROCKY-LINUX-INSTALL.md`
