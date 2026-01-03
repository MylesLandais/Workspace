# System Nebula

Invite-only community platform with stealth-mode landing page.

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

    # Run E2E tests
    docker compose exec client bun run test:e2e
    ```

4. **Access application:**
    - Home page: http://localhost:3001
    - Auth page: http://localhost:3001/auth
    - Invite page: http://localhost:3001/invite
    - Feed page: http://localhost:3001/feed

## Authentication Flow

### Waitlist / Mailing List
1. Visit home page
2. Enter email address
3. Click "Join Mailing List"
4. Receive confirmation message

### Invite Access
1. Click "Have an invite key?" on home page
2. Enter invite code (e.g., "ASDF-WHALECUM" or any "SN-XXXXX" key)
3. Validate code
4. Create account with invite key

### Existing Users
1. Click the subtle door icon at bottom-center of home page
2. Sign in with email/password or social login

## Valid Invite Codes

- **ASDF-WHALECUM** - Special beta access code
- **SN-XXXXXX** - Any code starting with "SN-" prefix

See `client/INVITE_CODES.md` for more details.

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
│   ├── feed/             # Feed pages (authenticated)
│   ├── auth/             # Authentication page (existing users)
│   ├── invite/           # Invite validation page
│   ├── page.tsx          # Landing page (waitlist)
│   └── layout.tsx        # Root layout
├── src/
│   ├── components/        # React components
│   │   ├── auth/       # Sign in/up components
│   │   ├── feed/       # Masonry grid and feed items
│   │   └── search/     # Search components
│   ├── hooks/            # Custom React hooks
│   ├── lib/
│   │   ├── hooks/      # Reusable hooks
│   │   ├── store/      # State management (Zustand)
│   │   ├── mock-data/  # Mock data generation
│   │   ├── types/       # TypeScript type definitions
│   │   └── utils/      # Utility functions
├── public/              # Static assets
├── Dockerfile           # Docker configuration
├── docker-compose.yml     # Local development setup
└── INVITE_CODES.md     # Invite system documentation
```

## Testing

### E2E Tests

- **Location**: `e2e/performance.spec.ts`, `e2e/auth.spec.ts`
- **Framework**: Playwright
- **Coverage**:
  - Page load performance
  - Authentication flows
  - Invite validation
  - Waitlist signup
  - Responsive design
  - Error handling
  - Accessibility

### Running Tests

```bash
# Run E2E tests
docker compose exec client bun run test:e2e

# Run unit tests with cleanup
docker compose exec client bun run test:ci

# Run tests with watcher
docker compose exec client bun test --watch
```

## Performance Optimizations

### Implemented
- **Initial load**: Reduced from 100 to 20 feed items (5x faster)
- **Image optimization**: AVIF/WebP formats with proper sizes
- **Client navigation**: Uses Next.js `<Link>` for instant transitions
- **Bundle optimization**: SWC minification and compression enabled

### Monitoring
See `PERFORMANCE.md` for detailed performance tracking guide.

## Features

### Landing Page
- **Stealth-mode design**: "Under Construction" badge, shadowy aesthetic
- **Mailing list signup**: Email collection for beta invites
- **Invite validation**: Check invite codes before signup
- **Existing user access**: Subtle door icon for login

### Authentication
- **Email/password**: Full registration and login support
- **Social login**: GitHub, Google, Discord providers
- **Invite integration**: Passes invite key to signup form
- **Error handling**: Clear messages for auth failures

### Feed Components (Authenticated)
- **MasonryGrid**: Responsive masonry layout
- **FeedItem**: Individual media cards with video/image support
- **InfiniteScrollSentinel**: Intersection observer for loading
- **useInfiniteFeed**: Hook for paginated feed data

## Mock Data

The application includes a mock data generator (`src/lib/mock-data/factory.ts`) that:
- Generates realistic feed items with varied aspect ratios
- Supports local test media from `/public/`
- Integrates Reddit metadata for component testing

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

## Known Issues

### Build Error
There's a pre-existing Next.js 15 build issue with static generation for error pages. Dev mode works perfectly. See `BUILD_ISSUE.md` for details and workarounds.

### Build Cache Permission Error
If you encounter permission denied errors when cleaning `.next` directory:

```bash
# Solution: Run cleanup inside the container
docker compose exec client sh -c "rm -rf .next"

# Or use the test script which does this automatically
docker compose exec client bun run test:ci
```

## Development Workflow

1. Start containers: `docker compose up -d`
2. Run tests: `docker compose exec client bun run test:ci`
3. Develop features
4. Run linter: `docker compose exec client bun run lint`
5. Run E2E: `docker compose exec client bun run test:e2e`
6. Build production: `docker compose exec client bun run build`

## Checkpoint Notes

### Recent Changes (Checkpoint)
- ✅ Redesigned landing page with "System Nebula" branding
- ✅ Created waitlist/mailing list signup
- ✅ Implemented invite validation system with code "ASDF-WHALECUM"
- ✅ Added auth page for existing users
- ✅ Fixed door icon navigation to use client-side routing
- ✅ Reduced initial feed load from 100 to 20 items
- ✅ Added comprehensive E2E test suite
- ✅ Implemented performance optimizations
- ✅ Fixed TypeScript and ESLint errors
- ✅ Added docstrings to all new components
- ✅ Updated documentation (README, INVITE_CODES, PERFORMANCE, BUILD_ISSUE)
