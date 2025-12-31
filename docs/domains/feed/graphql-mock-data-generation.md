# GraphQL Mock Data Generation

## Overview

We've implemented a system to pre-transform raw Reddit JSON data into GraphQL schema format, providing faster loading times and guaranteed schema compliance.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Raw Reddit JSON (/temp/mock_data/)            │
│   - Reddit post format                                  │
│   - Multiple subreddit JSON files                       │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ [Generation Script]
                   │ npm run generate-mock-data
                   │
┌──────────────────▼──────────────────────────────────────┐
│   Pre-transformed GraphQL Data                          │
│   (/public/temp/graphql-mock-data/)                     │
│   - Matches GraphQL schema exactly                      │
│   - feed-small.json, feed-medium.json, feed-large.json  │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ [MSW Handlers]
                   │ loadPreTransformedMockData()
                   │
┌──────────────────▼──────────────────────────────────────┐
│           Frontend GraphQL Queries                      │
│   - Fast loading (no runtime transformation)            │
│   - Schema-compliant responses                          │
└─────────────────────────────────────────────────────────┘
```

## Benefits

1. **Performance**: Pre-transformed data loads faster (no runtime transformation)
2. **Schema Compliance**: Data matches GraphQL schema exactly, catching schema mismatches early
3. **Testing**: Same data structure as real API, making frontend tests more reliable
4. **Flexibility**: Fallback to runtime transformation if pre-transformed data unavailable
5. **Development Speed**: Frontend developers can work without backend dependencies

## Usage

### Generate Pre-transformed Data

```bash
# Generate medium dataset (default)
npm run generate-mock-data

# Generate specific sizes
npm run generate-mock-data:small   # ~100-500 posts (priority subreddits)
npm run generate-mock-data:medium  # ~1k-2k posts (priority + some more)
npm run generate-mock-data:large   # ~6k+ posts (all subreddits)
```

### Generated Files

The script generates files in `public/temp/graphql-mock-data/`:

- `feed-{size}.json` - GraphQL FeedConnection format
- `feed-{size}-metadata.json` - Generation metadata (counts, timestamps, etc.)

### MSW Handlers

MSW handlers automatically:
1. Try to load pre-transformed data first
2. Fall back to runtime transformation if pre-transformed data not available
3. Log which method is being used

### Example Output

```json
{
  "edges": [
    {
      "node": {
        "id": "abc123",
        "title": "Post title",
        "imageUrl": "https://...",
        "sourceUrl": "https://reddit.com/...",
        "publishDate": "2025-12-24T12:00:00.000Z",
        "score": 1234,
        "subreddit": { "name": "TaylorSwift" },
        "author": { "username": "user123" },
        "platform": "REDDIT",
        "handle": { "name": "r/TaylorSwift", "handle": "r/TaylorSwift" },
        "mediaType": "IMAGE",
        "viewCount": 0
      },
      "cursor": "2025-12-24T12:00:00.000Z"
    }
  ],
  "pageInfo": {
    "hasNextPage": true,
    "endCursor": "2025-12-24T12:00:00.000Z"
  }
}
```

## Data Transformation

The generation script transforms raw Reddit JSON into GraphQL format:

**Raw Reddit Format**:
```json
{
  "id": "abc123",
  "title": "Post title",
  "score": 1234,
  "created_utc": "1735036800",
  "image_url": "https://...",
  "is_image": true,
  "author": "user123",
  "subreddit": "TaylorSwift"
}
```

**GraphQL Format**:
```json
{
  "id": "abc123",
  "title": "Post title",
  "imageUrl": "https://...",
  "sourceUrl": "https://reddit.com/r/TaylorSwift/comments/abc123",
  "publishDate": "2025-12-24T12:00:00.000Z",
  "score": 1234,
  "subreddit": { "name": "TaylorSwift" },
  "author": { "username": "user123" },
  "platform": "REDDIT",
  "handle": { "name": "r/TaylorSwift", "handle": "r/TaylorSwift" },
  "mediaType": "IMAGE"
}
```

## When to Regenerate

Regenerate pre-transformed data when:
- Raw mock data is updated (new subreddits, new posts)
- GraphQL schema changes (field names, types, structure)
- You want to test with different dataset sizes

## Implementation Details

### Generation Script

Location: `app/frontend/scripts/generate-graphql-mock-data.ts`

- Reads raw Reddit JSON from `/temp/mock_data/`
- Transforms to GraphQL schema format
- Supports multiple dataset sizes
- Deduplicates posts by ID
- Sorts by publish date (newest first)

### MSW Integration

Location: `app/frontend/src/lib/graphql/mocks/`

- **pre-transformed-loader.ts**: Loads pre-transformed JSON files
- **handlers.ts**: Updated to prefer pre-transformed data, fallback to runtime transformation

### Fallback Behavior

If pre-transformed data is not available, MSW handlers automatically fall back to:
1. Loading raw Reddit JSON files
2. Runtime transformation using existing `loader.ts` logic
3. Filtering and formatting for GraphQL responses

This ensures the app always works, even if pre-transformed data hasn't been generated yet.

## Future Enhancements

1. **Scenario-based Datasets**: Generate datasets for specific scenarios (empty feeds, error states)
2. **Incremental Updates**: Only regenerate changed subreddits
3. **Schema Validation**: Validate generated data against GraphQL schema
4. **CI/CD Integration**: Automatically generate mock data as part of build process
5. **Data Versioning**: Track schema versions and regenerate when schema changes

## Related Documentation

- [Mock Data Guide](./mock-data-guide.md) - Using mock data in development
- [ADR: Mock Data Strategy](../architecture/adr/mock-data-strategy.md) - Architecture decision
- [Mock Data User Stories](./mock-data-user-stories.md) - User stories




