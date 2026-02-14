# YouTube Video Tracking in Reddit Threads

## Overview

The system now automatically detects and tracks YouTube videos mentioned in Reddit threads. This is perfect for tracking when your radio station content and live sets get discussed!

## How It Works

When crawling Reddit threads, the system:
1. Scans post selftext and all comments for YouTube URLs
2. Extracts video IDs from various YouTube URL formats
3. Creates `YouTubeVideo` nodes in Neo4j
4. Links threads to videos with `REFERENCES_VIDEO` relationships

## Supported YouTube URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://m.youtube.com/watch?v=VIDEO_ID`
- URLs with additional parameters

## Example: Your Radio Station Video

For your video `https://youtu.be/ausHf688YC8`:

When someone mentions it in a Reddit thread, the system will:
- Detect the YouTube link
- Extract video ID: `ausHf688YC8`
- Create a `YouTubeVideo` node
- Link the Reddit thread to the video

## Usage

### Automatic Detection

YouTube links are automatically detected during normal crawling:

```bash
docker compose exec jupyterlab python fast_thread_crawler.py \
    --seed "https://www.reddit.com/r/music/comments/..." \
    --speed medium \
    --max-threads 100
```

The crawler will automatically:
- Find YouTube links in comments/posts
- Store them in Neo4j
- Create relationships

### Query YouTube Videos

Find all Reddit threads that mention your video:

```cypher
MATCH (v:YouTubeVideo {video_id: "ausHf688YC8"})<-[:REFERENCES_VIDEO]-(p:Post)
RETURN 
  p.title,
  p.subreddit,
  p.permalink,
  p.created_utc
ORDER BY p.created_utc DESC
```

### Find All Videos Mentioned in a Subreddit

```cypher
MATCH (p:Post)-[:REFERENCES_VIDEO]->(v:YouTubeVideo)
WHERE p.subreddit = "music"
RETURN 
  v.video_id,
  v.url,
  count(p) as mention_count
ORDER BY mention_count DESC
LIMIT 20
```

### Track Your Radio Station Content

Find all your videos mentioned across Reddit:

```cypher
// First, get all your video IDs (you can maintain a list)
MATCH (v:YouTubeVideo)
WHERE v.video_id IN ["ausHf688YC8", "another_video_id", ...]
MATCH (p:Post)-[:REFERENCES_VIDEO]->(v)
RETURN 
  v.video_id,
  v.url,
  p.subreddit,
  p.title,
  p.permalink
ORDER BY p.created_utc DESC
```

## Graph Schema

### YouTubeVideo Node
```cypher
(:YouTubeVideo {
  video_id: String (unique),
  url: String,
  created_at: DateTime,
  updated_at: DateTime
})
```

### Relationship
```cypher
(Post)-[:REFERENCES_VIDEO {
  source_type: String,  // "post" or "comment"
  source_author: String,
  comment_id: String,   // if from comment
  discovered_at: DateTime
}]->(YouTubeVideo)
```

## Integration with Existing System

YouTube tracking works alongside Reddit thread relationships:
- Threads can reference other threads (`RELATES_TO`)
- Threads can reference YouTube videos (`REFERENCES_VIDEO`)
- Both are detected automatically during crawling

## Example Workflow

1. **Crawl subreddits** where your content might be discussed:
   ```bash
   docker compose exec jupyterlab python fast_thread_crawler.py \
       --seed "https://www.reddit.com/r/music/..." \
       --speed medium \
       --max-threads 500
   ```

2. **Query for your videos**:
   ```cypher
   MATCH (v:YouTubeVideo {video_id: "ausHf688YC8"})<-[:REFERENCES_VIDEO]-(p:Post)
   RETURN p.title, p.subreddit, p.permalink
   ```

3. **Monitor mentions** over time:
   ```cypher
   MATCH (v:YouTubeVideo {video_id: "ausHf688YC8"})<-[:REFERENCES_VIDEO]-(p:Post)
   WHERE p.created_utc > datetime() - duration({days: 7})
   RETURN count(p) as mentions_this_week
   ```

## Files

- `src/feed/utils/youtube_url_extractor.py` - YouTube URL extraction
- `src/feed/storage/thread_storage.py` - Enhanced with YouTube tracking
- `src/feed/storage/migrations/008_youtube_videos.cypher` - Schema migration

## Next Steps

1. **Run the migration**:
   ```bash
   # Migration runs automatically when using crawlers
   # Or run manually if needed
   ```

2. **Start crawling** subreddits relevant to your radio station

3. **Query regularly** to see where your content is being discussed

4. **Set up monitoring** for specific video IDs you care about

## Tips

- Use the fast crawler for large-scale monitoring
- Query regularly to track mentions over time
- Combine with Reddit thread relationships for full context
- Track multiple videos by maintaining a list of video IDs






