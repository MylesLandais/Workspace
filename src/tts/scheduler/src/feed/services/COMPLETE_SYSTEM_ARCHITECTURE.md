# Complete Reverse Lookup System Architecture

## System Overview

A comprehensive reverse lookup and OSINT research system integrating:
1. **Stash** (Primary) - Self-hosted adult media organizer
2. **Multi-Source Crawlers** - Data18, IAFD, Indexxx
3. **Adult Reverse Image Search** - NameThatPorn, PornMD
4. **Watermark Detection** - OCR-based identification
5. **Face Recognition** - Performer matching
6. **GraphQL API** - Client-server architecture
7. **Neo4j Ontology** - Graph database for relationships

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    GraphQL API Layer                         │
│  (Strawberry GraphQL - Client-Server Architecture)          │
└──────────────┬──────────────────────────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
┌──────▼──────┐  ┌─────▼──────┐
│   Queries   │  │ Mutations  │
└──────┬──────┘  └─────┬──────┘
       │               │
┌───────┴───────────────────────┐
│   Service Layer               │
├───────────────────────────────┤
│ 1. ReverseImageSearch         │
│ 2. VideoIdentificationService │
│ 3. StashIntegration           │
│ 4. MultiSourceCrawler         │
│ 5. SpiderRecovery             │
└───────┬───────────────────────┘
        │
   ┌────┴────┬──────────┬──────────┬──────────┐
   │         │          │          │          │
┌──▼──┐  ┌──▼──┐   ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│Stash│  │Neo4j│   │Valkey │  │Data18 │  │IAFD   │
│API  │  │Graph│   │Vector │  │Crawler│  │Crawler│
└─────┘  └─────┘   └───────┘  └───────┘  └───────┘
                          │          │
                     ┌────▼────┐ ┌───▼────┐
                     │Indexxx  │ │Reverse │
                     │Crawler  │ │Search  │
                     └─────────┘ └────────┘
```

## Data Flow: Video Identification

### Primary Path (Stash Available)

```
Video File
    ↓
[Watermark Detection] → "fantasyhd.com"
    ↓
[Studio Identification] → "fantasyhd"
    ↓
[Stash Query] → FantasyHD scenes
    ↓
[Perceptual Hash Matching] → Exact scene match
    ↓
[StashDB Metadata] → Community data
    ↓
[Neo4j Storage] → Graph structure
    ↓
Result: High confidence (0.9)
```

### Fallback Path (Stash Unavailable)

```
Video File
    ↓
[Watermark Detection] → "fantasyhd.com"
    ↓
[Multi-Source Crawling]
    ├── Data18 → Performers, scenes
    ├── IAFD → Titles, cast
    └── Indexxx → Model profiles
    ↓
[Adult Reverse Image Search] → Performer names
    ↓
[Cross-Reference] → Verify across sources
    ↓
[Neo4j Storage] → Graph structure
    ↓
Result: Medium confidence (0.7)
```

## Component Details

### 1. Stash Integration (Primary)

**File**: `stash_integration.py`

**Features**:
- GraphQL API client for Stash
- Perceptual hash matching
- StashDB integration
- Scene and performer search
- Direct access to indexed collection

**Priority**: Highest (0.9 confidence)

### 2. Multi-Source Crawlers

**File**: `adult_content_crawlers.py`

**Sources**:
- **Data18**: Studio performers, scene lists
- **IAFD**: Distributor titles, performer filmography
- **Indexxx**: Model profiles, scene breakdowns

**Priority**: Medium (0.7 confidence)

### 3. Video Watermark Detection

**File**: `video_watermark_detection.py`

**Features**:
- Frame extraction
- OCR (Tesseract)
- Pattern matching
- Studio identification

### 4. Reverse Image Search

**File**: `reverse_image_search.py`

**Features**:
- URL lookup (Neo4j)
- Hash-based matching (SHA-256, dHash)
- Vector similarity (CLIP embeddings)
- External APIs (optional)

### 5. Spider Recovery

**File**: `spider_recovery.py`

**Features**:
- Check for missed images
- Manual post recovery
- Batch operations
- Gap analysis

## GraphQL API Endpoints

### Image Search

```graphql
query {
  checkImageCrawled(imageUrl: "...") { ... }
  findImageSource(imageUrl: "...") { ... }
  findExactMatches(imageUrl: "...") { ... }
  findSimilarImages(imageUrl: "...") { ... }
}
```

### Video Identification

```graphql
query {
  identifyVideo(
    videoPath: "..."
    watermarkPatterns: ["fantasyhd.com"]
    stashUrl: "http://192.168.0.222:9999"
  ) {
    identified
    studio
    sceneMatches {
      sceneTitle
      matchType  # 'stash', 'data18', 'iafd', 'indexxx'
      confidence
    }
  }
}
```

### Stash Queries

```graphql
query {
  stashScenes(
    stashUrl: "http://192.168.0.222:9999"
    studio: "FantasyHD"
    performerName: "Natalie"
  ) {
    id
    title
    url
    performers { name }
    phash
  }
  
  stashPerformers(
    stashUrl: "http://192.168.0.222:9999"
    query: "Natalie"
  ) {
    id
    name
    sceneCount
  }
}
```

## Neo4j Ontology

### Graph Structure

```
(Studio {slug: "fantasyhd"})
  -[:HAS_ACTOR]-> (Actor {data18_id, stash_id, name})
  -[:HAS_SCENE]-> (Scene {scene_id, stash_id, title})

