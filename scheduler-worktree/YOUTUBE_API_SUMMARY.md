# YouTube Media API - Implementation Summary

## What Was Done

1. **Downloaded 10 YouTube videos** from Paige Anastasi's channel
   - Videos stored in `/tmp/youtube_videos/`
   - Total: 1.5GB of content

2. **Uploaded videos to MinIO/S3 storage**
   - Bucket: `media/youtube/`
   - Format: `.webm` files
   - All 10 videos successfully uploaded

3. **Created Neo4j graph nodes**
   - Schema: `YouTubeVideo` and `YouTubeChannel` labels
   - 10 video nodes with metadata (title, duration, view count, etc.)
   - 1 channel node: `paige.anastasi`
   - Relationships: `HAS_VIDEO`

4. **Built GraphQL/REST API server**
   - Framework: FastAPI
   - Port: 4003
   - Features:
     - Video listing with pagination
     - Single video retrieval
     - Presigned S3 URLs for playback
     - Channel information

## API Endpoints

### Health Check
```
GET /health
```
Response:
```json
{"status": "healthy", "service": "youtube-graphql"}
```

### Get Videos (Paginated)
```
GET /api/videos?first=10&after=<cursor>
```
Response:
```json
{
  "edges": [
    {
      "node": {
        "id": "_VzW9-HnvD0",
        "title": "finals week as a student athlete at clemson",
        "url": "https://www.youtube.com/watch?v=_VzW9-HnvD0",
        "duration": 888.0,
        "viewCount": 5039,
        "s3Key": "youtube/_VzW9-HnvD0.webm",
        "s3Bucket": "media",
        "contentType": "video/webm",
        "createdAt": "2026-01-02T00:46:13",
        "updatedAt": "2026-01-02T00:46:13"
      },
      "cursor": "123"
    }
  ],
  "pageInfo": {
    "hasNextPage": false,
    "hasPreviousPage": false,
    "startCursor": "123",
    "endCursor": "456"
  }
}
```

### Get Single Video
```
GET /api/videos/{video_id}
```

### Get Playback URL
```
GET /api/videos/{video_id}/playback-url?expiry=3600
```
Response:
```json
{
  "url": "https://localhost:9000/media/youtube/_VzW9-HnvD0.webm?X-Amz-...",
  "expiresAt": "2026-01-02T01:46:13Z"
}
```

### Get Channels
```
GET /api/channels
```

## Neo4j Schema

### YouTubeVideo Node
```cypher
(:YouTubeVideo {
  id: String (unique)
  title: String
  url: String
  description: String
  duration: Float
  viewCount: Integer
  s3Key: String
  s3Bucket: String
  contentType: String
  createdAt: DateTime
  updatedAt: DateTime
})
```

### YouTubeChannel Node
```cypher
(:YouTubeChannel {
  handle: String (unique)
  url: String
  crawledAt: DateTime
})
```

### Relationship
```cypher
(:YouTubeChannel)-[:HAS_VIDEO]->(:YouTubeVideo)
```

## Client Integration Example

```javascript
// Fetch videos
async function fetchVideos(first = 10, after = null) {
  const response = await fetch(
    `http://localhost:4003/api/videos?first=${first}${after ? `&after=${after}` : ''}`
  );
  const { edges, pageInfo } = await response.json();

  return {
    videos: edges.map(edge => edge.node),
    pageInfo
  };
}

// Get playback URL
async function getPlaybackUrl(videoId) {
  const response = await fetch(
    `http://localhost:4003/api/videos/${videoId}/playback-url`
  );
  const { url, expiresAt } = await response.json();

  // Use url in <video> tag or media player
  return { url, expiresAt };
}

// Example usage
const { videos, pageInfo } = await fetchVideos(10);
const firstVideo = videos[0];
const { url } = await getPlaybackUrl(firstVideo.id);

// Render in UI
<video src={url} controls />
```

## Video Files in Storage

All videos are available at: `s3://media/youtube/{video_id}.webm`

