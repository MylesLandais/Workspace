# Quick Start Guide - Full YouTube Feed Features

This guide helps you get started with enhanced YouTube features in minutes.

## Prerequisites

Ensure you have:
- Neo4j database running (docker-compose.yml)
- Python 3.10+ with yt-dlp installed
- Project dependencies (requirements.txt)

## Step 1: Initialize Database Schema

```bash
python3 init_youtube_schema.py
```

Expected output:
```
Initializing Neo4j schema for enhanced YouTube features...
Creating constraints...
  ✓ CREATE CONSTRAINT video_id_unique IF NOT EXISTS...
  ✓ CREATE CONSTRAINT comment_id_unique IF NOT EXISTS...
Creating indexes...
  ✓ CREATE INDEX video_published_at IF NOT EXISTS...
Creating fulltext indexes...
  ✓ CREATE FULLTEXT INDEX video_title_ft IF NOT EXISTS...
✓ Schema initialization complete!
```

## Step 2: Initialize Schema in Neo4j

```bash
docker exec n4j.jupyter.dev.local cypher-shell -u neo4j -p password -f src/feed/schema/youtube_schema.cypher
```

## Step 3: Fetch a Video with All Features

```bash
# Test with a sample video
python3 test_youtube_enhanced.py https://www.youtube.com/watch?v=VIDEO_ID --creator developer
```

Expected output:
```
Testing enhanced YouTube features for: https://www.youtube.com/watch?v=VIDEO_ID

Step 1: Fetching video metadata...
✓ Fetched video: Video Title
  - Duration: 600s
  - Views: 10000
  - Likes: 500
  - Comments: 50

Step 2: Checking features...
✓ Description: Yes (1500 chars)
✓ Chapters: 5 chapters
✓ Comments: 50 comments
✓ Transcript: Yes (120 segments)
✓ Tags: 10 tags
✓ Categories: ['Education']

Step 3: Storing in database...
  Storing 5 chapters...
  Storing 50 comments...
  Storing transcript with 120 segments...
✓ Stored video VIDEO_ID with all features

Step 4: Verifying data in database...
✓ Video found in database:
  - Title: Video Title
  - Description: 1500 chars
  - Views: 10000
  - Likes: 500
✓ Chapters: 5 stored
✓ Comments: 50 stored
✓ Transcript segments: 120 stored

✓ All tests passed!

✓ Test completed successfully!
You can now query the video via API:
  http://localhost:8001/api/videos/VIDEO_ID
```

## Step 4: Start API Server

```bash
# Terminal 1
cd media-platform
python3 youtube_enhanced_api.py
```

Or with uvicorn:
```bash
uvicorn youtube_enhanced_api:app --host 0.0.0.0 --port 8001
```

## Step 5: Query the API

### Get Full Video with All Features

```bash
curl http://localhost:8001/api/videos/VIDEO_ID
```

### Get Comments (Sorted by Top)

```bash
curl "http://localhost:8001/api/videos/VIDEO_ID/comments?sort_by=top&limit=20"
```

### Get Comments (Sorted by Newest)

```bash
curl "http://localhost:8001/api/videos/VIDEO_ID/comments?sort_by=new&limit=20"
```

### Get Transcript

```bash
curl http://localhost:8001/api/videos/VIDEO_ID/transcript
```

### Get Chapter Markers

```bash
curl http://localhost:8001/api/videos/VIDEO_ID/chapters
```

### Get Description

```bash
curl http://localhost:8001/api/videos/VIDEO_ID/description
```

### Search Videos

```bash
curl "http://localhost:8001/api/search/videos?q=python+tutorial&limit=20"
```

### Search Comments

```bash
curl "http://localhost:8001/api/search/comments?q=helpful&limit=20"
```

## Step 6: Start Polling Worker (Optional)

If you want to automatically monitor channels:

```bash
# Terminal 2
python3 media-platform/youtube_polling_worker.py --interval 60
```

