# Video Identification & OSINT Research - Implementation Summary

## Overview

Extended the reverse lookup system to handle video identification using watermark detection, face recognition, and multi-source OSINT research.

## Components Created

### 1. Video Watermark Detection Service
**File**: `video_watermark_detection.py`

**Classes**:
- `VideoWatermarkDetector`: OCR-based watermark detection
- `Data18Crawler`: Crawler for data18.com database
- `FaceMatcher`: Face recognition and matching (placeholder for implementation)
- `VideoIdentificationService`: Orchestrates complete identification workflow

**Features**:
- Frame extraction from video files
- OCR using Tesseract for watermark detection
- Pattern matching for known watermarks (e.g., "fantasyhd.com")
- Studio identification from watermarks
- Actor database crawling
- Scene matching

### 2. Test Suite
**File**: `tests/test_video_identification.py`

**Test Coverage**:
- Watermark detection accuracy
- Frame extraction
- Data18 crawling
- End-to-end identification
- Evaluation metrics (detection rate, processing time, success rate)

### 3. GraphQL Integration
**File**: `graphql/image_search_schema.py`

**New Query**:
```graphql
query {
  identifyVideo(
    videoPath: "~/Downloads/1766554370099356.webm"
    watermarkPatterns: ["fantasyhd.com"]
  ) {
    identified
    studio
    watermarks { text, confidence, frameNumber }
    faceMatches { actorId, actorName, confidence }
    sceneMatches { sceneId, sceneTitle, url, confidence }
  }
}
```

### 4. Documentation
- `REVERSE_VIDEO_IDENTIFICATION_STORY.md`: Complete user story and methodology
- `VIDEO_IDENTIFICATION_SUMMARY.md`: This file

## Workflow

### Step 1: Watermark Detection
1. Extract frames from video (sample every 30 frames)
2. Run OCR on each frame
3. Detect watermark patterns
4. Extract studio name (e.g., "fantasyhd.com" → "fantasyhd")

### Step 2: Studio Identification
1. Map watermark to studio slug
2. Query data18.com for studio information
3. Get actor list (e.g., 188 actors for fantasyhd)

### Step 3: Actor Database Building
1. Crawl data18.com/studios/{studio}/pornstars
2. Extract actor entities
3. Store in Neo4j:
   - Studio node
   - Actor nodes (188 for fantasyhd)
   - Studio → HAS_ACTOR → Actor relationships

### Step 4: Face Recognition (Future)
1. Extract faces from video frames
2. Compute face encodings
3. Match against actor face database
4. Return matches with confidence scores

### Step 5: Scene Matching
1. For matched actors, query their scenes
2. Match scene metadata
3. Rank by confidence

### Step 6: Ontology Building
1. Create Studio, Actor, Scene nodes in Neo4j
2. Link relationships
3. Build comprehensive graph structure

## Usage Example

### Python API

```python
from feed.services.video_watermark_detection import VideoIdentificationService
from feed.storage.neo4j_connection import get_connection

neo4j = get_connection()
service = VideoIdentificationService(neo4j, enable_face_matching=True)

result = service.identify_video(
    "~/Downloads/1766554370099356.webm",
    watermark_patterns=["fantasyhd.com"]
)

print(f"Studio: {result.studio}")
print(f"Watermarks: {len(result.watermarks)}")
print(f"Scene matches: {len(result.scene_matches)}")
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
    }
    sceneMatches {
      sceneTitle
      url
    }
  }
}
```

## Testing & Evaluation

Run tests with:
```bash
pytest src/feed/services/tests/test_video_identification.py -v
```

**Metrics Tracked**:
- Watermark detection rate
- Face matching accuracy
- Scene identification rate
- Processing time
- Database coverage

## Dependencies

**Required**:
- `opencv-python`: Video processing
- `pytesseract`: OCR
- `Pillow`: Image processing
- `beautifulsoup4`: HTML parsing
- `requests`: HTTP requests

**Optional** (for face recognition):
- `face_recognition`: Face detection and matching
- `dlib`: Face recognition backend

## Next Steps

1. **Face Recognition Implementation**:
   - Implement face detection using OpenCV or face_recognition
   - Build actor face encoding database
   - Implement matching algorithm

2. **Enhanced OCR**:
   - Improve watermark detection accuracy
   - Handle partially obscured watermarks
   - Support multiple watermark patterns

3. **Multi-Source Research**:
   - Integrate additional databases
   - Cross-reference multiple sources
   - Build provenance chain

4. **Performance Optimization**:
   - Parallel frame processing
   - GPU acceleration
   - Caching results

5. **Ontology Expansion**:
   - Add Scene nodes
   - Link Video → Scene relationships
   - Build comprehensive metadata

## Notes

- Data18.com crawling respects rate limits (2-5 second delays)
- Watermark detection uses heuristic corner/edge detection
- Face matching is placeholder - needs implementation
- Scene matching currently basic - can be enhanced with metadata




