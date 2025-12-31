# Mock Data Setup for Frontend Development

This document explains how to use mock data for frontend development without requiring a working backend.

## Overview

The frontend uses MSW (Mock Service Worker) to intercept GraphQL requests and return mock data from `/temp/mock_data/`. This allows you to:

- Develop and test the frontend without a backend
- Use real data structures from exported Reddit posts
- Test filtering, search, and other features with realistic data

## Configuration

Mock mode is controlled by the `PUBLIC_GRAPHQL_MOCK` environment variable:

- `PUBLIC_GRAPHQL_MOCK=true` - Use MSW mocks (no backend needed)
- `PUBLIC_GRAPHQL_MOCK=false` - Connect to real GraphQL backend

The setting is in `docker-compose.yml`:

```yaml
environment:
  - PUBLIC_GRAPHQL_MOCK=true  # or false
```

## Mock Data Location

Mock data is mounted from the host at:
- Host: `/home/warby/Workspace/Bunny/temp/mock_data/`
- Container: `/app/public/temp/mock_data/`
- Browser: `/temp/mock_data/`

## Data Structure

Each subreddit has:
- `{subreddit}/json/{subreddit}_posts.json` - Post metadata
- `{subreddit}/images/` - Downloaded image files

Example: `Sjokz/json/Sjokz_posts.json`

## How It Works

1. **MSW Initialization**: When `PUBLIC_GRAPHQL_MOCK=true`, MSW starts in the browser
2. **GraphQL Interception**: MSW intercepts GraphQL queries to `/api/graphql`
3. **Data Loading**: Handlers load JSON files from `/temp/mock_data/`
4. **Transformation**: Raw Reddit post data is transformed to GraphQL format
5. **Response**: Mock data is returned matching the GraphQL schema

## Supported Queries

The following GraphQL queries are mocked:

- `FeedWithFilters` - Main feed query with filtering
- `Feed` - Legacy feed query
- `GetSavedBoards` - Saved board management
- `CreateSavedBoard` - Create new board
- `UpdateSavedBoard` - Update existing board
- `DeleteSavedBoard` - Delete board

## Filtering

Mock data supports filtering by:

- **Persons**: Maps person names to subreddit names (e.g., "Taylor Swift" → ["TaylorSwift", "TaylorSwiftCandids", ...])
- **Sources**: Filter by subreddit name (e.g., "r/Sjokz" or "Sjokz")
- **Search Query**: Search in post titles, authors, and sources

## Debugging

Check browser console for MSW logs:

- `[MSW] Mock mode enabled` - MSW is active
- `[MSW] FeedWithFilters handler called` - Query intercepted
- `[MSW] Loaded X total items` - Data loaded successfully
- `[MSW] After filtering: X items` - Filtering results

## Troubleshooting

### MSW Not Starting

1. Check `PUBLIC_GRAPHQL_MOCK=true` in docker-compose.yml
2. Restart frontend container: `docker compose restart`
3. Check browser console for MSW errors
4. Verify `mockServiceWorker.js` exists in `public/` directory

### No Data Loading

1. Verify mock data is accessible: `curl http://localhost:4321/temp/mock_data/Sjokz/json/Sjokz_posts.json`
2. Check browser console for fetch errors
3. Verify volume mount in docker-compose.yml points to correct path

### Data Not Filtering

1. Check person name mapping in `handlers.ts` → `getSubredditsForPerson()`
2. Verify filter variables in GraphQL query
3. Check browser console for filter debug logs

## Adding New Mock Data

1. Export data to `/temp/mock_data/{subreddit}/json/{subreddit}_posts.json`
2. Add subreddit to `SUBREDDITS` array in `src/lib/mock-data/loader.ts`
3. Add person mapping in `getSubredditsForPerson()` if needed
4. Restart frontend container

## Switching Between Mock and Real Backend

To switch between mock and real backend:

1. Edit `docker-compose.yml`:
   ```yaml
   environment:
     - PUBLIC_GRAPHQL_MOCK=true   # Use mocks
     # or
     - PUBLIC_GRAPHQL_MOCK=false  # Use real backend
   ```

2. Restart frontend:
   ```bash
   docker compose restart
   ```

3. Clear browser cache if needed (MSW service worker may cache)

## Notes

- MSW only works in the browser (not during SSR)
- Mock data is lazy-loaded on first request and cached
- Images are served from the same `/temp/mock_data/` path
- Filtering happens client-side in MSW handlers




