#!/bin/bash
# Automated update script for Podcast Manager
#
# This script pulls the latest code from git and updates the application
# Usage: sudo ./update.sh

set -e  # Exit on error

echo "================================================"
echo "Podcast Manager - Update Script"
echo "================================================"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: Please run as root (sudo)"
    exit 1
fi

# Navigate to app directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if git repository
if [ ! -d ".git" ]; then
    echo "Error: Not a git repository. Please clone from git first."
    exit 1
fi

# Backup database
echo "1. Backing up database..."
if [ -f "podcast_manager.db" ]; then
    BACKUP_FILE="podcast_manager.db.backup-$(date +%Y%m%d-%H%M%S)"
    cp podcast_manager.db "$BACKUP_FILE"
    echo "   Database backed up to: $BACKUP_FILE"
else
    echo "   No database found to backup"
fi

# Show current version
echo
echo "2. Current version:"
git log -1 --oneline
echo

# Pull latest changes
echo "3. Pulling latest changes from git..."
sudo -u podcastmgr git fetch origin
BEFORE=$(git rev-parse HEAD)
sudo -u podcastmgr git pull origin main
AFTER=$(git rev-parse HEAD)

if [ "$BEFORE" = "$AFTER" ]; then
    echo "   Already up to date!"
    echo
    read -p "Continue with dependency update anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Update cancelled."
        exit 0
    fi
fi

# Update Python dependencies
echo
echo "4. Updating Python dependencies..."
if [ -f "requirements.txt" ]; then
    sudo -u podcastmgr bash -c "source venv/bin/activate && pip install -r requirements.txt --quiet"
    echo "   Python dependencies updated"
else
    echo "   No requirements.txt found, skipping"
fi

# Update frontend dependencies and build
echo
echo "5. Updating frontend..."
if [ -d "frontend" ]; then
    cd frontend

    if [ -f "package.json" ]; then
        echo "   Installing npm packages..."
        sudo -u podcastmgr npm install --silent

        echo "   Building frontend for production..."
        sudo -u podcastmgr npm run build
        echo "   Frontend built successfully"
    fi

    cd ..
else
    echo "   No frontend directory found, skipping"
fi

# Restart backend service
echo
echo "6. Restarting services..."
if systemctl is-active --quiet podcast-manager-backend; then
    echo "   Restarting backend service..."
    systemctl restart podcast-manager-backend

    # Wait a moment for service to start
    sleep 2

    if systemctl is-active --quiet podcast-manager-backend; then
        echo "   ✅ Backend service restarted successfully"
    else
        echo "   ❌ Backend service failed to start!"
        echo "   Check logs: sudo journalctl -u podcast-manager-backend -n 50"
        exit 1
    fi
else
    echo "   Backend service not running, skipping restart"
fi

# Restart nginx if it's running
if systemctl is-active --quiet nginx; then
    echo "   Restarting nginx..."
    systemctl restart nginx
    echo "   ✅ Nginx restarted"
fi

# Restart frontend dev service if it's running
if systemctl is-active --quiet podcast-manager-frontend-dev; then
    echo "   Restarting frontend dev service..."
    systemctl restart podcast-manager-frontend-dev
    echo "   ✅ Frontend dev service restarted"
fi

echo
echo "================================================"
echo "✅ Update Complete!"
echo "================================================"
echo
echo "Updated to:"
git log -1 --oneline
echo
echo "Services status:"
systemctl status podcast-manager-backend --no-pager -l | head -5
echo
echo "To view logs:"
echo "  sudo journalctl -u podcast-manager-backend -f"
echo
echo "To rollback if needed:"
echo "  sudo -u podcastmgr git reset --hard $BEFORE"
echo "  sudo systemctl restart podcast-manager-backend"
echo
