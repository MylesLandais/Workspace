/**
 * Bunny Data Integration Examples
 *
 * This directory contains example React hooks and components for integrating
 * your web application with the Bunny GraphQL API.
 *
 * See INTEGRATION_GUIDE.md for full documentation.
 *
 * Directory structure:
 * - hooks/     - React hooks for data fetching
 * - components/ - Example React components
 * - queries/   - GraphQL query definitions and TypeScript types
 */

// Hooks
export { useFeed, getImageUrl, getAspectRatio, isUrlExpired } from './hooks/useFeed';
export type {
  UseFeedOptions,
  UseFeedReturn,
  Media,
  FeedFilters,
  FeedConnection,
  FeedEdge,
  PageInfo,
  HandleInfo,
  Platform,
  MediaType,
} from './hooks/useFeed';

export {
  useSources,
  useSubredditSearch,
  getPlatformLabel,
  getSourceHandle,
  getHealthColor,
} from './hooks/useSources';
export type {
  UseSourcesOptions,
  UseSourcesReturn,
  Source,
  CreateSourceInput,
  UpdateSourceInput,
  SourceFiltersInput,
  ActivityFilter,
  ImportResult,
  SubredditResult,
} from './hooks/useSources';

export {
  useSourceFilters,
  useFeedFilters,
  filtersToSearchParams,
  searchParamsToFilters,
} from './hooks/useSourceFilters';
export type {
  UseSourceFiltersReturn,
  UseFeedFiltersReturn,
} from './hooks/useSourceFilters';

// Components
export { FeedGrid, FeedMasonry } from './components/FeedGrid';
export { FeedItem, FeedItemCompact } from './components/FeedItem';
export { SourceList } from './components/SourceList';
export { SourceForm, SourceFormModal } from './components/SourceForm';

// Re-export all types from types.ts for convenience
export * from './queries/types';
