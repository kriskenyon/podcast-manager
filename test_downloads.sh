#!/bin/bash
# Test script for Download functionality

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Testing Podcast Download Functionality"
echo "=========================================="
echo ""

# Add a podcast first
echo "1. Adding a test podcast..."
PODCAST_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/podcasts" \
  -H "Content-Type: application/json" \
  -d '{
    "rss_url": "https://feeds.simplecast.com/54nAGcIl",
    "max_episodes_to_keep": 2,
    "auto_download": false
  }')

PODCAST_ID=$(echo "$PODCAST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")
echo "Podcast ID: $PODCAST_ID"
echo ""

# Get episodes
echo "2. Getting episodes for podcast..."
EPISODES_RESPONSE=$(curl -s "${BASE_URL}/api/podcasts/${PODCAST_ID}/episodes")
echo "$EPISODES_RESPONSE" | python3 -m json.tool | head -30
EPISODE_ID=$(echo "$EPISODES_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['episodes'][0]['id'] if data.get('episodes') else '')")
echo ""
echo "First Episode ID: $EPISODE_ID"
echo ""

if [ ! -z "$EPISODE_ID" ]; then
  # Queue download
  echo "3. Queuing episode for download..."
  DOWNLOAD_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/episodes/${EPISODE_ID}/download")
  echo "$DOWNLOAD_RESPONSE" | python3 -m json.tool
  DOWNLOAD_ID=$(echo "$DOWNLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")
  echo ""
  echo "Download ID: $DOWNLOAD_ID"
  echo ""

  # List downloads
  echo "4. Listing all downloads..."
  curl -s "${BASE_URL}/api/downloads" | python3 -m json.tool
  echo ""
  echo ""

  # Process download queue
  echo "5. Processing download queue..."
  curl -s -X POST "${BASE_URL}/api/downloads/process-queue" | python3 -m json.tool
  echo ""
  echo ""

  # Check download status
  echo "6. Checking download status..."
  for i in {1..5}; do
    echo "  Check $i:"
    curl -s "${BASE_URL}/api/downloads/${DOWNLOAD_ID}" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"    Status: {data.get('status')}, Progress: {data.get('progress', 0)*100:.1f}%\")"
    sleep 2
  done
  echo ""
  echo ""

  # List downloads by status
  echo "7. Listing completed downloads..."
  curl -s "${BASE_URL}/api/downloads?status=completed" | python3 -m json.tool
  echo ""
  echo ""

  echo "8. Listing failed downloads..."
  curl -s "${BASE_URL}/api/downloads?status=failed" | python3 -m json.tool
  echo ""
  echo ""
fi

echo "=========================================="
echo "Download Testing Complete!"
echo "=========================================="
echo ""
echo "Check the downloads directory for your downloaded episodes:"
echo "  ls -lh downloads/"
echo ""
echo "View detailed API docs at:"
echo "  ${BASE_URL}/docs"
echo ""
