#!/bin/bash
set -e

# Podcast Manager Installation Script for Rocky Linux
# This script sets up the podcast manager as systemd services

echo "=========================================="
echo "Podcast Manager - Rocky Linux Installation"
echo "=========================================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Configuration
INSTALL_DIR="/opt/podcast-manager"
SERVICE_USER="podcastmgr"
SERVICE_GROUP="podcastmgr"
DOWNLOAD_DIR="/mnt/media/podcasts"

echo "Configuration:"
echo "  Install Directory: $INSTALL_DIR"
echo "  Service User: $SERVICE_USER"
echo "  Downloads: $DOWNLOAD_DIR"
echo

read -p "Continue with installation? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Step 1: Install system dependencies
echo "Step 1: Installing system dependencies..."
dnf install -y python39 python39-pip python39-devel gcc sqlite nginx nodejs npm git

# Step 2: Create service user
echo "Step 2: Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d $INSTALL_DIR -m $SERVICE_USER
    echo "Created user: $SERVICE_USER"
else
    echo "User $SERVICE_USER already exists"
fi

# Step 3: Create directories
echo "Step 3: Creating directories..."
mkdir -p $INSTALL_DIR
mkdir -p $DOWNLOAD_DIR
mkdir -p $INSTALL_DIR/logs

# Step 4: Copy application files
echo "Step 4: Copying application files..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Copy all files except git, cache, etc
rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='node_modules' --exclude='venv' --exclude='.env' \
    $SCRIPT_DIR/ $INSTALL_DIR/

# Step 5: Set up Python virtual environment
echo "Step 5: Setting up Python virtual environment..."
cd $INSTALL_DIR
python3.9 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Step 6: Set up frontend
echo "Step 6: Setting up frontend..."
cd $INSTALL_DIR/frontend
npm install

# For production, build the frontend
read -p "Build frontend for production? (recommended) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm run build
    echo "Frontend built to dist/"
fi

# Step 7: Create .env file if it doesn't exist
echo "Step 7: Configuring environment..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp $INSTALL_DIR/.env.example $INSTALL_DIR/.env

    # Update paths in .env
    sed -i "s|DOWNLOAD_BASE_PATH=.*|DOWNLOAD_BASE_PATH=$DOWNLOAD_DIR|" $INSTALL_DIR/.env

    echo "Created .env file. Please edit $INSTALL_DIR/.env with your settings."
    echo "Especially set:"
    echo "  - PLEX_TOKEN (if using Plex integration)"
    echo "  - PLEX_URL"
else
    echo ".env file already exists"
fi

# Step 8: Initialize database
echo "Step 8: Initializing database..."
cd $INSTALL_DIR
source venv/bin/activate
python3 -c "from podcastmanager.db.database import init_db; import asyncio; asyncio.run(init_db())"

# Step 9: Set permissions
echo "Step 9: Setting permissions..."
chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR
chown -R $SERVICE_USER:$SERVICE_GROUP $DOWNLOAD_DIR
chmod 755 $INSTALL_DIR
chmod 775 $DOWNLOAD_DIR

# Step 10: Install systemd services
echo "Step 10: Installing systemd services..."

# Backend service
cp $INSTALL_DIR/podcast-manager-backend.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable podcast-manager-backend.service

# Step 11: Configure firewall
echo "Step 11: Configuring firewall..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-port=8000/tcp
    firewall-cmd --reload
    echo "Firewall configured"
fi

# Step 12: Set up nginx (optional)
echo
read -p "Configure nginx to serve the frontend? (recommended for production) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Install nginx config
    cp $INSTALL_DIR/nginx-podcast-manager.conf /etc/nginx/conf.d/

    # Test nginx config
    nginx -t

    # Enable and start nginx
    systemctl enable nginx
    systemctl restart nginx

    echo "Nginx configured"
    echo "Edit /etc/nginx/conf.d/podcast-manager.conf to set your server_name"
else
    # Install dev frontend service if not using nginx
    cp $INSTALL_DIR/podcast-manager-frontend-dev.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable podcast-manager-frontend-dev.service
fi

echo
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo
echo "Next steps:"
echo
echo "1. Edit configuration:"
echo "   sudo nano $INSTALL_DIR/.env"
echo
echo "2. Start services:"
echo "   sudo systemctl start podcast-manager-backend"
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "   sudo systemctl start podcast-manager-frontend-dev"
fi
echo
echo "3. Check status:"
echo "   sudo systemctl status podcast-manager-backend"
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "   sudo systemctl status podcast-manager-frontend-dev"
fi
echo
echo "4. View logs:"
echo "   sudo journalctl -u podcast-manager-backend -f"
echo
echo "5. Access the application:"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   http://your-server-ip/"
else
    echo "   http://your-server-ip:5173/"
fi
echo "   API: http://your-server-ip:8000/docs"
echo
echo "Useful commands:"
echo "  sudo systemctl stop podcast-manager-backend"
echo "  sudo systemctl restart podcast-manager-backend"
echo "  sudo systemctl status podcast-manager-backend"
echo
