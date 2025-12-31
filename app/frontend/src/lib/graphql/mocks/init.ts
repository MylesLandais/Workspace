/**
 * MSW initialization module - client-side only
 * Call this from a client component to ensure MSW starts before Apollo queries
 */

let mswInitialized = false;
let mswInitPromise: Promise<void> | null = null;

export async function initializeMSW(): Promise<void> {
  // Only run in browser
  if (typeof window === 'undefined') {
    console.log('[MSW] Skipping initialization (server-side)');
    return;
  }

  // Check if already initialized
  if (mswInitialized) {
    console.log('[MSW] Already initialized');
    return;
  }

  // Check if initialization is in progress
  if (mswInitPromise) {
    console.log('[MSW] Waiting for existing initialization...');
    return mswInitPromise;
  }

  // Check environment
  const isMockMode = import.meta.env.PUBLIC_GRAPHQL_MOCK === 'true';
  if (!isMockMode) {
    console.log('[MSW] Mock mode disabled, skipping MSW initialization');
    mswInitialized = true; // Mark as initialized to prevent retries
    return;
  }

  console.log('[MSW] ========== Starting MSW initialization ==========');
  console.log('[MSW] Environment:', {
    isMockMode,
    windowDefined: typeof window !== 'undefined',
    location: window.location.href,
    timestamp: new Date().toISOString(),
  });

  // Start initialization (with timeout to prevent hanging)
  mswInitPromise = (async () => {
    try {
      console.log('[MSW] Importing setupMockServer...');
      const { setupMockServer } = await import('./server');
      console.log('[MSW] Imported setupMockServer, calling...');
      
      // Add timeout to prevent hanging (service worker registration can sometimes hang)
      const timeoutMs = 8000;
      const setupPromise = setupMockServer();
      const timeoutPromise = new Promise<void>((_, reject) => 
        setTimeout(() => reject(new Error(`MSW setup timeout after ${timeoutMs}ms`)), timeoutMs)
      );
      
      await Promise.race([setupPromise, timeoutPromise]);
      mswInitialized = true;
      console.log('[MSW] ========== MSW initialization complete ==========');
    } catch (error) {
      console.error('[MSW] ========== MSW initialization failed ==========', error);
      console.error('[MSW] Error details:', {
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
      });
      mswInitialized = true; // Mark as initialized anyway to prevent infinite retries
      // Don't throw - allow app to continue
      console.warn('[MSW] Continuing without MSW - GraphQL requests may fail or use real backend');
    }
  })();

  return mswInitPromise;
}

// Auto-initialize when module loads (only in browser)
if (typeof window !== 'undefined') {
  // Use requestIdleCallback if available, otherwise setTimeout to delay slightly
  // This ensures DOM is ready and other scripts have loaded
  const initMSW = () => {
    const isMockMode = import.meta.env.PUBLIC_GRAPHQL_MOCK === 'true';
    if (isMockMode) {
      initializeMSW().catch((error) => {
        console.error('[MSW] Auto-initialization failed:', error);
      });
    }
  };

  if ('requestIdleCallback' in window) {
    requestIdleCallback(initMSW, { timeout: 1000 });
  } else {
    // Fallback for browsers without requestIdleCallback
    setTimeout(initMSW, 100);
  }
}

