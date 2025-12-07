# Rocky Linux Installation Guide

Complete guide for setting up Podcast Manager as a systemd service on Rocky Linux.

## Quick Install (Automated)

```bash
# Copy the project to your server
scp -r /path/to/pd/ user@rocky-server:/tmp/

# SSH to server
ssh user@rocky-server

# Run installer
cd /tmp/pd
sudo bash install-rocky-linux.sh
```

## Manual Installation

### 1. Install Dependencies

```bash
# Update system
sudo dnf update -y

# Install Python 3.9+
sudo dnf install -y python39 python39-pip python39-devel gcc sqlite

# Install Node.js
sudo dnf install -y nodejs npm

# Install nginx (optional, for production)
sudo dnf install -y nginx

# Install git (if needed)
sudo dnf install -y git rsync
```

### 2. Create Service User

```bash
# Create dedicated user for the service
sudo useradd -r -s /bin/bash -d /opt/podcast-manager -m podcastmgr
```

### 3. Set Up Application

```bash
# Create directories
sudo mkdir -p /opt/podcast-manager
sudo mkdir -p /mnt/media/podcasts
sudo mkdir -p /opt/podcast-manager/logs

# Copy application files
sudo cp -r /path/to/pd/* /opt/podcast-manager/

# Set ownership
sudo chown -R podcastmgr:podcastmgr /opt/podcast-manager
sudo chown -R podcastmgr:podcastmgr /mnt/media/podcasts
```

### 4. Install Python Dependencies

```bash
# Switch to application directory
cd /opt/podcast-manager

# Create virtual environment
sudo -u podcastmgr python3.9 -m venv venv

# Activate and install
sudo -u podcastmgr bash -c "source venv/bin/activate && pip install --upgrade pip"
sudo -u podcastmgr bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo -u podcastmgr bash -c "source venv/bin/activate && pip install -e ."
```

### 5. Install Frontend Dependencies

```bash
cd /opt/podcast-manager/frontend
sudo -u podcastmgr npm install

# For production, build the frontend
sudo -u podcastmgr npm run build
```

### 6. Configure Environment

```bash
# Copy and edit .env file
sudo cp /opt/podcast-manager/.env.example /opt/podcast-manager/.env
sudo nano /opt/podcast-manager/.env
```

**Important settings to configure:**
```bash
# Download location
DOWNLOAD_BASE_PATH=/mnt/media/podcasts

# Plex integration (optional)
PLEX_ENABLED=true
PLEX_URL=http://localhost:32400
PLEX_TOKEN=your-token-here
PLEX_LIBRARY=Podcasts

# Server settings
HOST=0.0.0.0
PORT=8000
```

### 7. Initialize Database

```bash
sudo -u podcastmgr bash -c "cd /opt/podcast-manager && source venv/bin/activate && python3 -c 'from podcastmanager.db.database import init_db; import asyncio; asyncio.run(init_db())'"
```

### 8. Install Systemd Services

**Backend Service:**
```bash
sudo cp /opt/podcast-manager/podcast-manager-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable podcast-manager-backend.service
```

**Frontend Dev Service (for development):**
```bash
sudo cp /opt/podcast-manager/podcast-manager-frontend-dev.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable podcast-manager-frontend-dev.service
```

### 9. Configure Firewall

```bash
# Allow HTTP and backend port
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=5173/tcp  # If using dev server
sudo firewall-cmd --reload
```

### 10. Configure Nginx (Production - Recommended)

```bash
# Copy nginx config
sudo cp /opt/podcast-manager/nginx-podcast-manager.conf /etc/nginx/conf.d/

# Edit to set your domain
sudo nano /etc/nginx/conf.d/podcast-manager.conf
# Change: server_name podcast-manager.local;
# To: server_name your-domain.com;

# Test configuration
sudo nginx -t

# Enable and start nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 11. Start Services

```bash
# Start backend
sudo systemctl start podcast-manager-backend

# Start frontend (dev) - OR use nginx
sudo systemctl start podcast-manager-frontend-dev

# Check status
sudo systemctl status podcast-manager-backend
sudo systemctl status podcast-manager-frontend-dev
```

## Service Management

### Check Status
```bash
sudo systemctl status podcast-manager-backend
```

### Start/Stop/Restart
```bash
sudo systemctl start podcast-manager-backend
sudo systemctl stop podcast-manager-backend
sudo systemctl restart podcast-manager-backend
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u podcast-manager-backend -f

# Last 100 lines
sudo journalctl -u podcast-manager-backend -n 100

