import React, { useEffect, useState } from 'react';
import { AppProviders } from '../../lib/providers/AppProviders';
import BunnyFeed from './BunnyFeed';

/**
 * Wrapper that provides AppProviders (Apollo + Theme) for BunnyFeed
 * This is needed because Astro can't pass children to client components directly
 */
export default function BunnyFeedWrapper() {
  useEffect(() => {
    console.log('[BunnyFeedWrapper] Component mounted');
    
    // Initialize MSW in the background (don't block rendering)
    // MSW will start intercepting requests once it's ready
    const initMSW = async () => {
      try {
        const { initializeMSW } = await import('../../lib/graphql/mocks/init');
        console.log('[BunnyFeedWrapper] Starting MSW initialization in background...');
        // Don't await - let it initialize in background
        initializeMSW().catch((error) => {
          console.error('[BunnyFeedWrapper] MSW initialization failed:', error);
        });
      } catch (error) {
        console.error('[BunnyFeedWrapper] Failed to import MSW init module:', error);
      }
    };

    initMSW();
  }, []);
  
  // Render immediately - MSW will catch requests once it's ready
  return (
    <AppProviders>
      <BunnyFeed />
    </AppProviders>
  );
}

