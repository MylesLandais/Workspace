# Mock Data Strategy for Frontend Development

## Status

Accepted

## Context

Frontend development requires realistic data to test UI components, pagination, filtering, and performance at scale. The backend GraphQL API may be unavailable, unstable, or require complex setup (Neo4j database, authentication, etc.). We have large datasets of real Reddit posts stored in `/temp/mock_data/` but need a systematic approach to use this data for development and testing.

Traditional approaches have limitations:
- Hard-coding small fixture arrays in components makes it hard to test edge cases
- Manually creating large datasets is tedious and doesn't scale
- Backend dependencies block frontend developers from working independently
- Component tests need consistent, controllable data scenarios

## Decision

Implement a comprehensive mock data strategy that treats the GraphQL schema as the contract and makes the backend optional for local development:

1. **Schema-Based Mocking**: Use MSW (Mock Service Worker) to intercept GraphQL requests and return realistic data that matches our schema
2. **Factory-Based Data Generation**: Build factories over existing JSON data to generate thousands of posts deterministically
3. **Multi-Scenario Support**: Support different dataset sizes (SMALL, MEDIUM, LARGE) and scenarios (empty feeds, error states, slow responses)
4. **Independent Development**: Frontend developers can work without backend dependencies

## Rationale

**Independent Development**: Frontend developers can iterate on UI/UX without waiting for backend, database setup, or API stability.

**Realistic Testing**: Using actual scraped Reddit data ensures we're testing against real-world content shapes, sizes, and edge cases.

**Scalable Datasets**: Factory-based generation lets us create 1k-10k item datasets for stress-testing virtualization, infinite scroll, and client-side filtering without manually creating fixtures.

**Deterministic Tests**: Same seed = same data, making tests reproducible and debuggable.

**Multiple Scenarios**: Can easily test edge cases (empty states, errors, slow responses) by switching dataset scenarios.

**Storybook Integration**: Mocked GraphQL layer enables component stories to run in isolation with different data scenarios.

## Implementation

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Frontend Application                    │
│  (Astro + React + Apollo Client)                        │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ GraphQL Queries
                   │
         ┌─────────▼─────────┐
         │  Apollo Client    │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  MSW Interceptor  │ ◄─── Intercepts in browser
         │  (mock mode)      │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Mock Handlers    │
         │  (handlers.ts)    │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐      ┌──────────────────┐
         │  Data Factories   │─────►│ /temp/mock_data/ │
         │  (loader.ts)      │      │  (JSON files)    │
         └───────────────────┘      └──────────────────┘
```

### Components

#### 1. Mock Service Worker (MSW)

**Location**: `app/frontend/src/lib/graphql/mocks/`

- Intercepts GraphQL requests in the browser via Service Worker
- Handlers implement the GraphQL schema contract
- Enabled via `PUBLIC_GRAPHQL_MOCK=true` environment variable
- Falls back to real backend when mock mode is disabled

#### 2. Data Factories

**Location**: `app/frontend/src/lib/mock-data/loader.ts`

Factories read from `/temp/mock_data/` and:
- Transform Reddit JSON format to GraphQL schema format
- Support lazy loading of subreddits (load on-demand, cache results)
- Filter and normalize data (remove removed posts, validate image URLs)
- Map subreddit names to creator entities for filtering

**Key Functions**:
- `loadAllMedia()`: Loads all posts from all available subreddits
- `loadSubredditData(subredditName)`: Loads posts from a specific subreddit
- `getMediaForSubreddit(subredditName)`: Quick preview of subreddit posts

#### 3. Dataset Scenarios

Support different dataset sizes via configuration:

- **SMALL**: ~100 posts from priority subreddits (Selena, Taylor, etc.) - fast startup
- **MEDIUM**: ~1k posts from 20-30 subreddits - balanced for most development
- **LARGE**: ~10k posts from all 65+ subreddits - stress testing

**Future Enhancement**: Support scenario-based datasets:
- `empty-feed`: No posts (test empty states)
- `error-state`: Simulate API errors
- `slow-response`: Add artificial delays
- `massive-thread`: Deep comment trees

#### 4. Filter Presets

Pre-configured filter presets for common testing scenarios:

- **"Pop Queenz"**: Filters by persons: `['Taylor Swift', 'Selena Gomez']` - tests person-based filtering
- **"Linux Threads"**: Search query `'linux'` - tests text search (when Linux data is available)

Defined in: `app/frontend/src/lib/bunny/services/fixtures.ts` as `DEMO_BOARDS`

## Consequences

### Positive

- **Fast Development Cycles**: Frontend developers can work without backend dependencies
- **Realistic Testing**: Real scraped data reveals real-world edge cases
- **Scalable**: Can generate datasets of any size for performance testing
- **Reproducible**: Deterministic generation makes tests consistent
- **Isolated Components**: Storybook stories can run with mocked data
- **Backend Optional**: Backend becomes optional for frontend development

### Negative

- **Data Sync Risk**: Mock data may drift from real backend schema if not maintained
- **Initial Setup**: Requires maintaining mock data files and factories
- **Loading Overhead**: Large datasets may cause initial load delays (mitigated by lazy loading and caching)
- **Schema Drift**: Schema changes require updating both backend and mock handlers

### Neutral

- Mock data lives in `/temp/mock_data/` (not versioned, developer-specific)
- Can be regenerated from scraped Reddit data as needed
- Factories can be extended to generate synthetic data if real data becomes unavailable

## Alternatives Considered

**Small Hard-Coded Fixtures**: Rejected because they don't scale and don't test real-world scenarios.

**Backend Dependency**: Rejected because it blocks independent frontend development and requires complex setup.

**Separate Mock API Server**: Considered but rejected because MSW's browser-based approach is simpler and doesn't require additional infrastructure.

**Generated Synthetic Data Only**: Rejected because real scraped data provides better edge case coverage and more realistic testing.

## References

- [MSW Documentation](https://mswjs.io/)
- [GraphQL Mocking Best Practices](https://graphql.org/blog/2016-04-19-mocking/)
- [Frontend Testing with Mocked Backends](https://about.codecov.io/blog/mastering-front-end-testing-a-guide-to-mocking-backends/)
- [GraphQL Tools Mocking](https://the-guild.dev/graphql/tools/docs/mocking)

## Future Enhancements

1. **Data Generation Tool**: Script to generate large canonical datasets (e.g., `home-small.json`, `home-large.json`, `thread-deep.json`)
2. **Scenario-Based Queries**: Support `scenario` or `size` arguments in GraphQL queries
3. **Storybook Integration**: Wire mocked GraphQL provider into Storybook stories
4. **E2E Test Scenarios**: Environment variables to select scenarios in Playwright/Cypress tests
5. **Performance Monitoring**: Add metrics to track mock data load times and optimize




