# Reverse Video Identification - User Story & Methodology

## User Story

**As an** OSINT researcher or content analyst  
**I want to** identify unknown video content using watermarks, face recognition, and multi-source database lookups  
**So that** I can:
- Identify the original source of video content
- Match actors and scenes from watermarked videos
- Build comprehensive metadata and ontology
- Track content across multiple platforms
- Conduct deep research investigations

## Use Case: FantasyHD Video Identification

### Scenario

We have a webm file (`~/Downloads/1766554370099356.webm`) that needs identification.

**Challenge**: The video has a watermark but we need to:
1. Detect the watermark using OCR
2. Identify the studio (fantasyhd.com)
3. Match against 188 actors in the database
4. Find the original scene/clip
5. Build metadata and ontology

### Methodology

#### Step 1: Watermark Detection

**Process**:
1. Extract frames from video (sample every 30 frames)
2. Run OCR on each frame to detect text
3. Identify watermark patterns (e.g., "fantasyhd.com")
4. Extract studio name from watermark

**Tools**:
- OpenCV for frame extraction
- Tesseract OCR for text detection
- Pattern matching for watermark identification

**Output**: `WatermarkDetection` with:
- Detected text: "fantasyhd.com"
- Confidence score
- Frame number and timestamp

#### Step 2: Studio Identification

**Process**:
1. Extract domain from watermark
2. Map to studio slug (fantasyhd.com → fantasyhd)
3. Query data18.com for studio information

**Output**: Studio metadata and actor list

#### Step 3: Actor Database Lookup

**Process**:
1. Crawl data18.com/studios/fantasyhd/pornstars
2. Extract all 188 actor entities
3. Store in Neo4j with:
   - Actor ID
   - Name
   - Profile URL
   - Studio relationship

**Output**: List of 188 actors with IDs

#### Step 4: Face Recognition Matching

**Process**:
1. Extract faces from video frames
2. Compute face encodings
3. Match against actor face database
4. Return matches with confidence scores

**Tools**:
- face_recognition library
- DeepFace (alternative)
- Custom face recognition model

**Output**: `FaceMatch` results with:
- Actor ID and name
- Confidence score
- Frame number

#### Step 5: Scene Matching

**Process**:
1. For each matched actor, query their scenes
2. Match scene metadata against video characteristics
3. Rank scenes by confidence

**Output**: `SceneMatch` results with:
- Scene ID and title
- Studio
- Actors list
- URL
- Confidence score

#### Step 6: Ontology Building

**Process**:
1. Create/update Studio node in Neo4j
2. Create/update Actor nodes
3. Create/update Scene nodes
4. Link relationships:
   - Studio → Actor
   - Actor → Scene
   - Video → Scene (via watermark/face match)

**Output**: Graph structure in Neo4j

#### Step 7: Multi-Source Research

**Process**:
1. Use identified scene to search:
   - Original studio website
   - Alternative databases
   - Social media platforms
   - Content aggregators

**Output**: Comprehensive metadata and source links

## Technical Implementation

### Components

1. **VideoWatermarkDetector**
   - Frame extraction
   - OCR processing
   - Watermark pattern matching

2. **Data18Crawler**
   - Studio actor list crawling
   - Scene database queries
   - HTML parsing and extraction

3. **FaceMatcher**
   - Face detection
   - Face encoding computation
   - Actor database matching

4. **VideoIdentificationService**
   - Orchestrates all components
   - Combines results
   - Returns comprehensive identification

### Data Flow

```
Video File
    ↓
[Frame Extraction]
    ↓
[OCR → Watermark Detection]
    ↓
[Studio Identification]
    ↓
[Data18 Crawler → Actor List]
    ↓
[Face Recognition → Actor Matching]
    ↓
[Scene Database → Scene Matching]
    ↓
[Ontology Building → Neo4j]
    ↓
[Multi-Source Research]
    ↓
Complete Identification Result
```

## GraphQL Integration

### Query: Identify Video

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
      timestamp
    }
    faceMatches {
      actorId
      actorName
      confidence
      frameNumber
    }
    sceneMatches {
      sceneId
      sceneTitle
      studio
      actors
      url
      confidence
    }
  }
}
```

### Mutation: Index Video

```graphql
mutation {
  indexVideo(
    videoPath: "~/Downloads/1766554370099356.webm"
    studio: "fantasyhd"
    actors: ["actor1", "actor2"]
    sceneId: "scene123"
  ) {
    success
    videoId
    nodesCreated
    relationshipsCreated
  }
}
```

## Testing & Evaluation

### Test Framework

Create evaluation tests that:
1. Test watermark detection accuracy
2. Test face matching precision/recall
3. Test scene matching correctness
4. Measure processing time
5. Track identification success rate

### Test Cases

1. **Watermark Detection Test**
   - Input: Video with known watermark
   - Expected: Correct watermark detected
   - Metric: Precision, Recall, F1

2. **Face Matching Test**
   - Input: Video with known actors
   - Expected: Correct actors matched
   - Metric: Top-1 accuracy, Top-5 accuracy

3. **End-to-End Test**
   - Input: Unknown video file
   - Expected: Complete identification
   - Metric: Success rate, processing time

## Challenges & Solutions

### Challenge 1: Paywalled Content

**Problem**: Main studio site is paywalled

**Solution**: 
- Use data18.com as primary source
- Crawl public pages only
- Build actor/scene database from public data

### Challenge 2: Large Actor Database

**Problem**: 188 actors to match against

**Solution**:
- Pre-compute face encodings
- Store in Neo4j with indexes
- Use efficient similarity search

### Challenge 3: Video Processing Performance

**Problem**: Processing full videos is slow

**Solution**:
- Sample frames intelligently
- Parallel processing
- Cache results
- Use GPU acceleration

### Challenge 4: OCR Accuracy

**Problem**: Watermarks may be partially obscured

**Solution**:
- Multiple frame sampling
- Image preprocessing (contrast, sharpening)
- Confidence thresholding
- Pattern matching fallback

## Future Enhancements

1. **Multi-Studio Support**: Expand beyond fantasyhd
2. **Deep Learning**: Train custom watermark/face models
3. **Real-time Processing**: Stream video identification
4. **Federated Search**: Query multiple databases simultaneously
5. **Metadata Enrichment**: Auto-tag with categories, tags, etc.
6. **Temporal Analysis**: Track content over time
7. **Source Attribution**: Build provenance chain

## Evaluation Metrics

Track in test suite:
- Watermark detection rate: X%
- Face matching accuracy: X%
- Scene identification rate: X%
- Average processing time: X seconds
- Database coverage: X actors/scenes indexed




