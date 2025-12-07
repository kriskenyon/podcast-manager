# Git-Based Deployment Guide

This guide shows how to use Git for version control and easy deployment to your Rocky Linux server.

## Initial Setup (One Time)

### 1. Initialize Git Repository (Local)

```bash
cd /path/to/pd
git init
git add .
git commit -m "Initial commit: Podcast Manager application"
```

### 2. Create Remote Repository

Choose one of these options:

#### Option A: GitHub (Recommended)

1. Go to https://github.com/new
2. Create a new repository (e.g., `podcast-manager`)
3. Don't initialize with README (we already have code)

```bash
# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/podcast-manager.git

# Push to GitHub
git branch -M main
git push -u origin main
```

#### Option B: GitLab

```bash
git remote add origin https://gitlab.com/YOUR_USERNAME/podcast-manager.git
git branch -M main
git push -u origin main
```

#### Option C: Self-Hosted Git (Gitea, Gogs, etc.)

```bash
git remote add origin https://your-git-server.com/username/podcast-manager.git
git branch -M main
git push -u origin main
```

#### Option D: Private Bare Repository on Server

```bash
# On Rocky Linux server
sudo mkdir -p /opt/git/podcast-manager.git
sudo chown podcastmgr:podcastmgr /opt/git/podcast-manager.git
sudo -u podcastmgr git init --bare /opt/git/podcast-manager.git

# On local machine
git remote add origin ssh://user@your-server:/opt/git/podcast-manager.git
git push -u origin main
```

## Deploy to Rocky Linux Server

### Method 1: Fresh Installation (First Time)

```bash
# SSH to server
ssh user@rocky-server

# Clone repository
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/podcast-manager.git podcast-manager

# Set ownership
sudo chown -R podcastmgr:podcastmgr /opt/podcast-manager

# Run installation
cd /opt/podcast-manager
sudo bash install-rocky-linux.sh
```

### Method 2: Update Existing Installation

```bash
# SSH to server
ssh user@rocky-server

# Pull latest changes
cd /opt/podcast-manager
sudo -u podcastmgr git pull origin main

# Update dependencies (if requirements.txt changed)
sudo -u podcastmgr bash -c "source venv/bin/activate && pip install -r requirements.txt"

# Update frontend (if frontend changed)
cd frontend
sudo -u podcastmgr npm install
sudo -u podcastmgr npm run build

# Restart services
sudo systemctl restart podcast-manager-backend
sudo systemctl restart nginx  # If using nginx
```

### Method 3: Automated Update Script

Create `/opt/podcast-manager/update.sh`:

```bash
#!/bin/bash
# Automated update script for Podcast Manager

set -e  # Exit on error

echo "================================================"
echo "Podcast Manager - Update Script"
echo "================================================"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Navigate to app directory
cd /opt/podcast-manager

# Backup database
echo "1. Backing up database..."
cp podcast_manager.db podcast_manager.db.backup-$(date +%Y%m%d-%H%M%S)

# Pull latest changes
echo "2. Pulling latest changes from git..."
sudo -u podcastmgr git fetch origin
sudo -u podcastmgr git pull origin main

# Update Python dependencies
echo "3. Updating Python dependencies..."
sudo -u podcastmgr bash -c "source venv/bin/activate && pip install -r requirements.txt"

# Update frontend dependencies and build
echo "4. Updating frontend..."
cd frontend
sudo -u podcastmgr npm install
sudo -u podcastmgr npm run build

# Restart services
echo "5. Restarting services..."
systemctl restart podcast-manager-backend

if systemctl is-active --quiet nginx; then
    systemctl restart nginx
fi

echo
echo "================================================"
echo "Update Complete!"
echo "================================================"
echo
echo "Services restarted. Check status:"
echo "  sudo systemctl status podcast-manager-backend"
echo
```

Make it executable:

```bash
sudo chmod +x /opt/podcast-manager/update.sh
```

Usage:

```bash
sudo /opt/podcast-manager/update.sh
```

## Daily Development Workflow

### On Your Local Machine

```bash
# Make changes to code
vim src/podcastmanager/...

# Test locally
python -m podcastmanager.main serve

# Commit changes
git add .
git commit -m "Description of changes"

# Push to remote
git push origin main
```