# Today's logs
sudo journalctl -u podcast-manager-backend --since today
```

### Enable/Disable Auto-start
```bash
sudo systemctl enable podcast-manager-backend   # Start on boot
sudo systemctl disable podcast-manager-backend  # Don't start on boot
```

## Accessing the Application

**With Nginx (Production):**
- Frontend: `http://your-server-ip/`
- API Docs: `http://your-server-ip/api/docs`

**With Dev Server:**
- Frontend: `http://your-server-ip:5173/`
- Backend API: `http://your-server-ip:8000/docs`

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u podcast-manager-backend -n 50

# Check file permissions
ls -la /opt/podcast-manager
ls -la /mnt/media/podcasts

# Test manually
sudo -u podcastmgr bash
cd /opt/podcast-manager
source venv/bin/activate
uvicorn podcastmanager.main:app --host 0.0.0.0 --port 8000
```

### Database Issues

```bash
# Reinitialize database
sudo -u podcastmgr bash -c "cd /opt/podcast-manager && rm -f podcast_manager.db && source venv/bin/activate && python3 -m podcastmanager.main init-db"
```

### Permission Errors

```bash
# Fix ownership
sudo chown -R podcastmgr:podcastmgr /opt/podcast-manager
sudo chown -R podcastmgr:podcastmgr /mnt/media/podcasts

# Fix permissions
sudo chmod 755 /opt/podcast-manager
sudo chmod 775 /mnt/media/podcasts
```

### Can't Access from Network

```bash
# Check firewall
sudo firewall-cmd --list-all

# Check if services are listening
sudo netstat -tlnp | grep -E '8000|5173|80'

# Check SELinux (if enabled)
sudo setenforce 0  # Temporarily disable to test
# If this fixes it, configure SELinux properly:
sudo setsebool -P httpd_can_network_connect 1
```

### Frontend Can't Connect to Backend

```bash
# Check backend is running
curl http://localhost:8000/api/health

# If using nginx, check config
sudo nginx -t
sudo tail -f /var/log/nginx/error.log

# If using dev server, check vite.config.js proxy settings
```

## Updating the Application

```bash
# Stop services
sudo systemctl stop podcast-manager-backend
sudo systemctl stop podcast-manager-frontend-dev

# Backup database
sudo cp /opt/podcast-manager/podcast_manager.db /opt/podcast-manager/podcast_manager.db.backup

# Pull/copy new code
cd /opt/podcast-manager
sudo -u podcastmgr git pull  # If using git
# OR
# Copy new files

# Update dependencies
sudo -u podcastmgr bash -c "source venv/bin/activate && pip install -r requirements.txt"
cd frontend
sudo -u podcastmgr npm install
sudo -u podcastmgr npm run build  # For production

# Restart services
sudo systemctl daemon-reload
sudo systemctl start podcast-manager-backend
sudo systemctl start podcast-manager-frontend-dev
```

## Uninstall

```bash
# Stop and disable services
sudo systemctl stop podcast-manager-backend podcast-manager-frontend-dev
sudo systemctl disable podcast-manager-backend podcast-manager-frontend-dev

# Remove service files
sudo rm /etc/systemd/system/podcast-manager-*.service
sudo systemctl daemon-reload

# Remove nginx config
sudo rm /etc/nginx/conf.d/podcast-manager.conf
sudo systemctl restart nginx

# Remove application
sudo rm -rf /opt/podcast-manager

# Remove user (optional)
sudo userdel -r podcastmgr

# Keep downloads or remove
# sudo rm -rf /mnt/media/podcasts
```

## Security Hardening

### 1. Use HTTPS (Recommended)

```bash
# Install certbot
sudo dnf install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### 2. Restrict Access

```bash
# In nginx config, add:
location / {
    allow 192.168.1.0/24;  # Your local network
    deny all;
}
```

### 3. Set Up Log Rotation

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/podcast-manager
```

Add:
```
/opt/podcast-manager/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## Performance Tuning

### Increase Concurrent Downloads

Edit `/opt/podcast-manager/.env`:
```bash
MAX_CONCURRENT_DOWNLOADS=5
```

### Adjust Feed Refresh Interval

```bash
FEED_REFRESH_INTERVAL=7200  # 2 hours instead of 1
```

### Use PostgreSQL (for better performance)

```bash
# Install PostgreSQL
sudo dnf install -y postgresql postgresql-server python3-psycopg2

# Initialize and start
sudo postgresql-setup --initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Update .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/podcast_manager
```

## Support

For issues, check:
- System logs: `sudo journalctl -xe`
- Application logs: `sudo journalctl -u podcast-manager-backend -f`
- Nginx logs: `sudo tail -f /var/log/nginx/error.log`
