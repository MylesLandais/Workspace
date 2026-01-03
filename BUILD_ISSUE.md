# Build Issue - Pre-Existing

## Problem
The Next.js build is failing with an error about `<Html>` being imported outside of `pages/_document`. This is a pre-existing issue in the codebase that appears to be related to how Next.js 15 handles static generation for error/404 pages.

## Error Details
```
Error: <Html> should not be imported outside of pages/_document.
Export encountered an error on /_error: /404, exiting the build.
```

## Investigation
1. The app is using App Router (no `/pages` directory exists)
2. No custom imports of `Html` from `next/document` in our code
3. Dev server runs successfully
4. Build fails during static page generation
5. Issue occurs even without custom error/not-found pages

## Workarounds Tried
- Removed `output: "standalone"` from next.config.ts
- Added `export const dynamic = "force-dynamic"` to all pages
- Removed custom error/not-found pages temporarily
- Simplified layout.tsx

## Current Status
- **Dev mode**: Works perfectly
- **Production build**: Fails due to this error

## Recommendation
This is likely a Next.js 15.1.4 bug with App Router static generation. Options:
1. Wait for Next.js update
2. Use Docker for deployment without static export
3. File bug report with Next.js team

## What Still Works
- Development server (`bun run dev`)
- All E2E tests (when run in dev mode)
- Door icon navigation
- Invite validation flow
- Waitlist signup
- Authentication flow

## Performance Optimizations Completed
Despite build issue, these optimizations were made:
- Reduced initial feed load from 100 to 20 items
- Added image optimization (AVIF/WebP)
- Changed `window.location.href` to `router.push()`
- Fixed door icon to use `<Link>` component
- Created performance monitoring utilities
- Comprehensive E2E test suite
