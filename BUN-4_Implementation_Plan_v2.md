# BUN-4 Masonry Grid Implementation & Layout Refactor

## Objective
Refactor the Feed Component to use a custom absolute-positioned Masonry layout as requested in code review, and migrate the project structure to follow the `client` + `server` naming convention.

## Changes Made

### 1. Project Structure & Naming
- Renamed `app/backend` → `app/server`.
- Renamed `app/frontend` (Astro) → `app/frontend-legacy-astro` (Deprecating in favor of Next.js).
- Established `app/client` (Next.js) as the primary frontend project.
- Updated `package.json` and `docker-compose.yml` in `app/server` to reflect the name change.

### 2. Layout Engine (app/client)
- **Absolute Positioning**: Implemented a custom Masonry algorithm in `useMasonryLayout.ts` that calculates `x` and `y` coordinates based on column heights.
- **Self-Measurement**: Integrated `ResizeObserver` into `FeedItem.tsx` to dynamically report item heights to the grid, ensuring accurate positioning even before images are fully loaded.
- **Responsiveness**: Created `useMediaQuery.ts` to implement strict breakpoint mappings:
    - Mobile (<640px): 1 Col, 12px Gap
    - Tablet (640px+): 2 Cols, 16px Gap
    - Desktop (1024px+): 3 Cols, 20px Gap
    - Wide (1440px+): 4 Cols, 24px Gap
    - Ultra (1920px+): 5 Cols, 24px Gap

### 3. Data Strategy
- **Mock Fallback**: Ported mock data loader logic to `app/client/src/lib/mock-data/loader.ts`.
- **Bypass Blockers**: Updated `useInfiniteFeed` hook to toggle between real GraphQL API and mock data based on the `NEXT_PUBLIC_USE_MOCK_DATA` environment variable (defaulting to mock for current development).
- **Environment**: Updated `docker-compose.yml` to mount `/temp/mock_data` to `/app/public/temp` for client access to raw JSON samples.

## Status: COMPLETE
- ✅ Absolute Positioning implemented.
- ✅ Client/Server naming convention applied.
- ✅ Mock data integrated for development.
- ✅ Responsive breakpoints strictly followed.

## Next Steps
- Resolve BUN-28/29 (S3/Neo4j metadata schema) to enable production GraphQL feed.
- Implement Lightbox detail view with navigation handlers already present in `FeedPage`.
