import React from 'react';
import { ThemeProvider } from '../../lib/themes/theme-context';
import Sidebar from './Sidebar';

interface ThemeProviderWrapperProps {
  children: React.ReactNode;
}

export default function ThemeProviderWrapper({ children }: ThemeProviderWrapperProps) {
  const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';
  
  return (
    <ThemeProvider>
      <div className="flex h-screen overflow-hidden">
        <Sidebar currentPath={currentPath} />
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </div>
    </ThemeProvider>
  );
}