### Deploy to Server

```bash
# SSH and pull latest
ssh user@rocky-server
cd /opt/podcast-manager
sudo ./update.sh
```

## Managing Secrets

**IMPORTANT:** Never commit sensitive files to Git!

### Files to Keep Secret (Already in .gitignore)

- `.env` - Contains passwords, API keys, tokens
- `podcast_manager.db` - Database with user data
- `downloads/` - Actual podcast files

### Setting Up Environment on Server

After cloning, create `.env` file on server:

```bash
sudo -u podcastmgr nano /opt/podcast-manager/.env
```

Copy your settings from `.env.example` and customize:

```bash
# Download location
DOWNLOAD_BASE_PATH=/mnt/media/podcasts

# Plex integration
PLEX_ENABLED=true
PLEX_TOKEN=your-secret-token-here
PLEX_URL=http://localhost:32400
PLEX_LIBRARY=Podcasts

# Server settings
HOST=0.0.0.0
PORT=8000
```

## Branching Strategy (Optional)

For more advanced workflow:

```bash
# Create development branch
git checkout -b development

# Make changes on development
git add .
git commit -m "Feature: new feature"
git push origin development

# When ready, merge to main
git checkout main
git merge development
git push origin main
```

Then deploy `main` to production, `development` to testing server.

## Rollback (If Update Breaks)

```bash
# View recent commits
git log --oneline -5

# Rollback to previous commit
sudo -u podcastmgr git reset --hard COMMIT_HASH

# Restore database backup
cp podcast_manager.db.backup-YYYYMMDD-HHMMSS podcast_manager.db

# Restart services
sudo systemctl restart podcast-manager-backend
```

## Best Practices

### 1. Commit Messages

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Fix: Resolve duplicate episode GUID issue in OPML import"
git commit -m "Feature: Add HTML sanitization for show notes"
git commit -m "Update: Improve error handling in download service"

# Bad
git commit -m "fix bug"
git commit -m "updates"
```

### 2. Regular Commits

Commit frequently, push daily:

```bash
# End of day
git add .
git commit -m "Day's work: improved error handling and added tests"
git push origin main
```

### 3. Tag Releases

Mark stable versions:

```bash
git tag -a v1.0.0 -m "Version 1.0.0: Initial production release"
git push origin v1.0.0
```

Deploy specific version:

```bash
cd /opt/podcast-manager
sudo -u podcastmgr git fetch --tags
sudo -u podcastmgr git checkout v1.0.0
sudo ./update.sh
```

## Quick Reference

```bash
# Local Development
git status                    # Check what's changed
git add .                     # Stage all changes
git commit -m "message"       # Commit changes
git push origin main          # Push to remote

# Server Deployment
ssh user@server
cd /opt/podcast-manager
sudo ./update.sh              # Update and restart

# Check logs after update
sudo journalctl -u podcast-manager-backend -f

# Rollback if needed
sudo -u podcastmgr git reset --hard HEAD~1
sudo systemctl restart podcast-manager-backend
```

## Troubleshooting

### Merge Conflicts

If you've modified files on both local and server:

```bash
# On server, stash local changes
sudo -u podcastmgr git stash

# Pull latest
sudo -u podcastmgr git pull origin main

# Reapply local changes (may need manual merge)
sudo -u podcastmgr git stash pop
```

### Permission Issues

```bash
# Fix git ownership
sudo chown -R podcastmgr:podcastmgr /opt/podcast-manager/.git

# Fix file permissions
sudo chmod -R 755 /opt/podcast-manager
```

### Clean Build (Nuclear Option)

```bash
# Backup .env and database
sudo cp /opt/podcast-manager/.env /tmp/
sudo cp /opt/podcast-manager/podcast_manager.db /tmp/

# Remove and re-clone
sudo rm -rf /opt/podcast-manager
sudo git clone https://github.com/YOUR_USERNAME/podcast-manager.git /opt/podcast-manager

# Restore .env and database
sudo mv /tmp/.env /opt/podcast-manager/
sudo mv /tmp/podcast_manager.db /opt/podcast-manager/

# Re-run install
cd /opt/podcast-manager
sudo bash install-rocky-linux.sh
```
