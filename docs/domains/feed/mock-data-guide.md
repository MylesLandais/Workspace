# Mock Data Guide for Frontend Developers

This guide explains how to use mock data for local frontend development and testing.

## Quick Start

### Enable Mock Mode

Mock mode is enabled by default in development. The app automatically uses MSW (Mock Service Worker) to intercept GraphQL requests when `PUBLIC_GRAPHQL_MOCK=true`:

```bash
# In docker-compose.yml (already configured)
PUBLIC_GRAPHQL_MOCK=true
```

### Verify Mock Data is Loading

1. Open the app at `http://localhost:4321`
2. Open browser DevTools (F12) → Console tab
3. Look for `[MSW]` logs showing mock data loading:
   ```
   [MSW] ========== Starting mock data load ==========
   [MSW] [1/9] Loading SelenaGomez...
   [MSW] ✓ Loaded 32 items from SelenaGomez
   ```

## Understanding Mock Data Structure

### Data Location

Mock data lives in `/temp/mock_data/` directory, mounted at `/app/public/temp/mock_data/` in the container.

Each subreddit has its own directory:
```
/temp/mock_data/
  ├── SelenaGomez/
  │   ├── json/
  │   │   └── SelenaGomez_posts.json
  │   └── images/ (optional, not loaded by default)
  ├── TaylorSwift/
  │   └── json/
  │       └── TaylorSwift_posts.json
  └── ... (65+ subreddits total)
```

### Available Subreddits

See `app/frontend/src/lib/mock-data/loader.ts` → `SUBREDDITS` array for the complete list.

Current priority subreddits (loaded first for fast startup):
- `SelenaGomez`
- `TaylorSwift`, `TaylorSwiftCandids`, `TaylorSwiftMidriff`, `Taylorhillfantasy`
- `ArianaGrande`
- `Pokimane`
- `SydneySweeney`
- `AddisonRae`

### Data Format

Each subreddit JSON file contains:
```json
{
  "subreddit": "SelenaGomez",
  "export_date": "2025-12-23T15:35:08.556260",
  "total_posts": 100,
  "images_downloaded": 32,
  "posts": [
    {
      "id": "1psbm9y",
      "title": "Post title",
      "score": 345,
      "created_utc": "2025-12-21T17:16:06.000000000+00:00",
      "image_url": "https://i.redd.it/...",
      "is_image": true,
      "author": "username",
      ...
    }
  ]
}
```

## Using Mock Data in Development

### Default Behavior

When mock mode is enabled, the app:
1. Intercepts GraphQL queries via MSW
2. Loads data from `/temp/mock_data/` on first request
3. Caches loaded data for subsequent requests
4. Returns data in GraphQL schema format

### Filter Presets

Pre-configured filter presets are available in the sidebar:

- **"Pop Queenz ✨"**: Shows posts from Taylor Swift and Selena Gomez subreddits
- **"Linux Threads 🐧"**: Search query for "linux" (placeholder for future Linux data)

Select these from the "MY BOARDS" section in the sidebar to test filtering.

### Testing Different Scenarios

Currently, mock data loads a subset of subreddits for performance. To test with more data:

1. **Edit loader priority**: Modify `prioritySubreddits` array in `app/frontend/src/lib/graphql/mocks/handlers.ts`
2. **Load all subreddits**: Change to use `loadAllMedia()` instead of priority subset
3. **Custom dataset**: Create your own JSON files and add subreddit names to `SUBREDDITS` array

## Debugging Mock Data Issues

### Check MSW Initialization

Look for these logs in the browser console:
```
[MSW] Mock mode enabled, initializing MSW...
[MSW] ========== Setting up MSW mock server ==========
[MSW] ========== Mock server started successfully ==========
```

If these don't appear, MSW isn't starting. Check:
- `PUBLIC_GRAPHQL_MOCK=true` is set
- `mockServiceWorker.js` exists in `app/frontend/public/`
- Browser console for errors

### Check Data Loading

Look for detailed loading logs:
```
[MSW] ========== Starting mock data load ==========
[MSW] Priority subreddits: ['SelenaGomez', 'TaylorSwift', ...]
[MSW] [1/9] Loading SelenaGomez...
[MSW] Fetch response for SelenaGomez: { status: 200, ... }
[MSW] ✓ Loaded 32 items from SelenaGomez (total so far: 32)
```

If loading fails, check:
- Files exist in `/temp/mock_data/{subreddit}/json/`
- File names match pattern: `{subreddit}_posts.json`
- JSON files are valid (no syntax errors)

### Check GraphQL Queries

When a query executes, you should see:
```
[MSW] ========== FeedWithFilters handler called ==========
[MSW] Request details: { variables: {...}, operationName: "FeedWithFilters" }
[MSW] Loading mock data...
[MSW] ========== FeedWithFilters response ready ==========
```

If queries aren't being intercepted:
- Check Network tab - requests should NOT go to backend URL
- Verify MSW is intercepting (requests should show "MSW" in Network tab)
- Check query operation name matches handler name

## Extending Mock Data

### Adding New Subreddits

