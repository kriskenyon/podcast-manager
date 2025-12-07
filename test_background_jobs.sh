#!/bin/bash
# Test script for Background Jobs functionality

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Testing Background Jobs"
echo "=========================================="
echo ""

# List all scheduled jobs
echo "1. Listing all scheduled jobs..."
curl -s "${BASE_URL}/api/jobs" | python3 -m json.tool
echo ""
echo ""

# Add a podcast for testing
echo "2. Adding a test podcast..."
PODCAST_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/podcasts" \
  -H "Content-Type: application/json" \
  -d '{
    "rss_url": "https://feeds.simplecast.com/54nAGcIl",
    "max_episodes_to_keep": 2,
    "auto_download": true
  }')
PODCAST_ID=$(echo "$PODCAST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")
echo "Podcast ID: $PODCAST_ID"
echo ""
echo ""

# Manually trigger feed refresh job
echo "3. Triggering feed refresh job manually..."
curl -s -X POST "${BASE_URL}/api/jobs/refresh_podcasts/trigger" | python3 -m json.tool
echo ""
echo "Waiting for job to complete..."
sleep 5
echo ""

# Check for new episodes and downloads
echo "4. Checking episodes for the podcast..."
curl -s "${BASE_URL}/api/podcasts/${PODCAST_ID}/episodes" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Found {data.get('total', 0)} episodes\")"
echo ""
echo ""

echo "5. Checking queued downloads..."
curl -s "${BASE_URL}/api/downloads?status=pending" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Pending downloads: {data.get('total', 0)}\")"
echo ""
echo ""

# Trigger download processor
echo "6. Triggering download processor job..."
curl -s -X POST "${BASE_URL}/api/jobs/process_downloads/trigger" | python3 -m json.tool
echo ""
echo "Waiting for downloads to process..."
sleep 10
echo ""

# Check download status
echo "7. Checking completed downloads..."
curl -s "${BASE_URL}/api/downloads?status=completed" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Completed downloads: {data.get('total', 0)}\")"
echo ""
echo ""

# View job status
echo "8. Viewing job schedule and next run times..."
curl -s "${BASE_URL}/api/jobs" | python3 -m json.tool
echo ""
echo ""

# Pause a job
echo "9. Pausing cleanup job..."
curl -s -X POST "${BASE_URL}/api/jobs/cleanup_episodes/pause" | python3 -m json.tool
echo ""
echo ""

# Resume a job
echo "10. Resuming cleanup job..."
curl -s -X POST "${BASE_URL}/api/jobs/cleanup_episodes/resume" | python3 -m json.tool
echo ""
echo ""

echo "=========================================="
echo "Background Jobs Testing Complete!"
echo "=========================================="
echo ""
echo "Jobs are now running automatically:"
echo "  - Feed refresh: Every ${FEED_REFRESH_INTERVAL:-3600} seconds"
echo "  - Download processor: Every 300 seconds (5 minutes)"
echo "  - Cleanup: Every ${CLEANUP_INTERVAL:-86400} seconds (24 hours)"
echo ""
echo "Monitor logs to see background jobs running:"
echo "  tail -f logs/podcast_manager.log"
echo ""
echo "View API docs:"
echo "  ${BASE_URL}/docs"
echo ""
