import React from 'react';
import { ApolloProvider } from '@apollo/client';
import { ThemeProvider } from '../themes/theme-context';
import { apolloClient } from '../graphql/client';

interface AppProvidersProps {
  children: React.ReactNode;
}

/**
 * Unified provider wrapper that provides Apollo Client and Theme context
 * to all child components. This should be used at the layout level.
 */
export function AppProviders({ children }: AppProvidersProps) {
  return (
    <ApolloProvider client={apolloClient}>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </ApolloProvider>
  );
}





