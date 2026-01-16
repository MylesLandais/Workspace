# YouTube GraphQL API

This directory provides a GraphQL API for YouTube videos backed by Neo4j.

## Schema

The GraphQL schema (`schema.graphql`) defines:

- `YouTubeVideo` - Video nodes with S3 references
- `YouTubeChannel` - Channel nodes with video relationships
- `MediaSignedUrl` - Presigned S3 URLs for video playback

## Implementation

### Services

- `services/youtube_service.py` - Neo4j queries for YouTube data
- `services/s3_url_service.py` - S3 presigned URL generation

### GraphQL Server

- `youtube_graphql_server.py` - Strawberry GraphQL server

## Usage

Start the server:

```bash
cd media-platform
docker compose up -d
python3 youtube_graphql_server.py
```

Query videos:

```graphql
query GetVideos {
  youtubeVideos(first: 10) {
    edges {
      node {
        id
        title
        url
        duration
        viewCount
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Get signed playback URL:

```graphql
query GetVideoUrl {
  mediaSignedUrl(videoId: "_VzW9-HnvD0") {
    url
    expiresAt
  }
}
```

## Architecture

```
Client
  ↓ (GraphQL)
Strawberry Server
  ↓ (Cypher)
Neo4j Graph DB
  + HAS_VIDEO relationship
  + S3 metadata (s3Key, s3Bucket)
  ↓ (presigned URL)
MinIO/S3 Storage
```

## Next Steps

1. Add authentication/authorization
2. Implement video upload endpoint
3. Add caching layer
4. Add metrics and monitoring