Or run once:
```bash
python3 media-platform/youtube_polling_worker.py --once
```

## Step 7: Fetch Developer Channel Videos

Now that the developer creator has the YouTube channel attached:

```bash
# Create a script to fetch all videos from the channel
cat > fetch_developer_videos.py << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.services.youtube_enhanced_service import YouTubeEnhancedService
from feed.storage.neo4j_connection import get_connection

# Get developer's YouTube channel URL
neo4j = get_connection()
query = """
MATCH (c:Creator {slug: 'developer'})-[:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform {slug: 'youtube'})
RETURN h.profile_url as url, h.username as handle
"""
result = neo4j.execute_read(query)

if not result:
    print("Developer YouTube handle not found")
    sys.exit(1)

channel_url = result[0]["url"]
handle = result[0]["handle"]
print(f"Fetching videos for: {handle}")

service = YouTubeEnhancedService()

# Fetch channel videos
import subprocess
import json

cmd = ["yt-dlp", "--dump-json", "--no-warnings", "--quiet", "--flat-playlist", channel_url]
result = subprocess.run(cmd, capture_output=True, text=True, check=True)

videos = []
for line in result.stdout.strip().split('\n'):
    if line:
        videos.append(json.loads(line))

print(f"Found {len(videos)} videos")

# Process each video
for i, video in enumerate(videos[:10]):  # Limit to first 10 for testing
    video_url = video.get("webpage_url")
    video_id = video.get("id")
    
    print(f"Processing {i+1}/{len(videos)}: {video.get('title')}")
    
    try:
        metadata = service.fetch_video_metadata(video_url)
        if metadata:
            service.store_video_with_all_features(metadata, creator_slug="developer")
            print(f"  ✓ Stored")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print(f"\n✓ Processed {len(videos)} videos")
EOF

python3 fetch_developer_videos.py
```

## Docker Deployment

Add to your docker-compose.yml:

```yaml
services:
  youtube-enhanced-api:
    build: .
    container_name: yt-api.jupyter.dev.local
    ports:
      - "8001:8001"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USERNAME=neo4j
      - NEO4J_PASSWORD=localpassword
    depends_on:
      - neo4j
    restart: unless-stopped

  youtube-polling-worker:
    build: .
    container_name: yt-worker.jupyter.dev.local
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USERNAME=neo4j
      - NEO4J_PASSWORD=localpassword
      - POLL_INTERVAL_MINUTES=60
    depends_on:
      - neo4j
    restart: unless-stopped
    command: python3 -m media-platform.youtube_polling_worker
```

Deploy:
```bash
docker-compose -f docker-compose.youtube.yml up -d
```

## Common Issues

### yt-dlp not found

```bash
# Install yt-dlp
pip install yt-dlp

# Or use nix-shell
nix-shell -p python3 yt-dlp --run "python3 your_script.py"
```

### Database connection failed

Check Neo4j is running:
```bash
docker ps | grep neo4j
```

Check connection:
```bash
docker exec n4j.jupyter.dev.local cypher-shell -u neo4j -p password "RETURN 'ok'"
```

### Transcript not available

Some videos don't have auto-captions:
- Verify video has captions enabled on YouTube
- Try manual captions with `--write-subtitles`

### Comments disabled

If comments are disabled on the video:
- The API will return empty comment array
- Check video permissions on YouTube

## Next Steps

1. **Fetch more videos**: Process multiple videos from developer channel
2. **Monitor channels**: Start polling worker for continuous updates
3. **Build UI**: Create frontend to display videos, comments, transcripts
4. **Add search**: Implement fulltext search frontend
5. **Analytics**: Create dashboards for comment analysis

## Documentation

For detailed documentation, see [YOUTUBE_FEEDS_GUIDE.md](YOUTUBE_FEEDS_GUIDE.md).

## Support

For issues or questions:
- Check logs in docker containers
- Review Neo4j browser: http://localhost:7474
- Test API endpoints individually
- Check yt-dlp version: `yt-dlp --version`
