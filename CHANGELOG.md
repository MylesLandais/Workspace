# Changelog

All notable changes to System Nebula (formerly Bunny) will be documented in this file.

## [Unreleased]

### Added
- System Nebula branded landing page with stealth-mode design
- Mailing list/waitlist signup for beta invite requests
- Invite validation page with code support
- Authentication page for existing users
- Invite code "ASDF-WHALECUM" to valid codes
- Comprehensive E2E test suite with 6 test categories
- Performance monitoring utilities (`src/lib/utils/performance.ts`)
- Docstrings to all new components

### Changed
- Landing page: Updated from "Bunny Project" to "System Nebula"
- Button text: "Join Beta" → "Join Mailing List"
- Success message: "You're on the list" → "You've joined the mailing list"
- Feed initial load: 100 items → 20 items (5x faster)
- Navigation: Fixed door icon to use `<Link>` component
- Feed redirect: Changed `window.location.href` to `router.push()`
- Next.js config: Added image optimization, removed invalid options
- Root layout: Updated metadata and removed custom theme attribute

### Fixed
- TypeScript errors (any types, Slide interface, RedditPost import)
- ESLint errors (@ts-ignore, unescaped apostrophes, unused imports)
- Build configuration issues (removed swcMinify, standalone output)
- Client-side routing for better UX

### Performance
- Enabled AVIF/WebP image formats
- Configured proper device and image sizes
- Added compression and SWC minification
- Reduced initial payload by 80% (20 vs 100 items)
- Optimized client-side navigation

### Documentation
- Updated README with new authentication flow
- Added INVITE_CODES.md for invite system docs
- Added PERFORMANCE.md for optimization guide
- Added BUILD_ISSUE.md for build error documentation
- Added docstrings to key components (Home, Invite, Auth, SignIn, tests)

### Test Coverage
- Page load performance tests
- Authentication flow tests (sign in, sign up, invite)
- Waitlist/mailing list signup tests
- Invite validation tests (valid, invalid codes)
- Responsive design tests
- Error handling tests
- Accessibility tests

---

## Previous Versions

See git history for earlier changes.