(Actor)-[:APPEARS_IN]->(Scene)
(Scene)-[:FROM_STUDIO]->(Studio)
(Scene)-[:HAS_METADATA {source: "stash|data18|iafd|indexxx"}]->(Metadata)

(Video {path, phash})
  -[:MATCHES]->(Scene)
```

## Testing & Evaluation

### Test Suite

```bash
# Run all tests
pytest src/feed/services/tests/test_video_identification.py -v

# Test specific components
pytest src/feed/services/tests/test_video_identification.py::TestStashIntegration -v
```

### Evaluation Metrics

Track in test suite:
- **Watermark Detection Rate**: X%
- **Stash Match Rate**: X%
- **Multi-Source Coverage**: X sources
- **Processing Time**: X seconds
- **Confidence Distribution**: By source type

## Configuration

### Environment Variables

```bash
# Stash
STASH_URL=http://192.168.0.222:9999
STASH_API_KEY=optional_api_key

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Valkey (for vector search)
VALKEY_URI=redis://localhost:6379
```

### Stash Setup

1. **Install Stash**: Docker or native
2. **Configure Scrapers**: Add CommunityScrapers
3. **Index Media**: Scan directories
4. **Enable StashDB**: Connect to community database
5. **Access API**: http://192.168.0.222:9999/graphql

## Usage Examples

### Python

```python
from feed.services.video_watermark_detection import VideoIdentificationService
from feed.storage.neo4j_connection import get_connection

neo4j = get_connection()
service = VideoIdentificationService(
    neo4j=neo4j,
    stash_url="http://192.168.0.222:9999"  # Primary source
)

result = service.identify_video(
    "video.webm",
    watermark_patterns=["fantasyhd.com"]
)
```

### GraphQL

```graphql
query {
  identifyVideo(
    videoPath: "~/Downloads/1766554370099356.webm"
    watermarkPatterns: ["fantasyhd.com"]
    stashUrl: "http://192.168.0.222:9999"
  ) {
    identified
    studio
    sceneMatches {
      sceneTitle
      matchType
      confidence
      url
    }
  }
}
```

## Performance Characteristics

| Source | Speed | Coverage | Confidence | Notes |
|--------|-------|----------|------------|-------|
| **Stash** | Fast (local) | Your collection | 0.9 | Primary source |
| **Data18** | Medium | Public | 0.7 | Rate-limited |
| **IAFD** | Medium | Public | 0.7 | Rate-limited |
| **Indexxx** | Medium | Public | 0.7 | Rate-limited |
| **Reverse Search** | Slow | External | 0.6 | API-dependent |

## Best Practices

1. **Use Stash First**: Highest confidence, fastest
2. **Fallback to Crawlers**: If Stash unavailable
3. **Cache Results**: Store in Neo4j to avoid repeated queries
4. **Rate Limiting**: Respect API limits
5. **Error Handling**: Graceful degradation
6. **Progress Tracking**: Use test suite metrics

## Future Enhancements

1. **StashDB Direct Integration**: Query StashDB API directly
2. **Perceptual Hash Computation**: Implement pHash for videos
3. **Face Recognition**: Complete face matching implementation
4. **Batch Processing**: Process multiple videos efficiently
5. **Real-time Updates**: Monitor Stash for new content
6. **Advanced Matching**: ML-based scene recognition




