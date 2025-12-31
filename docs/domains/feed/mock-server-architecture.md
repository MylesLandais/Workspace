# Mock GraphQL Server Architecture

## Overview

Our mock data architecture bridges raw Reddit JSON data with GraphQL schema-compliant responses, enabling frontend development without backend dependencies.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (React/Astro)                     │
│         Apollo Client + GraphQL Queries                 │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ GraphQL over HTTP
                   │
┌──────────────────▼──────────────────────────────────────┐
│         Mock GraphQL Server (MSW)                       │
│   - Browser-based (no separate server process)          │
│   - Intercepts GraphQL requests                         │
│   - Schema-compliant responses                          │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌────────▼────────┐
│ Pre-transformed│   │ Runtime         │
│ GraphQL Data   │   │ Transformation  │
│ (Preferred)    │   │ (Fallback)      │
└───────┬────────┘   └────────┬────────┘
        │                     │
        │           ┌─────────▼──────────┐
        │           │ Raw Reddit JSON    │
        │           │ (/temp/mock_data/) │
        │           └────────────────────┘
        │
┌───────▼───────────────────────────────┐
│   Data Generation Script              │
│   npm run generate-mock-data          │
│   - Reads raw JSON                    │
│   - Transforms to GraphQL format      │
│   - Outputs to /public/temp/          │
└───────────────────────────────────────┘
```

## Comparison: MSW vs Standalone Mock Server

### Current Approach: MSW (Mock Service Worker)

**Pros:**
- ✅ No separate server process needed
- ✅ Works in browser, same environment as app
- ✅ Simple setup, no additional infrastructure
- ✅ Service Worker intercepts requests transparently
- ✅ Perfect for frontend-only development

**Cons:**
- ❌ Limited to browser environment
- ❌ Can't serve static files directly (must use public/ directory)
- ❌ Less control over advanced GraphQL features

### Alternative: Standalone Mock Server (Node.js)

**Pros:**
- ✅ Full GraphQL schema introspection
- ✅ Can serve static assets (images, etc.) directly
- ✅ More control over resolvers and mocks
- ✅ Can use GraphQL Tools for schema-based mocking
- ✅ Works for E2E tests that need server process

**Cons:**
- ❌ Requires separate server process
- ❌ More complex setup and maintenance
- ❌ Different environment from browser

### Recommendation

**For Development**: Continue using MSW (current approach)
- Simple, works great for frontend development
- No additional infrastructure needed
- Pre-transformed data provides performance benefits

**For Advanced Testing**: Consider adding optional standalone server
- Useful for E2E tests (Playwright/Cypress)
- Better for scenario-based testing
- Can use GraphQL Tools for schema-based mocking

## Data Flow

### 1. Raw Data Source

Location: `/temp/mock_data/`

Structure:
```
/temp/mock_data/
  ├── SelenaGomez/
  │   ├── json/
  │   │   └── SelenaGomez_posts.json
  │   └── images/
  │       └── *.jpg
  ├── TaylorSwift/
  │   └── ...
```

### 2. Data Generation (Build Time)

Script: `scripts/generate-graphql-mock-data.ts`

```bash
npm run generate-mock-data:medium
```

Process:
1. Reads raw Reddit JSON files
2. Transforms to GraphQL schema format
3. Deduplicates and sorts
4. Outputs to `public/temp/graphql-mock-data/`

### 3. Runtime Loading (MSW Handlers)

Location: `src/lib/graphql/mocks/handlers.ts`

Flow:
1. Try to load pre-transformed GraphQL data (fast path)
2. If not available, load raw JSON and transform (fallback)
3. Apply filters (persons, sources, search query)
4. Return GraphQL-compliant response

### 4. Data Factories (Future Enhancement)

For generating large datasets deterministically:

```typescript
import { createFeed, Scenarios } from './article-factory';

// Generate 5000 articles from templates
const largeFeed = createFeed(templates, 5000);

// Scenario-based generation
const emptyFeed = Scenarios.emptyFeed();
const recentArticles = Scenarios.recentArticles(templates);
```

## Scenario-Based Testing

### Current State

MSW handlers can be extended to support scenarios via query variables or headers:

```typescript
// In handlers.ts
graphql.query('FeedWithFilters', async (req, res, ctx) => {
  const scenario = req.variables?.scenario || req.headers.get('x-test-scenario');
  
  if (scenario === 'empty-feed') {
    return res(ctx.data({ feed: { edges: [], pageInfo: { hasNextPage: false, endCursor: null } } }));
  }
  
  if (scenario === 'large-feed') {
    const largeData = await loadPreTransformedMockData('large');
    // Return large dataset
  }
  
  // Normal behavior
});
```

### Future: Standalone Server Scenarios

For E2E tests, a standalone server could support scenarios:

```javascript
// mock-server.ts (future)
const SCENARIOS = {
  'empty-feed': () => ({ articles: [], unreadCount: 0, hasMore: false }),
  'large-feed': () => ({ articles: createFeed(5000), unreadCount: 3200, hasMore: true }),
  'slow-response': async () => {
    await new Promise(resolve => setTimeout(resolve, 3000));
    return { articles: createFeed(50), unreadCount: 50, hasMore: true };
  },
};
```

## Image Assets

### Current Approach

Images are served from `/temp/mock_data/{subreddit}/images/` via:
- Docker volume mount: `../../temp:/app/public/temp:ro`
- Accessible at: `/temp/mock_data/{subreddit}/images/{filename}`

### Future Enhancement: Organized Fixtures

Organize images in a fixtures structure:

```
/public/fixtures/
  /images
    - article-001.jpg
    - article-002.jpg
    - feed-icon-techcrunch.png
  /data
    - subscriptions.json
    - articles-base.json
```

Served via:
- Express static (if using standalone server)
- Or public/ directory (current MSW approach)

## Schema-Based Mocking

### Current Approach

- Pre-transform data to match GraphQL schema exactly
- Handlers return schema-compliant responses
- Manual transformation from raw JSON

### Future: GraphQL Tools Integration

Could use `@graphql-tools/mock` for automatic schema-based mocking:

```javascript
import { makeExecutableSchema } from '@graphql-tools/schema';
import { addMocksToSchema } from '@graphql-tools/mock';
import { schema } from './schema.graphql';

const mockedSchema = addMocksToSchema({ schema });

// Automatic mocking based on schema types
// Override specific resolvers with real data
```

## Recommendations

### Short Term (Keep Current Approach)

1. ✅ Continue using MSW for development
2. ✅ Use pre-transformed GraphQL data for performance
3. ✅ Maintain data generation script
4. ✅ Document fixture organization

### Medium Term (Enhancements)

1. 🔄 Add data factories for deterministic generation
2. 🔄 Add scenario support to MSW handlers
3. 🔄 Better organize fixture images
4. 🔄 Add schema validation for generated data

### Long Term (Optional)

1. 📋 Consider standalone mock server for advanced E2E testing
2. 📋 Integrate GraphQL Tools for schema-based mocking
3. 📋 Add fixture management UI/tools
4. 📋 CI/CD integration for mock data generation

## Related Documentation

- [Mock Data Guide](./mock-data-guide.md) - Using mock data in development
- [GraphQL Mock Data Generation](./graphql-mock-data-generation.md) - Pre-transformation details
- [ADR: Mock Data Strategy](../architecture/adr/mock-data-strategy.md) - Architecture decision