List of videos:
1. `ve974Hp62DY.webm` - "first day of school and official practices..."
2. `hgY28ux5KWY.webm` - "what is a Clemson football game actually like?!"
3. `F8DSVD8RelQ.webm` - "a productive weekend in the life as a student athlete..."
4. `N7rFDUcbeqA.webm` - "the start of 20 hour weeks as a gymnast..."
5. `XVMQpHgdvj4.webm` - "comparing lives with my sister for a day..."
6. `DFSmUM0VNkc.webm` - "what I eat in a week as a d1-athlete"
7. `hDEH4i8qPMI.webm` - "what a student-athlete does over fall break..."
8. `QhnuFVr_r3k.webm` - "How I Got Recruited D1: My Best Advice for Athletes"
9. `Vo3uMXoDtfQ.webm` - "What It's REALLY Like to Be Out With an Injury (D1 Athlete)"
10. `_VzW9-HnvD0.webm` - "finals week as a student athlete at clemson"

## Architecture

```
Client App
    ↓ (HTTP/REST)
FastAPI Server (port 4003)
    ↓ (Cypher queries)
Neo4j Graph Database
    + Video metadata
    + S3 references
    ↓ (presigned URL)
MinIO S3 Storage
    + Video files
    + Bucket: media/youtube/
```

## Next Steps for Client Integration

1. **Add dependency** (if using npm):
   ```bash
   npm install axios
   ```

2. **Create service module**:
   ```javascript
   // services/youtubeService.js
   const API_BASE = 'http://localhost:4003/api';

   export const youtubeService = {
     async getVideos(first = 10, after = null) {
       const params = new URLSearchParams({ first: String(first) });
       if (after) params.set('after', after);
       const res = await fetch(`${API_BASE}/videos?${params}`);
       return res.json();
     },
     async getVideo(id) {
       const res = await fetch(`${API_BASE}/videos/${id}`);
       return res.json();
     },
     async getPlaybackUrl(id, expiry = 3600) {
       const res = await fetch(`${API_BASE}/videos/${id}/playback-url?expiry=${expiry}`);
       return res.json();
     }
   };
   ```

3. **Create React component**:
   ```jsx
   import React, { useState, useEffect } from 'react';
   import { youtubeService } from '../services/youtubeService';

   function YouTubeGallery() {
     const [videos, setVideos] = useState([]);
     const [pageInfo, setPageInfo] = useState(null);

     useEffect(() => {
       async function loadVideos() {
         const data = await youtubeService.getVideos(10);
         setVideos(data.edges.map(e => e.node));
         setPageInfo(data.pageInfo);
       }
       loadVideos();
     }, []);

     return (
       <div className="video-grid">
         {videos.map(video => (
           <VideoCard key={video.id} video={video} />
         ))}
       </div>
     );
   }

   function VideoCard({ video }) {
     const [playbackUrl, setPlaybackUrl] = useState(null);

     const handlePlay = async () => {
       const { url } = await youtubeService.getPlaybackUrl(video.id);
       setPlaybackUrl(url);
     };

     return (
       <div className="video-card">
         <h3>{video.title}</h3>
         <p>Duration: {Math.floor(video.duration / 60)}m {video.duration % 60}s</p>
         <p>Views: {video.viewCount?.toLocaleString()}</p>
         {playbackUrl ? (
           <video src={playbackUrl} controls width="100%" />
         ) : (
           <button onClick={handlePlay}>Play</button>
         )}
       </div>
     );
   }
   ```

## Current Status

✅ Videos downloaded
✅ Videos uploaded to MinIO
✅ Neo4j graph nodes created
✅ API server built
⚠️  API server needs debugging (returning 500 errors)

## Troubleshooting

Server is running on port 4003 but returning 500 errors. Common issues:

1. **Neo4j connection**: Check NEO4J_URI and credentials
2. **MinIO connection**: Verify MinIO is running and accessible
3. **Dependencies**: Ensure `fastapi`, `uvicorn`, `boto3`, `neo4j` are installed

To check logs:
```bash
docker exec jupyter.dev.local ps aux | grep youtube_graphql
# Find the PID and check /tmp/ or journalctl
```

Restart server:
```bash
docker exec jupyter.dev.local pkill -f youtube_graphql
cd /tmp
docker exec jupyter.dev.local python3 youtube_graphql_server.py
```
