# Full YouTube Feed Features

This document describes the complete YouTube feed system with enhanced features.

## Architecture

### Core Components

1. **Neo4j Database Schema**
   - `YouTubeVideo` nodes with metadata (title, description, stats, tags)
   - `YouTubeComment` nodes with full comment data
   - `YouTubeChapter` nodes for chapter markers
   - `YouTubeTranscript` nodes for transcript segments
   - Fulltext indexes for search

2. **YouTubeEnhancedService** (`src/feed/services/youtube_enhanced_service.py`)
   - Fetches video metadata using yt-dlp
   - Extracts chapters from metadata or description
   - Fetches comments with engagement data
   - Stores all data in Neo4j with proper relationships

3. **YouTubeEnhancedAPI** (`media-platform/youtube_enhanced_api.py`)
   - REST API for querying YouTube data
   - Endpoints for videos, comments, transcripts, chapters
   - Fulltext search across videos and comments

4. **YouTubePollingWorker** (`media-platform/youtube_polling_worker.py`)
   - Monitors subscribed channels
   - Fetches new videos automatically
   - Updates subscription status and statistics

## Features

### 1. Full Comment Index

**Schema:**
```
YouTubeVideo -[:HAS_COMMENT]-> YouTubeComment
```

**Properties:**
- `comment_id`: Unique identifier
- `text`: Comment text content
- `author`: Author name
- `author_id`: Author identifier
- `like_count`: Number of likes
- `reply_count`: Number of replies
- `is_reply`: Whether this is a reply
- `parent_id`: Parent comment ID (if reply)
- `timestamp`: When comment was posted

**API Endpoints:**
- `GET /api/videos/{video_id}/comments` - Get all comments for a video
- `GET /api/search/comments?q=query` - Search comments by text

### 2. Upload Description

**Schema:**
```
YouTubeVideo.description property
```

**Properties:**
- `description`: Full video description
- Stored as property on YouTubeVideo node

**API Endpoints:**
- `GET /api/videos/{video_id}/description` - Get full description

### 3. Transcript

**Schema:**
```
YouTubeVideo -[:HAS_TRANSCRIPT_SEGMENT]-> YouTubeTranscript
```

**Properties:**
- `start_time`: Segment start time (seconds)
- `end_time`: Segment end time (seconds)
- `text`: Transcript text

**API Endpoints:**
- `GET /api/videos/{video_id}/transcript` - Get full transcript

**Note:** Transcripts are fetched from auto-generated captions using yt-dlp's `--write-auto-sub` flag.

### 4. Chapter Markers

**Schema:**
```
YouTubeVideo -[:HAS_CHAPTER]-> YouTubeChapter
```

**Properties:**
- `index`: Chapter index (0, 1, 2, ...)
- `title`: Chapter title
- `start_time`: Start time (seconds)
- `end_time`: End time (seconds)
- `timestamp`: Formatted timestamp (e.g., "00:00", "05:30")

**API Endpoints:**
- `GET /api/videos/{video_id}/chapters` - Get all chapter markers

**Chapter Sources:**
1. YouTube's native chapters (if available)
2. Parsed from video description using timestamp patterns:
   - `0:00 Intro`
   - `0:00 - Intro`
   - `00:00 Intro`

### 5. Related/Recommended Videos

**Schema:**
```
YouTubeVideo -[:RELATED_TO]-> YouTubeVideo
```

**Note:** This feature is partially implemented. Full related video support would require:
- YouTube Data API integration (for accurate recommendations)
- Storing relationship between videos
- Caching related video metadata

## API Usage Examples

### Get Full Video with All Features

```bash
curl http://localhost:8001/api/videos/VIDEO_ID
```

**Response:**
```json
{
  "video": {
    "video_id": "abc123",
    "title": "Video Title",
    "description": "Full description...",
    "duration": 600,
    "view_count": 10000,
    "like_count": 500,
    "comment_count": 50,
    "published_at": "2026-01-09T00:00:00Z",
    "thumbnail_url": "https://...",
    "channel_id": "UC...",
    "channel_name": "Channel Name",
    "tags": ["tag1", "tag2"],
    "categories": ["Education"]
  },
  "chapters": [
    {
      "index": 0,
      "title": "Intro",
      "start_time": 0,
      "end_time": 30,
      "timestamp": "00:00"
    }
  ],
  "transcript": [
    {
      "start": 0,
      "end": 5,
      "text": "Hello, welcome to the video..."
    }
  ],
  "comments": [
    {
      "comment_id": "comment1",
      "text": "Great video!",
      "author": "User",
      "like_count": 10,
      "reply_count": 2,
      "is_reply": false,
      "parent_id": "",
      "timestamp": "2026-01-09T01:00:00Z"
    }
  ]
}
```

### Get Comments (Sorted)

```bash
# Top comments (by likes)
curl "http://localhost:8001/api/videos/VIDEO_ID/comments?sort_by=top&limit=20"

# Newest comments
curl "http://localhost:8001/api/videos/VIDEO_ID/comments?sort_by=new&limit=20"

# Most replied
curl "http://localhost:8001/api/videos/VIDEO_ID/comments?sort_by=replies&limit=20"
```

### Search Videos

```bash
curl "http://localhost:8001/api/search/videos?q=python+tutorial&limit=20"
```

### Search Comments

```bash
curl "http://localhost:8001/api/search/comments?q=helpful&limit=20"
```

