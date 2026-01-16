# Forum Thread Parsing & Wanted Metadata - User Story

## User Story

**As an** OSINT researcher investigating missing content  
**I want to** parse forum threads, track wanted metadata, and cross-reference sources  
**So that** I can:
- Extract images from forum discussions for reverse search
- Track missing content from various sources (18eighteen.com, etc.)
- Verify performers across multiple databases
- Build comprehensive ontology with forum context
- Evaluate reverse lookup system performance

## Use Case: Natalie Monroe Investigation

### Scenario

We found a forum thread on planetsuzy.org discussing "Natalie Monroe" with braces:
- Thread URL: http://www.planetsuzy.org/showthread.php?p=23377199&styleid=3
- Contains images that can be used for reverse similarity search
- References missing content from 18eighteen.com

We also found the performer on 18eighteen.com:
- URL: https://www.18eighteen.com/nude-teen-photos/Natalie-Monroe/43308/
- Content is missing from our self-hosted platform
- Need to verify if it maps to data18.com

### Workflow

#### Step 1: Parse Forum Thread

**Process**:
1. Parse vBulletin thread structure
2. Extract all posts and content
3. Extract all images from posts
4. Extract tags/keywords (e.g., "braces", "Natalie Monroe")
5. Store in Neo4j with relationships

**Output**: `ForumThread` with:
- Thread metadata (title, author, forum)
- All posts with content
- All image URLs
- Extracted tags

#### Step 2: Index Thread Images

**Process**:
1. Extract image URLs from thread
2. Index each image for reverse search:
   - Compute hashes (SHA-256, dHash)
   - Compute CLIP embeddings
   - Store in Neo4j and Valkey

**Output**: Images ready for reverse similarity search

#### Step 3: Track Wanted Metadata

**Process**:
1. Create "Wanted" entry for missing content
2. Link to performer node
3. Store source information (18eighteen.com)
4. Link forum thread to wanted entry

**Output**: Neo4j graph:
```
(Performer {name: "Natalie Monroe"})
  -[:WANTED]-> (Wanted {source_url: "18eighteen.com/...", source_type: "18eighteen"})
  -[:DISCUSSED_IN]-> (ForumThread {url: "planetsuzy.org/..."})
```

#### Step 4: Cross-Source Verification

**Process**:
1. Check if performer exists on data18.com
2. Verify 18eighteen → data18 mapping
3. Check Neo4j for existing content
4. Check Stash (if available)

**Output**: Verification results across all sources

#### Step 5: Evaluation & Benchmarking

**Process**:
1. Run test cases for reverse lookup
2. Measure accuracy, confidence, processing time
3. Track source breakdown
4. Generate benchmark report

**Output**: Evaluation metrics and progress tracking

## Components

### 1. Forum Parser (`forum_parser.py`)

**VBulletinParser**:
- Parses vBulletin forum threads
- Extracts posts, images, tags
- Supports search functionality

**Features**:
- Thread parsing
- Post extraction
- Image extraction
- Tag/keyword extraction
- Search support

### 2. Forum Storage (`forum_storage.py`)

**ForumStorage**:
- Stores forum threads in Neo4j
- Links images for reverse search
- Creates graph structure

**Graph Structure**:
```
(Forum {url: "planetsuzy.org"})
  -[:HAS_THREAD]-> (ForumThread {thread_id, title})
    -[:HAS_POST]-> (ForumPost {post_id, content})
    -[:HAS_IMAGE]-> (Image {url})
    -[:HAS_TAG]-> (Tag {name})
```

### 3. Wanted Metadata Tracker (`wanted_metadata_tracker.py`)

**WantedMetadataTracker**:
- Tracks missing content
- Links to performers
- Cross-references sources

**Features**:
- Create wanted entries
- Link forum threads
- Cross-reference sources
- Track missing status

### 4. Cross-Source Verifier (`cross_source_verifier.py`)

**CrossSourceVerifier**:
- Verifies performers across sources
- Maps between different databases
- Checks existence

**Sources Supported**:
- 18eighteen.com
- data18.com
- Neo4j (local)
- Stash (if available)

### 5. Evaluation Framework (`evaluation_framework.py`)

**ReverseLookupEvaluator**:
- Runs benchmark tests
- Measures performance
- Generates reports

