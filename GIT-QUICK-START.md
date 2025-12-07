# Git Deployment - Quick Start

## 1. Initialize Git Repository (Now)

```bash
# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Podcast Manager for Plex"
```

## 2. Push to GitHub (Recommended)

### Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `podcast-manager`
3. Description: "Podcast Manager for Plex Media Server"
4. **Don't** initialize with README
5. Click "Create repository"

### Push Code

```bash
# Add GitHub as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/podcast-manager.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 3. Deploy to Rocky Linux Server

### First Time Setup

```bash
# SSH to your server
ssh user@your-rocky-server

# Clone repository
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/podcast-manager.git

# Set ownership
sudo chown -R podcastmgr:podcastmgr /opt/podcast-manager

# Run installer
cd /opt/podcast-manager
sudo bash install-rocky-linux.sh
```

### Future Updates (Easy!)

```bash
# SSH to server
ssh user@your-rocky-server

# Run update script
cd /opt/podcast-manager
sudo ./update.sh
```

That's it! The update script will:
- ✅ Backup database
- ✅ Pull latest code
- ✅ Update dependencies
- ✅ Rebuild frontend
- ✅ Restart services

## Daily Workflow

### On Your Mac/PC

```bash
# Make changes
vim src/podcastmanager/...

# Commit and push
git add .
git commit -m "Fix: whatever you fixed"
git push
```

### On Rocky Linux Server

```bash
ssh user@server
cd /opt/podcast-manager
sudo ./update.sh
```

Done! Updates deployed in seconds.

## Full Documentation

See `GIT-DEPLOYMENT-GUIDE.md` for:
- Branching strategies
- Rollback procedures
- Troubleshooting
- Advanced workflows
