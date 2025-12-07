#!/bin/bash
# Test script for Podcast Manager API

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Testing Podcast Manager API"
echo "=========================================="
echo ""

# Test health check
echo "1. Testing health check..."
curl -s "${BASE_URL}/api/health" | python3 -m json.tool
echo ""
echo ""

# Add a podcast
echo "2. Adding a test podcast (The Daily from NY Times)..."
PODCAST_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/podcasts" \
  -H "Content-Type: application/json" \
  -d '{
    "rss_url": "https://feeds.simplecast.com/54nAGcIl",
    "max_episodes_to_keep": 3,
    "auto_download": false
  }')

echo "$PODCAST_RESPONSE" | python3 -m json.tool
PODCAST_ID=$(echo "$PODCAST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")
echo ""
echo "Podcast ID: $PODCAST_ID"
echo ""
echo ""

# List all podcasts
echo "3. Listing all podcasts..."
curl -s "${BASE_URL}/api/podcasts" | python3 -m json.tool
echo ""
echo ""

# Get podcast details
if [ ! -z "$PODCAST_ID" ]; then
  echo "4. Getting podcast details for ID $PODCAST_ID..."
  curl -s "${BASE_URL}/api/podcasts/${PODCAST_ID}" | python3 -m json.tool
  echo ""
  echo ""

  # List episodes for podcast
  echo "5. Listing episodes for podcast ID $PODCAST_ID..."
  curl -s "${BASE_URL}/api/podcasts/${PODCAST_ID}/episodes" | python3 -m json.tool
  echo ""
  echo ""

  # Get podcast with episodes
  echo "6. Getting podcast with all episodes..."
  curl -s "${BASE_URL}/api/podcasts/${PODCAST_ID}/with-episodes" | python3 -m json.tool
  echo ""
  echo ""
fi

echo "=========================================="
echo "API Testing Complete!"
echo "=========================================="
echo ""
echo "To view API documentation, visit:"
echo "  ${BASE_URL}/docs"
echo ""