**Metrics Tracked**:
- Accuracy
- Confidence scores
- Processing time
- Source breakdown

## GraphQL Integration

### Query: Parse Forum Thread

```graphql
query {
  parseForumThread(
    threadUrl: "http://www.planetsuzy.org/showthread.php?p=23377199"
    indexImages: true
  ) {
    success
    threadId
    title
    imagesFound
    imagesIndexed
  }
}
```

### Mutation: Create Wanted Entry

```graphql
mutation {
  createWantedEntry(
    performerName: "Natalie Monroe"
    sourceUrl: "https://www.18eighteen.com/nude-teen-photos/Natalie-Monroe/43308/"
    sourceType: "18eighteen"
  ) {
    success
    wantedId
  }
}
```

### Query: Cross-Reference Sources

```graphql
query {
  crossReferencePerformer(
    performerName: "Natalie Monroe"
    sources: ["data18", "neo4j", "stash"]
  ) {
    performerName
    sources {
      data18 {
        found
        url
      }
      neo4j {
        found
        sceneCount
      }
    }
  }
}
```

## Testing & Evaluation

### Test Cases

```python
test_cases = [
    TestCase(
        test_id="forum_001",
        test_type="forum",
        input_data={
            "thread_url": "http://www.planetsuzy.org/showthread.php?p=23377199"
        },
        expected_result={
            "images_found": 10,
            "tags": ["Natalie Monroe", "braces"]
        }
    ),
    TestCase(
        test_id="wanted_001",
        test_type="wanted",
        input_data={
            "performer_name": "Natalie Monroe",
            "source_url": "https://www.18eighteen.com/..."
        },
        expected_result={
            "created": True,
            "source_type": "18eighteen"
        }
    )
]
```

### Benchmark Report

```json
{
  "timestamp": "2025-01-XX...",
  "summary": {
    "total_tests": 10,
    "passed_tests": 8,
    "accuracy": 0.80,
    "average_confidence": 0.85,
    "source_breakdown": {
      "stash": 5,
      "data18": 2,
      "forum": 1
    }
  }
}
```

## Neo4j Ontology

### Complete Graph Structure

```
(Forum {url: "planetsuzy.org"})
  -[:HAS_THREAD]-> (ForumThread)
    -[:HAS_IMAGE]-> (Image)
    -[:HAS_TAG]-> (Tag)

(Performer {name: "Natalie Monroe"})
  -[:WANTED]-> (Wanted {source_type: "18eighteen"})
  -[:DISCUSSED_IN]-> (ForumThread)
  -[:APPEARS_IN]-> (Scene)

(Wanted)-[:DISCUSSED_IN]->(ForumThread)
```

## Usage Examples

### Parse Thread and Index Images

```python
from feed.services.forum_parser import VBulletinParser
from feed.services.forum_storage import ForumStorage

parser = VBulletinParser("http://www.planetsuzy.org")
storage = ForumStorage(neo4j)

thread = parser.parse_thread(thread_url)
storage.store_thread(thread, index_images=True)
```

### Track Wanted Content

```python
from feed.services.wanted_metadata_tracker import WantedMetadataTracker

tracker = WantedMetadataTracker(neo4j)

wanted_id = tracker.create_wanted_entry(
    performer_name="Natalie Monroe",
    source_url="https://www.18eighteen.com/...",
    source_type="18eighteen"
)
```

### Cross-Verify Sources

```python
from feed.services.cross_source_verifier import CrossSourceVerifier

verifier = CrossSourceVerifier(neo4j)

mapping = verifier.check_18eighteen_to_data18_mapping(
    "Natalie Monroe",
    "https://www.18eighteen.com/..."
)
```

## Evaluation Workflow

1. **Create Test Cases**: Define expected results
2. **Run Tests**: Execute reverse lookups
3. **Measure Metrics**: Accuracy, confidence, time
4. **Generate Report**: JSON benchmark report
5. **Track Progress**: Monitor improvements over time

## Next Steps

1. **Enhanced Parsing**: Support more forum platforms
2. **Image Similarity**: Use thread images for reverse search
3. **Automated Wanted Tracking**: Auto-detect missing content
4. **Advanced Cross-Reference**: ML-based matching
5. **Real-time Evaluation**: Continuous benchmarking




