# Cross-Platform Media Normalization

## Status

Accepted

## Context

Different platforms return different JSON structures for media (Tweets, YouTube videos, TikToks, Reddit posts). The frontend needs a unified interface to render feeds without platform-specific logic.

## Decision

Define a standard `Media` interface and create platform adapters that normalize external API responses to this standard structure.

## Rationale

**Frontend Simplicity**: Single rendering component works for all platforms.

**Consistency**: Uniform data structure enables consistent sorting, filtering, and display.

**Maintainability**: Platform-specific logic isolated in adapters, not scattered in UI.

**Extensibility**: Adding new platforms only requires a new adapter, not frontend changes.

## Implementation

### Standard Media Interface

```typescript
interface Media {
  id: string;
  title: string;
  sourceUrl: string;
  publishDate: DateTime;
  thumbnail: string;
  mediaType: MediaType;
  duration?: number;  // For videos
  aspectRatio?: string;  // e.g., "16:9", "9:16", "1:1"
  viewCount?: number;
  platform: Platform;
  handle: Handle;
}
```

### Platform Adapters

Each platform has an adapter that maps its API response to the standard interface:

**Reddit Adapter**:
```typescript
function normalizeRedditPost(post: RedditPost): Media {
  return {
    id: post.id,
    title: post.title,
    sourceUrl: `https://reddit.com${post.permalink}`,
    publishDate: new Date(post.created_utc * 1000),
    thumbnail: post.thumbnail || post.url,
    mediaType: post.is_video ? MediaType.VIDEO : MediaType.IMAGE,
    aspectRatio: calculateAspectRatio(post),
    platform: Platform.REDDIT,
    handle: post.subreddit
  };
}
```

**YouTube Adapter**:
```typescript
function normalizeYouTubeVideo(video: YouTubeVideo): Media {
  return {
    id: video.id,
    title: video.snippet.title,
    sourceUrl: `https://youtube.com/watch?v=${video.id}`,
    publishDate: new Date(video.snippet.publishedAt),
    thumbnail: video.snippet.thumbnails.high.url,
    mediaType: MediaType.VIDEO,
    duration: parseDuration(video.contentDetails.duration),
    aspectRatio: "16:9",
    viewCount: video.statistics.viewCount,
    platform: Platform.YOUTUBE,
    handle: video.channelId
  };
}
```

### Neo4j Media Labels

Use labels for efficient querying without sparse properties:

```cypher
// Base Media node
CREATE (m:Media {
  id: $id,
  title: $title,
  sourceUrl: $sourceUrl,
  publishDate: datetime($publishDate),
  thumbnail: $thumbnail,
  mediaType: $mediaType,
  platform: $platform
})

// Add platform-specific label
FOREACH (ignoreMe IN CASE WHEN $mediaType = "video" THEN [1] ELSE [] END |
  SET m:Video
  SET m.duration = $duration
  SET m.viewCount = $viewCount
)

FOREACH (ignoreMe IN CASE WHEN $mediaType = "image" THEN [1] ELSE [] END |
  SET m:Image
  SET m.width = $width
  SET m.height = $height
)
```

## Consequences

**Positive**:
- Frontend code is platform-agnostic
- Consistent data structure across all sources
- Easy to add new platforms
- Efficient queries using labels

**Negative**:
- Adapter layer adds complexity
- Some data loss in normalization (platform-specific fields)
- Requires maintaining adapters for API changes

**Neutral**:
- Adapters can preserve raw platform data in separate property
- Normalization happens at ingestion time, not query time

## Alternatives Considered

**Platform-Specific Types**: Rejected because it requires platform-specific UI components and logic.

**Union Types**: Rejected because TypeScript union types don't work well with GraphQL and add complexity.

## Implementation Notes

- Store raw platform response in `rawData` property for debugging
- Version adapters to handle API changes
- Use aspect ratio for layout calculations (masonry grids)
- Duration in seconds for consistent sorting
- Thumbnail fallback chain (high -> medium -> low quality)

## References

- Adapter pattern
- Data normalization best practices


