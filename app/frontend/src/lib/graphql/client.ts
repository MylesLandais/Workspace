import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';

const isMockMode = import.meta.env.PUBLIC_GRAPHQL_MOCK === 'true';
const endpoint = import.meta.env.PUBLIC_GRAPHQL_ENDPOINT || 'http://localhost:4002/api/graphql';

const httpLink = createHttpLink({
  uri: endpoint,
});

// MSW initialization is handled separately in mocks/init.ts
// This file only exports the Apollo Client

export const apolloClient = new ApolloClient({
  link: httpLink,
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
    },
    query: {
      fetchPolicy: 'network-only',
    },
  },
});

export const isMock = isMockMode;

// MSW initialization is handled in mocks/init.ts and called from client components
// This module-level code runs during SSR, so we can't initialize MSW here

