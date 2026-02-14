# Complete OSINT System for Video Identification

## System Overview

A comprehensive reverse lookup and OSINT research system for identifying adult video content using:
- Watermark detection (OCR)
- Multi-source database crawling (Data18, IAFD, Indexxx)
- Adult-specific reverse image search
- Face recognition matching
- Ontology building in Neo4j

## Architecture

```
Video File (webm)
    ↓
[Watermark Detection - OCR]
    ↓
[Studio Identification: "fantasyhd.com" → "fantasyhd"]
    ↓
[Multi-Source Database Crawling]
    ├── Data18.com (performers, scenes)
    ├── IAFD.com (titles, cast)
    └── Indexxx.com (model profiles, scene dates)
    ↓
[Adult Reverse Image Search]
    ├── NameThatPorn
    └── PornMD
    ↓
[Face Recognition Matching]
    └── Match against 188+ actor database
    ↓
[Scene Matching & Cross-Reference]
    ↓
[Ontology Building - Neo4j]
    ├── Studio nodes
    ├── Actor nodes
    ├── Scene nodes
    └── Relationships
```

## Components

### 1. Video Watermark Detection
- **File**: `video_watermark_detection.py`
- **Class**: `VideoWatermarkDetector`
- **Features**:
  - Frame extraction (configurable sampling)
  - OCR using Tesseract
  - Pattern matching for known watermarks
  - Deduplication of similar detections

### 2. Multi-Source Database Crawlers
- **File**: `adult_content_crawlers.py`
- **Classes**:
  - `Data18Crawler`: Studio performers, scene lists
  - `IAFDCrawler`: Distributor titles, performer filmography
  - `IndexxxCrawler`: Model profiles, scene breakdowns
  - `MultiSourceCrawler`: Orchestrates all sources
  - `AdultReverseImageSearch`: Adult-specific reverse search

### 3. Video Identification Service
- **File**: `video_watermark_detection.py`
- **Class**: `VideoIdentificationService`
- **Features**:
  - End-to-end identification workflow
  - Multi-source scene matching
  - Face recognition integration
  - Result aggregation

### 4. GraphQL API
- **File**: `graphql/image_search_schema.py`
- **Query**: `identifyVideo`
- **Returns**: Complete identification with watermarks, face matches, scene matches

## Usage Examples

### Python API

```python
from feed.services.video_watermark_detection import VideoIdentificationService
from feed.storage.neo4j_connection import get_connection

neo4j = get_connection()
service = VideoIdentificationService(
    neo4j=neo4j,
    enable_face_matching=True,
    use_multi_source=True  # Use Data18, IAFD, Indexxx
)

result = service.identify_video(
    "~/Downloads/1766554370099356.webm",
    watermark_patterns=["fantasyhd.com"]
)

print(f"Studio: {result.studio}")
print(f"Scene matches: {len(result.scene_matches)}")
for scene in result.scene_matches:
    print(f"  - {scene.scene_title} (source: {scene.source})")
```

### Multi-Source Crawling

```python
from feed.services.adult_content_crawlers import MultiSourceCrawler

crawler = MultiSourceCrawler()

# Get all performers
performers = crawler.get_all_fantasyhd_performers()
print(f"Found {len(performers)} performers across all sources")

# Search scenes
scenes = crawler.search_scenes_multi_source(studio="fantasyhd")
print(f"Found {len(scenes)} unique scenes")
```

### GraphQL API

```graphql
query {
  identifyVideo(
    videoPath: "~/Downloads/1766554370099356.webm"
    watermarkPatterns: ["fantasyhd.com"]
  ) {
    identified
    studio
    watermarks {
      text
      confidence
      frameNumber
    }
    sceneMatches {
      sceneId
      sceneTitle
      studio
      performers
      url
      source
      confidence
    }
  }
}
```

## Database Coverage

### Data18.com
- ✅ Studio performer lists (188+ for FantasyHD)
- ✅ Performer-specific scene lists
- ✅ Scene metadata and URLs
- ✅ Free trailers and photos

### IAFD.com
- ✅ Complete distributor catalog
- ✅ Historical title database
- ✅ Performer filmography
- ✅ Release dates and cast

### Indexxx.com
- ✅ Model profiles
- ✅ Scene breakdowns by site
- ✅ Co-star information
- ✅ Scene dates

## Testing & Evaluation

### Run Tests

```bash
pytest src/feed/services/tests/test_video_identification.py -v
```

### Test Coverage

- ✅ Watermark detection accuracy
- ✅ Multi-source crawling
- ✅ Scene matching
- ✅ Deduplication
- ✅ End-to-end identification
- ✅ Evaluation metrics

### Metrics Tracked

- Watermark detection rate
- Face matching accuracy
- Scene identification rate
- Processing time
- Database coverage
- Multi-source agreement

## Neo4j Ontology

### Graph Structure

```
(Studio {slug: "fantasyhd"})
  -[:HAS_ACTOR]-> (Actor {data18_id, name, profile_url})
  -[:HAS_SCENE]-> (Scene {scene_id, title, url})

(Actor)-[:APPEARS_IN]->(Scene)
(Scene)-[:FROM_STUDIO]->(Studio)
(Scene)-[:HAS_METADATA {source: "data18|iafd|indexxx"}]->(Metadata)
```

### Storing Results

```python
# Store complete identification
query = """
MATCH (s:Studio {slug: $studio})
MERGE (sc:Scene {scene_id: $scene_id})
ON CREATE SET
    sc.title = $title,
    sc.url = $url,
    sc.source = $source
MERGE (s)-[:HAS_SCENE]->(sc)
"""
```

## Best Practices

1. **Rate Limiting**: 2-5 second delays between requests
2. **Error Handling**: Graceful fallback if source unavailable
3. **Deduplication**: Automatic across sources
4. **Caching**: Store in Neo4j to avoid repeated queries
5. **Progressive Enhancement**: Start with fastest source, add others for verification

## Future Enhancements

1. **Face Recognition**: Implement actual face matching
2. **API Integration**: Direct API access where available
3. **Machine Learning**: Train models on metadata
4. **Real-time Updates**: Monitor sources for new content
5. **Community Integration**: Forum/Reddit discussions
6. **Additional Sources**: More aggregator sites

## References

- Data18: https://www.data18.com/studios/fantasyhd
- IAFD: https://www.iafd.com/distrib.rme/distrib=7411/fantasyhd.com.htm
- Indexxx: https://www.indexxx.com
- NameThatPorn: https://namethatporn.com




