# Reverse Image Search - GraphQL API Documentation

## Overview

The reverse image search functionality is now available through GraphQL, providing a client-server architecture for:
- Internal lookup against spider crawling data
- Public search tooling (external APIs)
- Ontology integration (garment styles, products)

## GraphQL Endpoint

The GraphQL API is available at the standard GraphQL endpoint (configured in your server setup).

## Queries

### 1. Check if Image Already Crawled

Fast lookup to check if an image URL exists in the database.

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
    hashes {
      sha256
      dhash
    }
  }
}
```

**Response**:
```json
{
  "data": {
    "checkImageCrawled": {
      "found": true,
      "matches": [
        {
          "matchType": "url",
          "confidence": 1.0,
          "sourcePostId": "abc123",
          "sourceProductId": null
        }
      ],
      "hashes": {
        "sha256": "abc123...",
        "dhash": "def456"
      }
    }
  }
}
```

### 2. Find Original Source

Find where an image first appeared in the database.

```graphql
query {
  findImageSource(
    imageUrl: "https://i.redd.it/example.jpg"
    includeExternal: false
  ) {
    found
    matches {
      imageUrl
      matchType
      sourcePostId
      metadata
    }
  }
}
```

### 3. Find Exact Matches

Find all occurrences of an image using multiple strategies.

```graphql
query {
  findExactMatches(
    imageUrl: "https://i.redd.it/example.jpg"
    includeExternal: false
  ) {
    found
    matches {
      matchType
      confidence
      imageUrl
      sourcePostId
      sourceProductId
    }
    hashes {
      sha256
      dhash
    }
    embeddingComputed
  }
}
```

### 4. Find Similar Images

Visual similarity search using CLIP embeddings.

```graphql
query {
  findSimilarImages(
    imageUrl: "https://i.redd.it/example.jpg"
    minSimilarity: 0.85
    limit: 10
  ) {
    imageUrl
    matches {
      imageUrl
      matchType
      confidence
      sourcePostId
    }
    totalFound
  }
}
```

### 5. Check Image Status

Check if an image was missed and needs recovery.

```graphql
query {
  checkImageStatus(imageUrl: "https://i.redd.it/example.jpg") {
    found
    recoveryNeeded
    matches {
      matchType
      confidence
      sourcePostId
    }
    similarImages {
      imageUrl
      confidence
      sourcePostId
    }
  }
}
```

### 6. Public Image Search

Search external reverse image search APIs.

```graphql
query {
  publicImageSearch(
    imageUrl: "https://i.redd.it/example.jpg"
    providers: [TINEYE, GOOGLE_IMAGES]
  ) {
    imageUrl
    providers {
      provider
      results {
        imageUrl
        matchType
        confidence
      }
      totalResults
    }
  }
}
```

### 7. Find Image Matches with Ontology

Find matches with garment style integration.

```graphql
query {
  findImageMatches(imageUrl: "https://i.redd.it/example.jpg") {
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
      confidence
      matchedProducts
    }
  }
}
```

## Mutations

### 1. Recover Post

Manually ingest a missed Reddit post.

```graphql
mutation {
  recoverPost(postUrl: "https://reddit.com/r/example/comments/abc123/") {
    success
    postId
    imagesFound
    imagesIndexed
    error
  }
}
```

### 2. Index Image

Index an image for future search.

```graphql
mutation {
  indexImage(imageUrl: "https://i.redd.it/example.jpg") {
    success
    hashesStored
    embeddingStored
    error
  }
}
```

## Type Definitions

### ImageLookupResultType

```graphql
type ImageLookupResultType {
  imageUrl: String!
  found: Boolean!
  matches: [ImageMatchType!]!
  hashes: ImageHashes
  embeddingComputed: Boolean!
}
```

### ImageMatchType

```graphql
type ImageMatchType {
  imageUrl: String!
  matchType: String!  # 'url', 'sha256', 'dhash', 'vector', 'external'
  confidence: Float!
  sourcePostId: String
  sourceCommentId: String
  sourceProductId: String
  metadata: String  # JSON string
}
```

### ImageStatusResult

```graphql
type ImageStatusResult {
  imageUrl: String!
  found: Boolean!
  matchType: String
  matches: [ImageMatchType!]!
  recoveryNeeded: Boolean!
  similarImages: [ImageMatchType!]!
}
```

### GarmentStyleMatch

```graphql
type GarmentStyleMatch {
  uuid: String!
  name: String!
  features: [String!]!
  confidence: Float!
  matchedProducts: [String!]!
}
```

## Integration with Existing Schema

The image search queries are integrated into the main GraphQL schema alongside:
- E-commerce queries (products, garment styles)
- Creator queries (creators, handles, media)
- imageboard queries (threads, posts, images)
- Feed queries (posts, subreddits)

## Example Client Usage

### Python Client

```python
import requests

# GraphQL query
query = """
query {
  checkImageCrawled(imageUrl: "https://i.redd.it/example.jpg") {
    found
    matches {
      matchType
      confidence
      sourcePostId
    }
  }
}
"""

response = requests.post(
    "http://localhost:8000/graphql",
    json={"query": query}
)

data = response.json()
print(data["data"]["checkImageCrawled"])
```

### JavaScript/TypeScript Client

```typescript
import { GraphQLClient } from 'graphql-request';

const client = new GraphQLClient('http://localhost:8000/graphql');

const query = `
  query {
    checkImageCrawled(imageUrl: "https://i.redd.it/example.jpg") {
      found
      matches {
        matchType
        confidence
        sourcePostId
      }
    }
  }
`;

const data = await client.request(query);
console.log(data.checkImageCrawled);
```

## Error Handling

All queries return standard GraphQL error format:

```json
{
  "errors": [
    {
      "message": "Image URL is required",
      "path": ["checkImageCrawled"]
    }
  ]
}
```

## Performance Considerations

1. **URL Lookup**: ~1-5ms (fastest)
2. **Hash Lookup**: ~10-50ms (medium)
3. **Vector Search**: ~50-200ms (slowest)
4. **External APIs**: ~500-2000ms (depends on provider)

Use `checkImageCrawled` for fastest results, `findExactMatches` for comprehensive search.

## Authentication

Currently, all queries are public. Add authentication middleware as needed for production use.

## Future Enhancements

1. **Rate Limiting**: Per-user rate limits
2. **Caching**: Cache frequent queries
3. **Batch Operations**: Check multiple images at once
4. **Webhooks**: Notify on new matches
5. **Analytics**: Track search patterns