1. Add JSON file to `/temp/mock_data/{SubredditName}/json/{SubredditName}_posts.json`
2. Add subreddit name to `SUBREDDITS` array in `app/frontend/src/lib/mock-data/loader.ts`
3. Optionally add creator mapping in `getCreatorNameForSubreddit()` function

### Creating Filter Presets

Edit `app/frontend/src/lib/bunny/services/fixtures.ts`:

```typescript
export const DEMO_BOARDS: SavedBoard[] = [
  {
    id: 'my-custom-board',
    name: 'My Custom Feed',
    filters: {
      persons: ['Taylor Swift'],  // Filter by creator
      sources: [],                 // Or by subreddit: ['r/TaylorSwift']
      searchQuery: 'concert'       // Or by search term
    },
    createdAt: Date.now()
  }
];
```

### Generating Pre-transformed GraphQL Data

Pre-transformed GraphQL data provides faster loading and guaranteed schema compliance:

```bash
# Generate pre-transformed datasets
npm run generate-mock-data          # Medium dataset (default)
npm run generate-mock-data:small    # Small dataset (~100-500 posts)
npm run generate-mock-data:medium   # Medium dataset (~1k-2k posts)
npm run generate-mock-data:large    # Large dataset (~6k+ posts)
```

Generated files are stored in `public/temp/graphql-mock-data/`:
- `feed-{size}.json` - GraphQL FeedConnection format
- `feed-{size}-metadata.json` - Generation metadata

MSW handlers automatically use pre-transformed data when available, falling back to runtime transformation if not found.

See [GraphQL Mock Data Generation](./graphql-mock-data-generation.md) for details.

## Performance Considerations

### Initial Load Time

Loading all 65+ subreddits can take 10-30 seconds. Current implementation:
- Loads only priority subreddits initially (faster startup)
- Uses lazy loading (data loads on first query)
- Caches results (subsequent queries are instant)

### Optimizing Load Times

If initial load is too slow:
1. Reduce `prioritySubreddits` array size
2. Implement chunked/parallel loading (future enhancement)
3. Pre-generate and cache transformed data (future enhancement)

### Memory Usage

Large datasets (10k+ posts) may impact browser memory:
- Monitor memory in DevTools → Memory tab
- Consider pagination limits in queries
- Implement virtual scrolling for large lists (already in place)

## Integration with Testing

### Component Tests

Mock data can be used in component tests:

```typescript
import { render } from '@testing-library/react';
import { MockedProvider } from '@apollo/client/testing';
import { handlers } from '../lib/graphql/mocks/handlers';

// Use MSW handlers in tests
import { setupServer } from 'msw/node';
const server = setupServer(...handlers);
```

### Storybook Stories

Future enhancement: Wire mocked GraphQL provider into Storybook:

```typescript
// Storybook story example
export default {
  decorators: [
    (Story) => (
      <MockedProvider>
        <Story />
      </MockedProvider>
    )
  ]
};
```

### E2E Tests (Playwright/Cypress)

Future enhancement: Select scenarios via environment variables:

```bash
SCENARIO=massive-feed npm run test:e2e
```

## Troubleshooting

### "Curating your feed..." Never Finishes

1. Check browser console for `[MSW]` errors
2. Verify MSW is intercepting requests (Network tab)
3. Check if data files are accessible (try loading JSON directly in browser)
4. Look for infinite loops in console logs

### No Data Appears

1. Verify mock data files exist and are valid JSON
2. Check creator mappings in `getCreatorNameForSubreddit()` match filter selections
3. Verify subreddit names match exactly (case-sensitive)
4. Check filter logic in `filterFeedItems()` function

### Slow Performance

1. Reduce number of subreddits in `prioritySubreddits`
2. Check Network tab for large payloads
3. Verify caching is working (subsequent queries should be instant)
4. Consider implementing pagination limits

### MSW Not Starting

1. Check `PUBLIC_GRAPHQL_MOCK=true` is set
2. Verify `mockServiceWorker.js` exists in `public/` directory
3. Check browser console for Service Worker errors
4. Try hard refresh (Ctrl+Shift+R) to re-register Service Worker

## Best Practices

1. **Keep Schema in Sync**: When GraphQL schema changes, update mock handlers accordingly
2. **Use Real Data**: Prefer real scraped data over synthetic data for realistic testing
3. **Test Edge Cases**: Create scenarios for empty states, errors, and slow responses
4. **Monitor Performance**: Watch for memory leaks and slow load times with large datasets
5. **Document Scenarios**: Document custom scenarios and filter presets for the team

## References

- [ADR: Mock Data Strategy](../architecture/adr/mock-data-strategy.md)
- [GraphQL Mock Data Generation](./graphql-mock-data-generation.md) - Pre-transformation details
- [Mock Server Architecture](./mock-server-architecture.md) - Architecture overview and comparison
- [GraphQL Schema](../../interfaces/graphql/schema.graphql)
- [MSW Documentation](https://mswjs.io/)
- [Mock Data Loader](../../../app/frontend/src/lib/mock-data/loader.ts)

