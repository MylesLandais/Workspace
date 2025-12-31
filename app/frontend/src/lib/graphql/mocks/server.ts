import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

/**
 * Setup MSW worker for browser environment
 * This should be called when PUBLIC_GRAPHQL_MOCK=true
 * 
 * Note: Requires mockServiceWorker.js to be generated in the public directory.
 * Run: npx msw init public/ --save
 */
export async function setupMockServer() {
  if (typeof window === 'undefined') {
    // Server-side rendering - MSW doesn't work here
    console.log('[MSW] Skipping setup (server-side rendering)');
    return;
  }

  console.log('[MSW] ========== Setting up MSW mock server ==========');
  console.log('[MSW] Environment check:', {
    windowDefined: typeof window !== 'undefined',
    location: typeof window !== 'undefined' ? window.location.href : 'N/A',
    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'N/A',
  });
  console.log('[MSW] Handlers count:', handlers.length);
  console.log('[MSW] Handlers:', handlers);

  try {
    console.log('[MSW] Creating worker with handlers...');
    const worker = setupWorker(...handlers);
    console.log('[MSW] Worker created, starting...');

    await worker.start({
      onUnhandledRequest: 'bypass', // Don't warn on unhandled requests, just let them through
      serviceWorker: {
        url: '/mockServiceWorker.js',
        options: {
          scope: '/',
        },
      },
      // Suppress MSW's default console messages
      quiet: false,
    });

    console.log('[MSW] ========== Mock server started successfully ==========');
    console.log('[MSW] Listening for GraphQL queries...');
  } catch (error) {
    console.error('[MSW] ========== FAILED to start mock server ==========', {
      error,
      errorType: error?.constructor?.name,
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
    });
    console.warn('[MSW] Make sure mockServiceWorker.js exists in public/ directory');
    console.warn('[MSW] Run: npx msw init public/ --save');
  }
}

