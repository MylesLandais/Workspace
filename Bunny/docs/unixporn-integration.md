# Unixporn Media Integration Guide

This document describes the integration between Jupyter (data mining/crawling) and Bunny (web client) for managing r/unixporn Reddit posts with MinIO media storage.

## Architecture Overview

```
┌─────────────────┐         ┌──────────────┐         ┌─────────────┐
│   Jupyter       │         │    MinIO     │         │    Bunny    │
│                 │         │   (S3 API)   │         │             │
│ 1. Crawl Reddit │────────▶│              │         │             │
│ 2. Download     │         │ Store Media  │         │             │
│    Media        │         │              │         │             │
│ 3. Update JSON  │         │              │         │             │
│                 │         │              │         │             │
│ 4. Sync to      │────────▶│              │────────▶│ 5. Display  │
│    Neo4j        │         │              │         │    Feed     │
└─────────────────┘         └──────────────┘         └─────────────┘
```

## Components

### 1. Jupyter (Data Mining)

#### Crawler Script: `crawl_unixporn.py`

- Fetches new posts from r/unixporn using Reddit API
- Downloads media (images/videos) to MinIO bucket `unixporn-media`
- Updates `data/unixporn_latest.json` with post metadata and MinIO URLs
- Can be run periodically (cron/systemd timer)

**Usage:**

```bash
cd ~/Workspace/jupyter
python crawl_unixporn.py
```

**Features:**

- Deduplication (skips existing posts)
- Media download with automatic extension detection
- JSON backup before updates
- Error handling and logging

#### Sync Script: `syncUnixpornPosts.ts` (Bunny)

- Syncs posts from JSON file to Neo4j database
- Handles `media_url` field from MinIO
- Updates Post nodes with media information

**Usage:**

```bash
cd ~/Workspace/Bunny/app/server
bun run src/scripts/syncUnixpornPosts.ts [path-to-unixporn_latest.json]
```

### 2. MinIO Storage

**Configuration:**

- Endpoint: `http://localhost:9000`
- Bucket: `unixporn-media`
- Object prefix: `unixporn/`
- URL pattern: `{endpoint}/{bucket}/{prefix}/{postId}.{ext}`

**Example:**

```
http://localhost:9000/unixporn-media/unixporn/1pwvpyb.mp4
```

### 3. Bunny (Web Client)

#### GraphQL API

- **Query:** `redditPosts(subreddit: "unixporn", limit: 20)`
- **Fields:**
  - `id`, `title`, `score`, `numComments`
  - `mediaUrl` - MinIO URL for media
  - `isRead` - Read/unread status (TODO: implement database tracking)

#### Feed Page: `/unixporn`

- Infinite scroll feed of r/unixporn posts
- Read/unread tracking (currently localStorage, TODO: database)
- Media display from MinIO URLs
- Mark as read/unread functionality

**Features:**

- Visual indicators for unread posts
- Click to mark as read
- Infinite scroll with intersection observer
- Responsive design

## Data Flow

1. **Crawling:**

   ```
   Reddit API → crawl_unixporn.py → MinIO → unixporn_latest.json
   ```

2. **Syncing:**

   ```
   unixporn_latest.json → syncUnixpornPosts.ts → Neo4j
   ```

3. **Display:**
   ```
   Neo4j → GraphQL API → Bunny Client → Feed View
   ```

## Setup Instructions

### 1. Ensure MinIO is Running

```bash
# Check if MinIO is accessible
curl http://localhost:9000/minio/health/live
```

### 2. Run Initial Crawl

```bash
cd ~/Workspace/jupyter
python crawl_unixporn.py
```

### 3. Sync to Neo4j

```bash
cd ~/Workspace/Bunny/app/server
bun run src/scripts/syncUnixpornPosts.ts
```

### 4. View Feed

Navigate to `http://localhost:3000/unixporn` in your browser.

## Automation

### Cron Job (Recommended)

Add to crontab to run every hour:

```bash
0 * * * * cd /home/warby/Workspace/jupyter && python crawl_unixporn.py >> /tmp/unixporn_crawl.log 2>&1
```

### Systemd Timer

Create `/etc/systemd/system/unixporn-crawler.timer`:

```ini
[Unit]
Description=Unixporn Crawler Timer

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

## Future Enhancements

1. **Database Read Tracking:**
   - Add `UserReadPost` relationship in Neo4j
   - Track read status per user
   - Add GraphQL mutations for marking posts as read

2. **Real-time Updates:**
   - WebSocket connection for new posts
   - Push notifications for unread posts

3. **Media Processing:**
   - Thumbnail generation
   - Video transcoding
   - Image optimization

4. **Analytics:**
   - View counts
   - Engagement metrics
   - Popular posts tracking

## Troubleshooting

### Media Not Loading

- Check MinIO bucket exists: `mc ls minio/unixporn-media`
- Verify bucket is public or CORS is configured
- Check media URLs in JSON file

### Posts Not Syncing

- Verify Neo4j connection
- Check JSON file path
- Review sync script logs

### Feed Not Displaying

- Check GraphQL API is running
- Verify Neo4j has Post nodes
- Check browser console for errors

## Related Files

- `jupyter/crawl_unixporn.py` - Main crawler script
- `jupyter/data/unixporn_latest.json` - Post data with MinIO URLs
- `Bunny/app/server/src/scripts/syncUnixpornPosts.ts` - Neo4j sync script
- `Bunny/app/server/src/bunny/resolvers.ts` - GraphQL resolvers
- `Bunny/app/client/app/unixporn/page.tsx` - Feed view component
- `Bunny/app/client/app/api/reddit/posts/route.ts` - API route
