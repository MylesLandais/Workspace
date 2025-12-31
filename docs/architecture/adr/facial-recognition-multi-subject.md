# Facial Recognition and Multi-Subject Image Analysis

## Status

Accepted

## Context

Media content (images, videos) often contains multiple subjects, but current ingestion only associates media with a single creator based on the source platform (e.g., subreddit name). Users want to:

- See content featuring a creator even when they're not the primary subject (e.g., group photos, event coverage)
- Automatically identify creators in images when the platform metadata doesn't indicate their presence
- Build creator-based feeds that include all content featuring that person, regardless of source context
- Handle images with multiple people where each person should be identified and linked

Traditional platform-based tagging (e.g., subreddit name) fails when:
- A post features multiple creators but only mentions one in the title/subreddit
- Content is cross-posted or shared without proper attribution
- Group photos or event coverage feature multiple creators

## Decision

Implement facial recognition and multi-subject image analysis by **integrating** existing open-source facial recognition tools (specifically Immich's implementation) rather than developing proprietary algorithms. Extract facial embeddings from images, match them against a Creator face database, and create `[:FEATURES]` relationships between Media and Creator nodes for all detected subjects.

**Approach**: Similar to Palantir's ontology-driven entity resolution pattern, we treat facial recognition as a data integration and fusion problem rather than a computer vision research problem. Biometric data (facial embeddings) are integrated into our graph ontology as first-class objects, enabling probabilistic matching and cross-media entity resolution without building custom ML models.

## Rationale

**Integration Over Algorithm Development**: Following the Palantir pattern of ontology-driven data fusion, we integrate existing facial recognition tools rather than developing proprietary algorithms. This focuses our engineering effort on entity resolution, graph relationships, and data integration—areas where we can add unique value.

**Leverage Existing Open-Source Work**: Immich has a production-ready facial recognition implementation with multi-subject detection, face clustering, and configurable thresholds. Reusing their architecture accelerates development and reduces maintenance burden compared to building custom models (e.g., FaceNet-style embeddings).

**Multi-Subject Support**: Immich's system handles multiple faces in a single image natively, which directly addresses our use case of identifying all creators in group photos.

**Open-Source Advantage**: Immich is TypeScript/Node.js based, making it easier to integrate or adapt compared to Python-only solutions. We can learn from their implementation patterns even if we don't use their code directly. This aligns with our principle of leveraging open-source projects.

**Graph-Native Integration**: Store facial recognition results as graph relationships (`[:FEATURES]`), enabling powerful queries like "all images featuring both Creator A and Creator B" or "group photos with Creator X". This mirrors Palantir's dynamic ontology approach where biometric data is linked probabilistically across sources.

**Creator Identity Resolution**: Facial recognition complements our Creator/Handle model by providing another signal for identity resolution beyond platform usernames and bio crawlers. Like Palantir's cross-media matching, we fuse facial data with social media profiles, metadata, and other signals to build comprehensive creator profiles.

## Consequences

**Positive**:
- Enables creator-based feeds that include all content featuring that person
- Improves content discovery beyond platform-based filtering
- Leverages proven open-source implementation (Immich)
- Graph relationships enable powerful multi-creator queries
- Supports manual correction workflow for uncertain matches

**Negative**:
- Requires ML model deployment and computational resources
- Privacy considerations for storing facial embeddings
- Requires building initial Creator face database (from profile avatars or manual uploads)
- False positives/negatives require manual review workflows
- May need GPU resources for real-time processing at scale

**Neutral**:
- Can start with Immich's approach and adapt to our Neo4j structure
- Batch processing recommended for efficiency (async after ingestion)
- Confidence thresholds need tuning per use case

## Implementation

### Integration Architecture Pattern

Our approach follows an **integration and ontology-driven** pattern rather than algorithm development:

1. **Facial Recognition as Data Integration**: We treat facial recognition as a data fusion problem, similar to Palantir's Gotham platform approach. Biometric data (facial embeddings) are integrated as structured objects in our Neo4j graph ontology, enabling probabilistic entity resolution across heterogeneous sources.

2. **Open-Source Tool Integration**: Rather than building custom ML models, we integrate existing open-source facial recognition tools (Immich). This mirrors how Palantir integrates third-party biometric tools, but we use open-source alternatives suitable for consumer applications.

3. **Graph-Native Entity Resolution**: Facial embeddings become first-class objects in our graph, linked via `[:FEATURES]` relationships to Creator nodes. This enables cross-media matching (images → creators → handles → media) similar to Palantir's cross-media entity resolution.

4. **Probabilistic Matching**: Confidence scores and thresholds (like Immich's configurable recognition distance) allow probabilistic matching with manual review workflows, enabling entity resolution while handling uncertainty.

**Key Difference from Palantir**: We use open-source tools and focus on consumer/content use cases (creator identification in social media content) rather than surveillance/government applications. Our ontology is Creator/Handle/Media-centric rather than person/profile/record-centric.

### Reference: Immich's Approach

Immich's facial recognition system provides several patterns we should adopt:

1. **Face Clustering**: Groups similar faces together before identity assignment. We can adapt this to create Creator clusters.

2. **Configurable Thresholds**:
   - Minimum detection score: Confidence threshold for face detection (reduces false positives)
   - Maximum recognition distance: Threshold for considering two faces as the same person
   - Minimum recognized faces: Minimum faces needed to create a person cluster

3. **Manual Adjustments**: Support for merging/hiding faces, changing feature photos, correcting misidentifications

4. **ML Pipeline**: Uses models for face detection and embedding generation

### Neo4j Graph Schema

```cypher
// Media node with facial recognition metadata
(:Media {
  id: String,
  url: String,
  facesDetected: Integer,  // Number of faces found in image
  faceRecognitionProcessed: Boolean,
  faceRecognitionProcessedAt: DateTime
})

// Creator node (existing, extended with face data)
(:Creator {
  id: String,
  slug: String,
  name: String,
  // ... existing properties ...
  faceEmbedding: List<Float>,  // Facial embedding vector (optional, could be external)
  faceDatabaseId: String,  // Reference to face database entry
  primaryFaceImageUrl: String  // Reference image for this creator
})

// Relationship: Media features a Creator (multiple per Media allowed)
(:Media)-[:FEATURES {
  confidence: Float,  // 0.0-1.0 similarity score
  detectedAt: DateTime,
  faceBoundingBox: Map,  // {x, y, width, height} for UI display
  verified: Boolean  // User-confirmed match
}]->(:Creator)
```

### Face Detection and Embedding Pipeline

```typescript
// Pseudocode for face detection workflow
async function processMediaForFaces(mediaId: string, imageUrl: string) {
  // 1. Download and load image
  const image = await loadImage(imageUrl);
  
  // 2. Detect faces (using Immich's approach or compatible library)
  const faces = await detectFaces(image);
  
  // 3. Extract embeddings for each face
  const faceEmbeddings = await Promise.all(
    faces.map(face => extractEmbedding(face))
  );
  
  // 4. For each detected face, find matching creators
  const matches = await Promise.all(
    faceEmbeddings.map(async (embedding, index) => {
      const creatorMatch = await findMatchingCreator(embedding, {
        maxDistance: FACE_RECOGNITION_THRESHOLD,
        minConfidence: MIN_DETECTION_SCORE
      });
      
      if (creatorMatch) {
        return {
          faceIndex: index,
          creatorId: creatorMatch.creatorId,
          confidence: creatorMatch.similarity,
          boundingBox: faces[index].boundingBox
        };
      }
      return null;
    })
  );
  
  // 5. Create FEATURES relationships in Neo4j
  for (const match of matches.filter(m => m !== null)) {
    await neo4j.query(`
      MATCH (m:Media {id: $mediaId})
      MATCH (c:Creator {id: $creatorId})
      MERGE (m)-[r:FEATURES]->(c)
      SET r.confidence = $confidence,
          r.detectedAt = datetime(),
          r.faceBoundingBox = $boundingBox,
          r.verified = false
    `, {
      mediaId,
      creatorId: match.creatorId,
      confidence: match.confidence,
      boundingBox: match.boundingBox
    });
  }
  
  // 6. Update Media node metadata
  await neo4j.query(`
    MATCH (m:Media {id: $mediaId})
    SET m.facesDetected = $count,
        m.faceRecognitionProcessed = true,
        m.faceRecognitionProcessedAt = datetime()
  `, {
    mediaId,
    count: faces.length
  });
}
```

### Creator Face Database Building

```typescript
// Build initial face database from Creator profile images
async function buildCreatorFaceDatabase() {
  // Get all creators with profile images
  const creators = await neo4j.query(`
    MATCH (c:Creator)
    WHERE c.avatarUrl IS NOT NULL
    RETURN c.id, c.slug, c.avatarUrl
  `);
  
  for (const creator of creators) {
    // Download profile image
    const image = await loadImage(creator.avatarUrl);
    
    // Detect and extract primary face
    const faces = await detectFaces(image);
    if (faces.length > 0) {
      const primaryFace = faces[0];  // Assume first face is the creator
      const embedding = await extractEmbedding(primaryFace);
      
      // Store embedding (could be in separate vector DB or Neo4j property)
      await storeCreatorFaceEmbedding(creator.id, embedding, {
        sourceImage: creator.avatarUrl,
        boundingBox: primaryFace.boundingBox
      });
    }
  }
}
```

### Querying Multi-Creator Content

```cypher
// Find all media featuring a specific creator
MATCH (m:Media)-[r:FEATURES {verified: true}]->(c:Creator {slug: "laufey"})
RETURN m
ORDER BY m.createdAt DESC

// Find media featuring multiple creators together
MATCH (m:Media)-[:FEATURES]->(c1:Creator {slug: "creator1"})
MATCH (m)-[:FEATURES]->(c2:Creator {slug: "creator2"})
WHERE c1 <> c2
RETURN m, c1, c2

// Find group photos (media with 3+ detected creators)
MATCH (m:Media)-[r:FEATURES {verified: true}]->(c:Creator)
WITH m, count(c) as creatorCount
WHERE creatorCount >= 3
RETURN m, creatorCount
ORDER BY creatorCount DESC

// Find unverified face matches for manual review
MATCH (m:Media)-[r:FEATURES {verified: false}]->(c:Creator)
WHERE r.confidence < 0.85  // Below high confidence threshold
RETURN m, c, r.confidence
ORDER BY r.confidence ASC
```

### Manual Review and Correction Workflow

```typescript
// GraphQL mutation for verifying/correcting face matches
type Mutation {
  verifyFaceMatch(
    mediaId: ID!,
    creatorId: ID!,
    verified: Boolean!
  ): FaceMatch!
  
  removeFaceMatch(
    mediaId: ID!,
    creatorId: ID!
  ): Boolean!
  
  addFaceMatch(
    mediaId: ID!,
    creatorId: ID!,
    boundingBox: BoundingBox!
  ): FaceMatch!
}
```

### Batch Processing Strategy

```typescript
// Process images asynchronously after ingestion
async function queueMediaForFaceRecognition(mediaId: string) {
  await jobQueue.add('face-recognition', {
    mediaId,
    priority: 'normal'  // Could prioritize based on source confidence
  });
}

// Worker processes face recognition jobs
jobQueue.process('face-recognition', async (job) => {
  const { mediaId } = job.data;
  const media = await neo4j.getMedia(mediaId);
  
  // Skip if already processed
  if (media.faceRecognitionProcessed) {
    return;
  }
  
  await processMediaForFaces(mediaId, media.url);
});
```

## Alternatives Considered

**Build From Scratch (Custom ML Models)**: Creating our own facial recognition algorithms (e.g., custom FaceNet-style embedding models) would give full control but requires significant ML research expertise and ongoing maintenance. This approach is unnecessary when proven open-source implementations exist. Similar to how Palantir doesn't build proprietary facial recognition models but integrates third-party biometric tools.

**Cloud APIs (AWS Rekognition, Google Vision)**: Simpler integration but adds cost, latency, and privacy concerns. Self-hosted open-source approach gives more control, better cost scaling, and aligns with our privacy-first principles.

**Image Tagging Only (No Facial Recognition)**: Relying on platform metadata and manual tagging is simpler but misses multi-subject content and requires extensive manual effort. This fails to leverage the graph-native entity resolution capabilities we're building.

**Perceptual Hashing Only**: Detecting duplicate images but not identifying subjects. Doesn't solve the multi-creator identification problem and misses the ontology-driven entity fusion benefits.

**Proprietary Government Tools (e.g., Clearview AI, DHS OBIM)**: Used by Palantir in government contracts, but these are closed-source, require special access, and raise significant privacy/ethical concerns inappropriate for our open-source consumer platform.

## Integration with Existing Systems

This feature integrates with:

- **Media Normalization ADR**: Extends Media nodes with facial recognition metadata
- **Creator/Handle Model ADR**: Enhances Creator identity resolution with visual signals
- **Unified Feed ADR**: Enables creator-based feeds that include all featuring content
- **Media Tagging ADR**: Complements visual similarity search with identity-based matching

## Implementation Phases

### Phase 1: Foundation
- Research and evaluate Immich's implementation
- Set up face detection and embedding extraction pipeline
- Build Creator face database from profile images
- Basic face matching against Creator database

### Phase 2: Graph Integration
- Implement `[:FEATURES]` relationship creation
- Add face recognition metadata to Media nodes
- GraphQL queries for creator-based media discovery

### Phase 3: Multi-Subject Support
- Handle multiple faces per image
- Multiple `[:FEATURES]` relationships per Media
- Multi-creator query support

### Phase 4: Manual Review Workflow
- UI for reviewing and correcting face matches
- Confidence-based filtering for review queue
- User verification workflow

## Configuration

Following Immich's configurable approach:

- **FACE_DETECTION_MIN_SCORE**: Minimum confidence for face detection (default: 0.7)
- **FACE_RECOGNITION_MAX_DISTANCE**: Maximum distance for matching faces (default: 0.6)
- **FACE_RECOGNITION_MIN_CONFIDENCE**: Minimum confidence for auto-linking (default: 0.85)
- **FACE_BATCH_SIZE**: Number of images to process per batch
- **FACE_DATABASE_UPDATE_INTERVAL**: How often to rebuild face database from profile images

## Privacy and Ethical Considerations

- **Consent**: Only process images from public sources (Reddit, etc.), not user-uploaded private content
- **Data Minimization**: Store only embeddings, not full images or face crops
- **Opt-Out**: Allow creators to opt out of facial recognition
- **Transparency**: Clearly indicate when content is matched via facial recognition
- **Accuracy**: Provide manual correction tools for false positives/negatives

## References

- [Immich Facial Recognition Documentation](https://docs.immich.app/features/facial-recognition)
- [User Story: Multi-Subject Image Analysis](../domains/subscriptions/user-stories.md#card-7-multi-subject-image-analysis--facial-recognition)
- [ADR: Media Tagging and Visual Search](./media-tagging-visual-search.md)
- [ADR: Creator/Handle Model](./creator-handle-model.md)
- Test Case: https://www.reddit.com/r/laufeyhot/comments/1ph7zfj/beauty/

### Reference Architecture: Palantir's Integration Pattern

Our approach follows Palantir's ontology-driven entity resolution pattern (data integration/fusion rather than algorithm development), but using open-source tools:

- **Palantir**: Integrates third-party biometric tools (e.g., Clearview AI, DHS OBIM) into Gotham's dynamic ontology for cross-media entity resolution
- **Our Approach**: Integrate open-source facial recognition (Immich) into Neo4j graph for creator entity resolution
- **Key Similarity**: Both treat biometric data as structured objects in an ontology, enabling probabilistic matching across heterogeneous sources
- **Key Difference**: We use open-source tools and focus on consumer/content use cases rather than surveillance/government applications

Note: We reference Palantir's architectural pattern (integration-focused ontology-driven approach), not their specific tools or applications, which are proprietary and government-focused.

