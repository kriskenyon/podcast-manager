# Plex Integration Setup Guide

## Quick Start

The Plex integration allows the podcast manager to check if episodes have been played before deleting them, ensuring you never lose unlistened episodes.

## Step 1: Get Your Plex Token

### Method 1: Via Plex Web App (Easiest)
1. Open Plex Web App in your browser
2. Play any media item
3. Click the three dots `...` → **"Get Info"**
4. Click **"View XML"**
5. In the URL bar, look for `X-Plex-Token=XXXXX`
6. Copy everything after the `=` sign

### Method 2: Via Plex Settings
1. Open Plex Web App
2. Go to Settings → Account
3. At the bottom of the page, you'll see your **Plex Token**

### Method 3: Using curl
```bash
curl -u username:password https://plex.tv/users/sign_in.xml -X POST
```
Look for `<authentication-token>` in the response.

## Step 2: Configure Podcast Manager

1. **Edit your `.env` file:**

```bash
# Enable Plex Integration
PLEX_ENABLED=true

# Your Plex server URL (usually http://localhost:32400 for local)
PLEX_URL=http://localhost:32400

# The token you got from Step 1
PLEX_TOKEN=your-actual-token-here

# Name of your Plex library that contains podcasts
PLEX_LIBRARY=Podcasts
```

2. **Save the file and restart the podcast manager:**

```bash
# Stop the server (Ctrl+C)
./run.sh serve
```

## Step 3: Set Up Plex Library (if not already done)

1. Open Plex Web App
2. Click **"+"** next to Libraries
3. Select **"Music"** library type
4. Name it **"Podcasts"** (or whatever you set in `PLEX_LIBRARY`)
5. Add the folder path that matches your `DOWNLOAD_BASE_PATH`
   - Example: `/mnt/media/podcasts` or `/Volumes/webroot/play/pd/downloads`
6. Click **"Add Library"**

## Step 4: Test the Connection

The podcast manager will test the Plex connection when it starts. Check the logs:

```bash
# You should see:
# "Connected to Plex: [Your Server Name]"
# "Found Plex library: Podcasts"
# "Plex integration enabled - will check play status before cleanup"
```

## How It Works

### Without Plex Integration (Standard Mode)
- Keeps only the 3 most recent episodes
- Deletes anything older automatically

### With Plex Integration (Smart Mode)
- **Always keeps** the 3 most recent episodes
- **For older episodes:**
  - ✅ If played in Plex → Deletes (frees up space)
  - ❌ If not played in Plex → Keeps (you haven't listened yet!)

## Example Scenario

Let's say you have a podcast set to keep 3 episodes:

### Episodes Downloaded:
1. Episode 100 (Dec 4) - Most recent
2. Episode 99 (Nov 28) - Second recent
3. Episode 98 (Nov 20) - Third recent
4. Episode 97 (Nov 13) - Old
5. Episode 96 (Nov 6) - Old

### Cleanup Behavior:

**Without Plex:**
- Keeps: 100, 99, 98
- Deletes: 97, 96

**With Plex (if episode 96 is unplayed):**
- Keeps: 100, 99, 98, 96 (unplayed!)
- Deletes: 97 (played)

## Troubleshooting

### "Failed to connect to Plex"

**Check:**
1. Plex server is running
2. `PLEX_URL` is correct (try `http://localhost:32400` or your server's IP)
3. `PLEX_TOKEN` is valid and has no extra spaces
4. Your firewall isn't blocking the connection

**Test manually:**
```bash
curl -H "X-Plex-Token: YOUR_TOKEN" http://localhost:32400/library/sections
```
You should see your libraries listed.

### "Library 'Podcasts' not found"

**Check:**
1. Library name exactly matches (case-sensitive!)
2. The library exists in Plex
3. Try checking what libraries are available:

```bash
curl -H "X-Plex-Token: YOUR_TOKEN" http://localhost:32400/library/sections | grep title
```

### "Episode not found in Plex"

This is normal! It means:
- The episode file hasn't been scanned by Plex yet
- The filename doesn't match what Plex has indexed
- The episode will be kept (safe default behavior)

**Force Plex to scan:**
1. Go to your Podcasts library in Plex
2. Click the three dots `...`
3. Select **"Scan Library Files"**

## Advanced Configuration

### Multiple Plex Servers
Currently, only one Plex server is supported. If you need multiple servers, the cleanup job will use the first configured server.

### Custom Library Names
You can use any library name, just make sure it matches:
```bash
PLEX_LIBRARY=My Podcast Collection
```

### Disable Temporarily
Set `PLEX_ENABLED=false` in `.env` to temporarily disable without removing your token.

## Benefits

✅ **Never lose unlistened episodes** - Smart cleanup based on actual listening
✅ **Automatic space management** - Deletes episodes after you've listened
✅ **Respects your habits** - Works with how you actually use Plex
✅ **Backward compatible** - Works perfectly without Plex too
✅ **No manual cleanup** - Set it and forget it

## Security Note

Your Plex token is like a password. Keep it secure:
- Don't commit `.env` to version control
- Use restrictive file permissions: `chmod 600 .env`
- Regenerate the token if it's ever compromised

## Need Help?

Check the main documentation or open an issue on GitHub.
