import React from 'react';
import { AppProviders } from '../../lib/providers/AppProviders';
import Sidebar from './Sidebar';

interface ThemeProviderWrapperProps {
  children: React.ReactNode;
}

/**
 * Layout wrapper that provides app-wide providers (Apollo, Theme) and
 * includes the legacy sidebar for non-Bunny pages.
 * 
 * For pages that provide their own layout (like BunnyFeed), they should
 * use AppProviders directly instead of this wrapper.
 */
export default function ThemeProviderWrapper({ children }: ThemeProviderWrapperProps) {
  const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';
  
  return (
    <AppProviders>
      <div className="flex h-screen overflow-hidden">
        <Sidebar currentPath={currentPath} />
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </div>
    </AppProviders>
  );
}

