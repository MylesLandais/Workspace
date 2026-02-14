# Reverse Image Search - User Story & Architecture

## User Story

**As a** content curator or feed manager  
**I want to** search for images using reverse image search across multiple sources  
**So that** I can:
- Check if an image has already been crawled by our spider
- Find the original source of an image
- Discover all occurrences of an image across platforms
- Find visually similar images for content discovery
- Match images to our garment/product ontology

## Use Cases

### 1. Feed Management: Check if Image Already Crawled

**Scenario**: Before processing a new post, check if its images are already in the database.

**User Flow**:
1. User provides an image URL
2. System checks:
   - URL lookup (fastest)
   - Hash-based lookup (exact/near-duplicates)
   - Vector similarity search (visual matches)
3. Returns matches with source information (post ID, product ID, etc.)

**GraphQL Query**:
```graphql
query {
  checkImageCrawled(imageUrl: "https://i.redd.it/example.jpg") {
    found
    matches {
      matchType
      confidence
      sourcePostId
      sourceProductId
    }
  }
}
```

### 2. Source Attribution: Find Original Source

**Scenario**: Find where an image first appeared in our database.

**User Flow**:
1. User provides an image URL
2. System finds earliest occurrence
3. Returns original source with timestamp

**GraphQL Query**:
```graphql
query {
  findImageSource(imageUrl: "https://i.redd.it/example.jpg", includeExternal: false) {
    found
    earliestMatch {
      imageUrl
      sourcePostId
      firstSeen
    }
  }
}
```

### 3. Exact Match Discovery: Find All Occurrences

**Scenario**: Find all places where an image appears (exact and near-exact matches).

**User Flow**:
1. User provides an image URL
2. System searches using:
   - SHA-256 hash (exact duplicates)
   - dHash (near-duplicates: cropped, resized)
   - CLIP embeddings (visually similar)
   - External APIs (TinEye, Google Images) - optional
3. Returns all matches with confidence scores

**GraphQL Query**:
```graphql
query {
  findExactMatches(
    imageUrl: "https://i.redd.it/example.jpg"
    includeExternal: false
  ) {
    found
    hashes {
      sha256
      dhash
    }
    matches {
      matchType
      confidence
      imageUrl
      sourcePostId
      sourceProductId
    }
  }
}
```

### 4. Visual Similarity Search

**Scenario**: Find visually similar images for content discovery.

**User Flow**:
1. User provides an image URL
2. System computes CLIP embedding
3. Searches vector database for similar images
4. Returns matches sorted by similarity score

**GraphQL Query**:
```graphql
query {
  findSimilarImages(
    imageUrl: "https://i.redd.it/example.jpg"
    minSimilarity: 0.85
    limit: 10
  ) {
    matches {
      imageUrl
      similarity
      sourcePostId
      sourceProductId
    }
  }
}
```

### 5. Ontology Integration: Match to Garment Styles

**Scenario**: Match an image to garment styles in our ontology.

**User Flow**:
1. User provides an image URL
2. System:
   - Finds image in database
   - Queries garment style relationships
   - Returns matched styles with confidence

**GraphQL Query**:
```graphql
query {
  findImageMatches(
    imageUrl: "https://i.redd.it/example.jpg"
  ) {
    found
    matches {
      matchType
      confidence
      sourceProductId
    }
    garmentStyles {
      uuid
      name
      features
      matchedProducts {
        id
        title
        price
      }
    }
  }
}
```

### 6. Public Search Integration

**Scenario**: Search external reverse image search APIs (TinEye, Google Images).

**User Flow**:
1. User provides an image URL
2. System queries external APIs
3. Returns results from external sources

**GraphQL Query**:
```graphql
query {
  publicImageSearch(
    imageUrl: "https://i.redd.it/example.jpg"
    providers: [TINEYE, GOOGLE_IMAGES]
  ) {
    provider
    results {
      url
      title
      source
      confidence
    }
  }
}
```

### 7. Spider Recovery: Check for Missed Images

**Scenario**: Check if an image was missed due to spider downtime.

**User Flow**:
1. User provides an image URL
2. System checks database
3. If not found, suggests recovery options
4. Optionally recovers post containing image

**GraphQL Query**:
```graphql
query {
  checkImageStatus(imageUrl: "https://i.redd.it/example.jpg") {
    found
    recoveryNeeded
    similarImages {
      url
      similarity
      sourcePostId
    }
  }
}

mutation {
  recoverPost(postUrl: "https://reddit.com/r/example/comments/abc123/") {
    success
    postId
    imagesFound
    imagesIndexed
  }
}
```

## Architecture

### Client-Server GraphQL Architecture

```
┌─────────────────┐
│   GraphQL API   │
│   (Strawberry)  │
└────────┬────────┘
         │
         ├─── ReverseImageSearch Service
         │    ├─── URL Lookup (Neo4j)
         │    ├─── Hash Lookup (Neo4j)
         │    └─── Vector Search (Valkey)
         │
         ├─── SpiderRecovery Service
         │    └─── Post Recovery
         │
         ├─── Public Search Service
         │    ├─── TinEye API
         │    ├─── Google Images API
         │    └─── Other providers
         │
         └─── Ontology Service
              └─── Garment Style Matching
```

### Data Sources

1. **Internal (Spider Data)**:
   - Neo4j: Image nodes, Post nodes, Product nodes
   - Valkey: CLIP embeddings for vector search
   - Image hashes (SHA-256, dHash)

2. **External (Public Search)**:
   - TinEye API
   - Google Images Reverse Search
   - Bing Visual Search (optional)

3. **Ontology**:
   - Garment styles
   - Product relationships
   - Feature matching

### GraphQL Schema Structure

```graphql
type Query {
  # Image lookup queries
  checkImageCrawled(imageUrl: String!): ImageLookupResult!
  findImageSource(imageUrl: String!, includeExternal: Boolean): ImageLookupResult!
  findExactMatches(imageUrl: String!, includeExternal: Boolean): ImageLookupResult!
  findSimilarImages(imageUrl: String!, minSimilarity: Float, limit: Int): SimilarImageResult!
  checkImageStatus(imageUrl: String!): ImageStatusResult!
  
  # Public search
  publicImageSearch(imageUrl: String!, providers: [ImageSearchProvider!]): PublicSearchResult!
  
  # Ontology integration
  findImageMatches(imageUrl: String!): ImageMatchResult!
  findImagesByStyle(styleUuid: String!): [Image!]!
}

type Mutation {
  # Recovery operations
  recoverPost(postUrl: String!): RecoveryResult!
  indexImage(imageUrl: String!): IndexResult!
}
```

## Implementation Status

- ✅ Reverse Image Search Service (Python)
- ✅ Spider Recovery Service (Python)
- ⏳ GraphQL Schema (In Progress)
- ⏳ Public Search Integration (Planned)
- ⏳ Ontology Integration (Planned)

## Next Steps

1. Create GraphQL schema file (`image_search_schema.py`)
2. Add resolvers for all queries
3. Integrate with existing GraphQL server
4. Add public search API integrations
5. Connect to garment ontology
6. Add authentication/authorization
7. Create frontend client examples




