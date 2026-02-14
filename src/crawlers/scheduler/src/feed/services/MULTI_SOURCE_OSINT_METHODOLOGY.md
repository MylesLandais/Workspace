# Multi-Source OSINT Methodology for Adult Content Identification

## Overview

Enhanced reverse lookup system with multi-source database support for comprehensive OSINT research on adult video content.

## Supported Databases

### 1. Data18.com
**URL**: https://www.data18.com/studios/fantasyhd/pornstars

**Strengths**:
- Detailed scene lists per performer/studio
- Free trailers and photos
- Filters by studio
- Performer-specific FantasyHD pages

**Usage**:
```python
from feed.services.adult_content_crawlers import Data18Crawler

crawler = Data18Crawler()
performers = crawler.get_studio_performers("fantasyhd")
scenes = crawler.get_performer_fantasyhd_scenes(performer_id, "fantasyhd")
```

### 2. IAFD.com (Internet Adult Film Database)
**URL**: https://www.iafd.com/distrib.rme/distrib=7411/fantasyhd.com.htm

**Strengths**:
- Comprehensive title and performer database
- Distributor lookup functionality
- Lists all known FantasyHD titles and cast
- Historical data coverage

**Usage**:
```python
from feed.services.adult_content_crawlers import IAFDCrawler

crawler = IAFDCrawler()
titles = crawler.get_distributor_titles("fantasyhd.com")
performer_titles = crawler.get_performer_fantasyhd_titles("Performer Name")
```

### 3. Indexxx.com
**URL**: https://www.indexxx.com/models/{model-name}

**Strengths**:
- Model profiles with scene breakdowns by site
- Direct counts of FantasyHD appearances per model
- Scene dates and co-stars information
- Detailed metadata

**Usage**:
```python
from feed.services.adult_content_crawlers import IndexxxCrawler

crawler = IndexxxCrawler()
scenes = crawler.get_model_fantasyhd_scenes("Model Name")
```

## Complete Workflow

### Step 1: Watermark Detection
```python
from feed.services.video_watermark_detection import VideoWatermarkDetector

detector = VideoWatermarkDetector()
watermarks = detector.detect_watermarks_in_video(
    "video.webm",
    watermark_patterns=["fantasyhd.com"]
)
```

### Step 2: Studio Identification
Extract studio from watermark:
- "fantasyhd.com" → "fantasyhd"
- Map to studio slug for database queries

### Step 3: Multi-Source Performer Database
```python
from feed.services.adult_content_crawlers import MultiSourceCrawler

crawler = MultiSourceCrawler()
performers = crawler.get_all_fantasyhd_performers()
# Returns deduplicated list from all sources
```

### Step 4: Scene Search Across Sources
```python
scenes = crawler.search_scenes_multi_source(
    studio="fantasyhd",
    performer_name=None,  # Optional filter
    keywords=None  # Optional keywords
)
# Returns combined results from Data18, IAFD, Indexxx
```

### Step 5: Adult Reverse Image Search
```python
from feed.services.adult_content_crawlers import AdultReverseImageSearch

reverse_search = AdultReverseImageSearch()
results = reverse_search.search_by_image("frame.jpg", provider="namethatporn")
# Returns performer names, scene titles, confidence scores
```

### Step 6: Cross-Reference and Verification
1. Match reverse search results against database scenes
2. Verify performer names across multiple sources
3. Build confidence scores from multiple matches
4. Identify exact scene match

## GraphQL API

### Query: Identify Video (Multi-Source)

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
    }
    sceneMatches {
      sceneId
      sceneTitle
      studio
      performers
      url
      source  # 'data18', 'iafd', 'indexxx'
      confidence
    }
  }
}
```

## Database Comparison

| Feature | Data18 | IAFD | Indexxx |
|---------|--------|------|---------|
| Studio performer lists | ✅ | ❌ | ❌ |
| Performer scene lists | ✅ | ✅ | ✅ |
| Scene metadata | ✅ | ✅ | ✅ |
| Release dates | Partial | ✅ | ✅ |
| Co-stars | Partial | ✅ | ✅ |
| Descriptions | Partial | ✅ | Partial |

## Best Practices

1. **Rate Limiting**: All crawlers respect 2-5 second delays
2. **Deduplication**: MultiSourceCrawler automatically deduplicates results
3. **Error Handling**: Graceful fallback if one source fails
4. **Caching**: Store results in Neo4j to avoid repeated queries
5. **Progressive Enhancement**: Start with Data18, add IAFD/Indexxx for verification

## Ontology Building

### Neo4j Graph Structure

```
(Studio {slug: "fantasyhd"})
  -[:HAS_ACTOR]-> (Actor {data18_id, name})
  -[:HAS_SCENE]-> (Scene {scene_id, title})

(Actor)-[:APPEARS_IN]->(Scene)
(Scene)-[:FROM_STUDIO]->(Studio)
(Scene)-[:HAS_METADATA]->(Metadata {source: "data18|iafd|indexxx"})
```

### Storing Multi-Source Data

```python
# Store performer with multiple source references
query = """
MATCH (s:Studio {slug: $studio})
MERGE (a:Actor {data18_id: $data18_id})
ON CREATE SET
    a.name = $name,
    a.data18_url = $data18_url,
    a.iafd_url = $iafd_url,
    a.indexxx_url = $indexxx_url
MERGE (s)-[:HAS_ACTOR]->(a)
"""
```

## Testing & Evaluation

### Test Multi-Source Coverage

```python
# Test that all sources are accessible
crawler = MultiSourceCrawler()
performers_data18 = crawler.data18.get_studio_performers("fantasyhd")
scenes_iafd = crawler.iafd.get_distributor_titles("fantasyhd.com")

assert len(performers_data18) > 0
assert len(scenes_iafd) > 0
```

### Evaluate Identification Accuracy

```python
# Test end-to-end identification
result = video_service.identify_video(video_path)
assert result.identified == True
assert len(result.scene_matches) > 0
assert any(s.source in ['data18', 'iafd', 'indexxx'] for s in result.scene_matches)
```

## Future Enhancements

1. **Additional Sources**: Add more aggregator sites
2. **API Integration**: Direct API access where available
3. **Machine Learning**: Train models on extracted metadata
4. **Real-time Updates**: Monitor sources for new content
5. **Community Data**: Integrate forum/Reddit discussions

## References

- Data18: https://www.data18.com/studios/fantasyhd
- IAFD: https://www.iafd.com/distrib.rme/distrib=7411/fantasyhd.com.htm
- Indexxx: https://www.indexxx.com
- NameThatPorn: https://namethatporn.com (reverse image search)




