# Performance Optimization Guide

## Quick Performance Checks

### 1. Measure Page Load Times

```bash
# Build with production optimizations
docker compose exec client bun run build

# Start production server
docker compose exec client bun run start
```

### 2. Run Performance E2E Tests

```bash
docker compose exec client bun run test:e2e
```

### 3. Check Network Waterfall

- Open Chrome DevTools (F12)
- Go to Network tab
- Reload page
- Look for:
  - Long requests (>1s)
  - Large JS bundles (>200KB)
  - Unoptimized images

## Changes Made

### 1. Feed Page Optimizations

- Reduced initial load from 100 to 20 items (5x faster initial load)
- Changed `window.location.href` to `router.push()` (smoother navigation)

### 2. Next.js Configuration

- Added image optimization (AVIF/WebP)
- Enabled SWC minification
- Added CSS optimization
- Compressed output

### 3. Navigation Fixes

- Changed door icon from `<a>` to `<Link>` (client-side routing)
- Faster page transitions

### 4. Feed Improvements

- Smaller initial payload (20 items vs 100)
- Lazy loading with infinite scroll
- Proper image sizes configured

## Performance Monitoring

### Development Mode

```bash
# Check performance metrics in browser console
# All API calls are logged with timing
```

### Production Mode

Add this to `app/page.tsx`:

```typescript
useEffect(() => {
  if ("performance" in window) {
    window.addEventListener("load", () => {
      const perfData = performance.getEntriesByType("navigation")[0] as any;
      console.log({
        domComplete: perfData.domComplete,
        loadTime: perfData.loadEventEnd - perfData.navigationStart,
        ttfb: perfData.responseStart - perfData.requestStart,
      });
    });
  }
}, []);
```

## Common Performance Issues

### Slow Initial Load

- Check bundle size: `docker compose exec client bun run build -- --help | grep analyze`
- Look for large dependencies
- Enable code splitting

### Slow API Calls

- Add database indexes
- Use connection pooling
- Cache responses

### Image Performance

- Use Next.js `<Image>` component
- Enable AVIF/WebP formats
- Lazy load below-the-fold images

## E2E Test Coverage

We now have comprehensive tests for:

- Page load performance
- Door icon navigation
- Waitlist signup
- Invite validation
- Authentication flow
- Responsive design
- Error handling
- Accessibility

Run all tests:

```bash
docker compose exec client bun run test:e2e
```

## Debugging Slow Loads

1. **Check build output** for large chunks
2. **Run performance tests** to identify bottlenecks
3. **Use Chrome DevTools** to measure real-world performance
4. **Monitor database queries** with logging
5. **Check network requests** for slow responses

## Next Steps for Performance

1. Add service worker for caching
2. Implement request deduplication
3. Add analytics for production monitoring
4. Consider edge deployment for static assets
5. Optimize images with next/image everywhere
