# Bunny Client

Infinite wall feed with masonry layout for curated content.

## Quick Start

1. **Install dependencies:**
   ```bash
   docker compose up -d
   ```

2. **Run development server:**
   ```bash
   docker compose exec client bun run dev --hostname 0.0.0.0
   ```

3. **Run tests:**
   ```bash
   # Run unit tests with cleanup
   docker compose exec client bun run test:ci

   # Run tests without cleanup (for watch mode)
   docker compose exec client bun test

   # Run with test watcher
   docker compose exec client bun test --watch
   ```

4. **Access the application:**
   - Feed page: http://localhost:3001/feed
   - Reddit demo: http://localhost:3001/reddit-demo

## Tech Stack

- **Client**: Next.js 15 (App Router) + React 19 + TailwindCSS + Bun runtime
- **Server**: Elysia.js (Bun-native) + Eden (end-to-end type safety)
- **Database**: Neo4j (graph) + Drizzle ORM (relational) + Valkey (cache)
- **Runtime**: Bun for development, builds, and server
- **Testing**: Bun (unit) + Playwright (E2E)
- **Type Safety**: Eden treaty for client-server type inference

## Project Structure

```
/
├── app/                  # Next.js App Router pages and layouts
│   ├── api/               # API routes
│   ├── feed/             # Feed pages
│   └── reddit-demo/       # Reddit embed component showcase
├── src/
│   ├── components/        # React components
│   │   ├── feed/       # Masonry grid and feed items
│   │   ├── reddit/      # Reddit embed components (BUN-42)
│   │   └── search/     # Search components
│   ├── hooks/            # Custom React hooks
│   ├── lib/
│   │   ├── hooks/      # Reusable hooks (use-infinite-feed, etc.)
│   │   ├── store/      # State management (Zustand)
│   │   ├── mock-data/  # Mock data generation
│   │   ├── types/       # TypeScript type definitions
│   │   └── utils.ts    # Utility functions
├── public/              # Static assets and test media
├── Dockerfile           # Docker configuration
└── docker-compose.yml     # Local development setup
```

## Testing

### Unit Tests

- **Location**: `src/lib/store/search-store.test.ts`
- **Framework**: Bun test runner
- **Status**: All tests passing (3/3)
- **Coverage**: Zustand store functionality

### Running Tests

```bash
# Run tests with automatic cleanup (recommended)
docker compose exec client bun run test:ci

# Run tests without cleanup (for watch mode)
docker compose exec client bun test

# Run tests with file watcher
docker compose exec client bun test --watch
```

### Test Script Details

The `test:ci` script in `package.json` runs tests and then cleans the build cache:

```json
"test:ci": "bun test && rm -rf .next"
```

This approach prevents build cache permission issues by running cleanup **inside** the Docker container.

## Known Issues

### Build Cache Permission Error

If you encounter permission denied errors when cleaning `.next` directory:

```bash
# Solution: Run cleanup inside the container
docker compose exec client sh -c "rm -rf .next"

# Or use the test script which does this automatically
docker compose exec client bun run test:ci
```

## Features

### Feed Components

- **MasonryGrid**: Responsive masonry layout with absolute positioning
- **FeedItem**: Individual media cards with video/image support
- **InfiniteScrollSentinel**: Intersection observer for loading more items
- **useInfiniteFeed**: Hook for paginated feed data

### Reddit Components (BUN-42)

- **RedditPostCard**: Premium embeddable Reddit post with gallery support
- **RedditGalleryEmbed**: Full-featured Reddit embed with lightbox and comments
- **useReddit**: Hooks for Reddit API integration

See `/reddit-demo` for live component examples.

## Mock Data

The application includes a mock data generator (`src/lib/mock-data/factory.ts`) that:
- Generates realistic feed items with varied aspect ratios
- Supports local test media from `/public/test-media/`
- Integrates Reddit metadata for BUN-42 component testing

To add your own test media:
1. Place files in `public/test-media/`
2. Update `src/lib/mock-data/test-files.json` with file list (run `ls public/test-media/ > src/lib/mock-data/test-files.json` inside container)

## Docker Compliance

**IMPORTANT**: All `bun` commands must be executed through Docker.

```bash
# Start development server
docker compose up -d

# Stop containers
docker compose down

# Rebuild from scratch
docker compose up -d --build
```

## Environment

- **NODE_ENV**: Set to `development` in docker-compose.yml
- **NEXT_PUBLIC_USE_MOCK_DATA**: Set to `true` to use mock data (default)
- **NEXT_PUBLIC_REDDIT_API_URL**: Configure for Reddit API integration

## Development Workflow

1. Start containers: `docker compose up -d`
2. Run tests: `docker compose exec client bun run test:ci`
3. Develop features
4. Run linter: `docker compose exec client bun run lint`
5. Build production: `docker compose exec client bun run build`