## Database Schema

### Node Labels

- **YouTubeVideo**: Main video node
- **YouTubeComment**: Comment node
- **YouTubeChapter**: Chapter marker node
- **YouTubeTranscript**: Transcript segment node

### Relationship Types

- **HAS_COMMENT**: Video → Comment
- **HAS_CHAPTER**: Video → Chapter
- **HAS_TRANSCRIPT_SEGMENT**: Video → Transcript
- **RELATED_TO**: Video → Video (for recommendations)

### Constraints

- `video_id`: Unique on YouTubeVideo
- `comment_id`: Unique on YouTubeComment
- `uuid`: Unique on YouTubeVideo, YouTubeComment, YouTubeChapter, YouTubeTranscript

### Indexes

- `published_at`: On YouTubeVideo for chronological queries
- `channel_id`: On YouTubeVideo for channel queries
- `timestamp`: On YouTubeComment for sorting
- `start_time`: On YouTubeChapter and YouTubeTranscript for time-based queries
- Fulltext on `video_title_ft` (title, description)
- Fulltext on `comment_text_ft` (text)

## Setup Instructions

### 1. Initialize Database Schema

```bash
python3 init_youtube_schema.py
```

### 2. Fetch and Store Video Data

```bash
# Fetch a single video with all features
python3 -m src.feed.services.youtube_enhanced_service VIDEO_URL --creator developer

# Or use the enhanced service directly
python3 -c "
from src.feed.services.youtube_enhanced_service import YouTubeEnhancedService
service = YouTubeEnhancedService()
data = service.fetch_video_metadata('https://www.youtube.com/watch?v=VIDEO_ID')
service.store_video_with_all_features(data)
"
```

### 3. Start API Server

```bash
cd media-platform
uvicorn youtube_enhanced_api:app --host 0.0.0.0 --port 8001
```

### 4. Start Polling Worker

```bash
# Run once
python3 media-platform/youtube_polling_worker.py --once

# Run continuous polling (60 minute interval)
python3 media-platform/youtube_polling_worker.py --interval 60
```

## Integration with Existing System

The YouTube enhanced system integrates with your existing Creator/Handle/Media ontology:

```
Creator -[:OWNS_HANDLE]-> Handle -[:ON_PLATFORM]-> Platform (youtube)
         ↓
    [:PUBLISHED]-> YouTubeVideo
                        ↓
                    [:HAS_COMMENT]-> YouTubeComment
                    [:HAS_CHAPTER]-> YouTubeChapter
                    [:HAS_TRANSCRIPT_SEGMENT]-> YouTubeTranscript
```

### Linking Videos to Creators

When fetching a video, you can specify a creator slug to link it:

```python
service.store_video_with_all_features(
    video_data,
    creator_slug="developer"
)
```

This creates a `PUBLISHED` relationship from the Creator's YouTube Handle to the Video.

## Monitoring Channels

The polling worker monitors all channels with active `SUBSCRIBED_TO` relationships:

1. Checks `last_polled_at` for each channel
2. Fetches videos uploaded since last poll
3. Processes new videos with full features
4. Updates poll status and statistics

**Configuration:**
- Poll interval: Configurable (default: 60 minutes)
- Subscription status: `active` channels only
- Error tracking: `error_count_24h` for health monitoring

## Data Storage

All YouTube data is stored in Neo4j:
- Video metadata: `YouTubeVideo` nodes
- Comments: `YouTubeComment` nodes
- Chapters: `YouTubeChapter` nodes
- Transcripts: `YouTubeTranscript` nodes

For large-scale deployments, consider:
- Chunking transcript data for very long videos
- Archiving old comments to reduce database size
- Using S3/MinIO for storing video files (thumbnail, etc.)

## Future Enhancements

1. **Related Videos**: Integrate YouTube Data API for accurate recommendations
2. **Comment Replies**: Store full reply hierarchies
3. **Sentiment Analysis**: Analyze comments and transcripts
4. **Video Embeddings**: Store vector embeddings for semantic search
5. **Live Streaming**: Support for live chat and stream metadata
6. **Playlist Support**: Index video playlists and collections

## Performance Considerations

- **Fulltext Search**: Use fulltext indexes for title/description/comment search
- **Pagination**: Use cursor-based pagination for large result sets
- **Caching**: Consider Redis caching for frequently accessed videos
- **Batch Processing**: Polling worker processes videos in batches
- **Connection Pooling**: Neo4j driver manages connections automatically

## Troubleshooting

### Transcript Not Available

If auto-captions aren't available:
- Video may not have captions enabled
- Try with `--write-subtitles` instead of `--write-auto-sub`
- Some videos disable captions entirely

### Comments Disabled

Some videos disable comments:
- The service will return empty comment list
- Check video permissions on YouTube

### Chapters Not Found

If chapters aren't available:
- Check if video has native chapters
- Verify description has timestamp patterns
- Some videos don't use chapters

## Dependencies

- **yt-dlp**: For fetching YouTube data and comments
- **Neo4j**: Graph database for storage
- **FastAPI**: API server
- **Uvicorn**: ASGI server for API
- **Pydantic**: Data validation

## Security Notes

- Never store API keys in code
- Use environment variables for credentials
- Implement rate limiting for API endpoints
- Sanitize user inputs (search queries)
- Monitor for abuse/comment spam
