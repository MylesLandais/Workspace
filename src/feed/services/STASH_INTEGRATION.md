# Stash Integration Guide

## Overview

Stash (stashapp/stash) is a self-hosted adult media organizer that provides:
- **Perceptual hashing** for scene identification
- **StashDB integration** (crowd-sourced metadata)
- **Community scrapers** for FantasyHD and other studios
- **Performer recognition** and tagging
- **Scene matching** and metadata enrichment

## Why Stash?

Stash is ideal for OSINT workflows because:
1. **Local Control**: All data stays private, no cloud uploads
2. **Comprehensive Indexing**: Built-in support for large collections
3. **Community Scrapers**: FantasyHD scrapers already available
4. **Perceptual Hashing**: Identifies clips without manual lookup
5. **StashDB Integration**: Crowd-sourced metadata from community
6. **GraphQL API**: Easy integration with our system

## Setup

### 1. Install Stash

```bash
# Docker (recommended)
docker run -d \
  --name stash \
  -p 9999:9999 \
  -v /path/to/media:/data \
  stashapp/stash:latest
```

### 2. Access Stash

- Local: http://localhost:9999
- Network: http://192.168.0.222:9999 (your instance)
- Custom domain: http://stash.xyz (if configured)

### 3. Configure Scrapers

Install FantasyHD scraper from CommunityScrapers:
- https://github.com/stashapp/CommunityScrapers
- Enables automatic metadata scraping for FantasyHD content

## Integration

### Python API

```python
from feed.services.stash_integration import StashClient, StashIntegration

# Connect to Stash
stash_url = "http://192.168.0.222:9999"
client = StashClient(stash_url)

# Get FantasyHD scenes
scenes = client.get_fantasyhd_scenes(limit=100)
print(f"Found {len(scenes)} FantasyHD scenes")

# Search by performer
scenes = client.search_scenes(
    performer_name="Natalie",
    studio="FantasyHD"
)

# Get scene by ID
scene = client.get_scene_by_id("1934")
print(f"Scene: {scene.title}")
```

### Video Identification with Stash

```python
from feed.services.video_watermark_detection import VideoIdentificationService

service = VideoIdentificationService(
    neo4j=neo4j,
    stash_url="http://192.168.0.222:9999"  # Enable Stash
)

result = service.identify_video(
    "video.webm",
    watermark_patterns=["fantasyhd.com"]
)

# Stash matches have highest confidence
stash_matches = [s for s in result.scene_matches if s.match_type == 'stash']
```

### GraphQL API

```graphql
# Query Stash scenes
query {
  stashScenes(
    stashUrl: "http://192.168.0.222:9999"
    studio: "FantasyHD"
    performerName: "Natalie"
    limit: 20
  ) {
    id
    title
    url
    date
    performers {
      name
      stashId
    }
    phash
    stashId
  }
}

# Query Stash performers
query {
  stashPerformers(
    stashUrl: "http://192.168.0.222:9999"
    query: "Natalie"
    limit: 10
  ) {
    id
    name
    sceneCount
    stashId
  }
}

# Identify video with Stash
query {
  identifyVideo(
    videoPath: "~/Downloads/1766554370099356.webm"
    watermarkPatterns: ["fantasyhd.com"]
    stashUrl: "http://192.168.0.222:9999"
  ) {
    identified
    sceneMatches {
      sceneTitle
      matchType  # 'stash' for Stash matches
      confidence
      url
    }
  }
}
```

## Workflow Priority

When Stash is available, the system uses this priority:

1. **Stash** (if available)
   - Perceptual hash matching
   - StashDB metadata
   - Community scraper data
   - Highest confidence (0.9)

2. **Multi-Source Crawlers** (if Stash unavailable)
   - Data18.com
   - IAFD.com
   - Indexxx.com
   - Medium confidence (0.7)

3. **Adult Reverse Image Search** (supplementary)
   - NameThatPorn
   - PornMD
   - Lower confidence (0.6)

## StashDB Integration

StashDB is a crowd-sourced metadata database (like MusicBrainz for adult content).

### Benefits

- **Collaborative**: Community-maintained metadata
- **Comprehensive**: Covers many studios and performers
- **Stash-ID**: Unique identifiers for scenes/performers
- **Automatic Matching**: Stash can auto-match via phash

### Usage

```python
# Scene with StashDB ID
scene = client.get_scene_by_id("1934")
if scene.stash_id:
    # StashDB metadata available
    print(f"StashDB ID: {scene.stash_id}")
    # Can query StashDB API: https://stashdb.org/api/v1/scenes/{stash_id}
```

## Perceptual Hashing

Stash uses perceptual hashing (pHash) to identify scenes:
- **Robust**: Works even with compression, cropping, resizing
- **Fast**: Efficient matching against large databases
- **Accurate**: High precision for exact scene matches

### Matching Workflow

1. Extract frame from video
2. Compute perceptual hash
3. Match against Stash database
4. Return matches with Hamming distance
5. Calculate confidence from distance

## Community Scrapers

Stash community maintains scrapers for:
- FantasyHD / PornPros network
- Many other studios
- Automatic metadata enrichment

### Installation

1. Go to Stash Settings → Scrapers
2. Add CommunityScrapers repository
3. Enable FantasyHD scraper
4. Configure auto-scraping

## Neo4j Integration

Store Stash data in Neo4j for cross-referencing:

```cypher
// Store Stash scene
MATCH (s:Studio {slug: "fantasyhd"})
MERGE (sc:Scene {stash_id: $stash_id})
ON CREATE SET
    sc.title = $title,
    sc.stash_url = $stash_url,
    sc.phash = $phash
MERGE (s)-[:HAS_SCENE]->(sc)

// Link performers
MATCH (sc:Scene {stash_id: $stash_id})
MATCH (a:Actor {stash_id: $performer_stash_id})
MERGE (a)-[:APPEARS_IN]->(sc)
```

## Testing

### Test Stash Connection

```python
from feed.services.stash_integration import StashClient

client = StashClient("http://192.168.0.222:9999")
scenes = client.get_fantasyhd_scenes(limit=10)
assert len(scenes) > 0, "Stash connection failed"
```

### Test Video Identification

```python
service = VideoIdentificationService(
    neo4j=neo4j,
    stash_url="http://192.168.0.222:9999"
)

result = service.identify_video("test.webm")
assert result.identified == True
assert any(s.match_type == 'stash' for s in result.scene_matches)
```

## Advantages Over External Crawlers

| Feature | Stash | External Crawlers |
|---------|-------|-------------------|
| **Data Ownership** | ✅ Local | ❌ External |
| **Perceptual Hashing** | ✅ Built-in | ❌ Manual |
| **StashDB Integration** | ✅ Native | ❌ None |
| **Community Scrapers** | ✅ Available | ❌ Manual |
| **Performance** | ✅ Fast (local) | ⚠️ Rate-limited |
| **Coverage** | ✅ Your collection | ✅ Public databases |

## Best Practices

1. **Use Stash as Primary**: Highest confidence, most comprehensive
2. **Fallback to Crawlers**: If Stash unavailable or no match
3. **Sync to Neo4j**: Store Stash data for cross-referencing
4. **Enable Scrapers**: Use community scrapers for auto-enrichment
5. **StashDB IDs**: Track StashDB IDs for community metadata

## References

- **Stash GitHub**: https://github.com/stashapp/stash
- **Stash Docs**: https://docs.stashapp.cc/
- **StashDB**: https://stashdb.org/
- **Community Scrapers**: https://github.com/stashapp/CommunityScrapers
- **Stash Forum**: https://discourse.stashapp.cc/




