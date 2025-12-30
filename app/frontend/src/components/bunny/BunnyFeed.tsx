import React, { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { Sidebar } from './Sidebar';
import { FilterBar } from './FilterBar';
import { FeedItem } from './FeedItem';
import { Lightbox } from './Lightbox';
import { EntityManager } from './EntityManager';
import { FilterState, INITIAL_FILTERS, FeedItem as FeedItemType, SavedBoard, Theme, AppView, MediaType } from '../../lib/bunny/types';
import { Loader2, RefreshCw } from 'lucide-react';
import { DEMO_BOARDS } from '../../lib/bunny/services/fixtures';
import { useTheme } from '../../lib/themes/theme-context';
import { mapBunnyThemeToThemeId, mapThemeIdToBunnyTheme } from '../../lib/bunny/theme-adapter';
import { GET_SAVED_BOARDS, FEED_WITH_FILTERS } from '../../lib/graphql/queries';
import { CREATE_SAVED_BOARD as CREATE_BOARD_MUTATION, DELETE_SAVED_BOARD as DELETE_BOARD_MUTATION } from '../../lib/graphql/mutations';

function BunnyFeedContent() {
  // Debug: Check if component is rendering
  if (typeof window !== 'undefined') {
    console.log('[BunnyFeedContent] Rendering...');
  }
  
  // Use theme - AppProviders should provide this, but guard against SSR
  // useTheme already returns a default during SSR, but we're client-only so this should work
  const themeContext = useTheme();
  const { themeId, setTheme: setUnifiedTheme } = themeContext;
  const [filters, setFilters] = useState<FilterState>(INITIAL_FILTERS);
  const [feedItems, setFeedItems] = useState<FeedItemType[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [initialLoadDone, setInitialLoadDone] = useState(false);
  const [currentView, setCurrentView] = useState<AppView>('feed');
  const [selectedItem, setSelectedItem] = useState<FeedItemType | null>(null);
  
  // Theme State - sync with unified theme system
  const [bunnyTheme, setBunnyTheme] = useState<Theme>(() => {
    return mapThemeIdToBunnyTheme(themeId);
  });

  useEffect(() => {
    // Sync Bunny theme with unified theme system
    const unifiedThemeId = mapBunnyThemeToThemeId(bunnyTheme);
    if (unifiedThemeId !== themeId) {
      setUnifiedTheme(unifiedThemeId);
    }
  }, [bunnyTheme, themeId, setUnifiedTheme]);

  useEffect(() => {
    // Sync unified theme changes back to Bunny theme
    const newBunnyTheme = mapThemeIdToBunnyTheme(themeId);
    if (newBunnyTheme !== bunnyTheme) {
      setBunnyTheme(newBunnyTheme);
    }
  }, [themeId]);

  const handleThemeChange = (theme: Theme) => {
    setBunnyTheme(theme);
    const unifiedThemeId = mapBunnyThemeToThemeId(theme);
    setUnifiedTheme(unifiedThemeId);
  };

  // TODO: Get userId from auth context when available
  const userId = 'default-user'; // Placeholder for multi-user support
  
  // Load saved boards from GraphQL
  const { data: boardsData, refetch: refetchBoards } = useQuery(GET_SAVED_BOARDS, {
    variables: { userId },
    skip: typeof window === 'undefined',
    fetchPolicy: 'cache-and-network',
  });
  
  const [createBoard] = useMutation(CREATE_BOARD_MUTATION, {
    refetchQueries: [{ query: GET_SAVED_BOARDS, variables: { userId } }],
  });
  
  const [deleteBoard] = useMutation(DELETE_BOARD_MUTATION, {
    refetchQueries: [{ query: GET_SAVED_BOARDS, variables: { userId } }],
  });
  
  const savedBoards: SavedBoard[] = boardsData?.getSavedBoards?.map((b: any) => ({
    id: b.id,
    name: b.name,
    filters: b.filters,
    createdAt: new Date(b.createdAt).getTime(),
  })) || DEMO_BOARDS; // Fallback to demo data

  const handleSaveBoard = async () => {
    const defaultName = filters.persons.length > 0 ? filters.persons.join(' & ') : 'My Custom Feed';
    const name = window.prompt("Name this board:", defaultName);
    if (!name) return;
    
    try {
      await createBoard({
        variables: {
          userId,
          input: {
            name,
            filters: {
              persons: filters.persons,
              sources: filters.sources,
              tags: filters.tags,
              searchQuery: filters.searchQuery,
            },
          },
        },
      });
    } catch (error) {
      console.error('Failed to save board:', error);
      alert('Failed to save board. Please try again.');
    }
  };

  const handleDeleteBoard = async (id: string) => {
    if (window.confirm("Are you sure you want to delete this board?")) {
      try {
        await deleteBoard({
          variables: { id },
        });
      } catch (error) {
        console.error('Failed to delete board:', error);
        alert('Failed to delete board. Please try again.');
      }
    }
  };

  const handleSelectBoard = (board: SavedBoard) => {
    setFilters(board.filters);
    setIsMobileMenuOpen(false);
    setCurrentView('feed');
  };

  // Fetch feed from GraphQL
  // Normalize filters: don't send empty arrays, use undefined instead for cleaner queries
  const normalizedFilters = {
    ...(filters.persons.length > 0 && { persons: filters.persons }),
    ...(filters.sources.length > 0 && { sources: filters.sources }),
    ...(filters.searchQuery.trim() && { searchQuery: filters.searchQuery.trim() }),
  };

  const { data: feedData, loading: feedLoading, refetch: refetchFeed, error: feedError } = useQuery(FEED_WITH_FILTERS, {
    variables: {
      limit: 50,
      filters: Object.keys(normalizedFilters).length > 0 ? normalizedFilters : undefined,
    },
    skip: typeof window === 'undefined' || currentView !== 'feed',
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all', // Continue rendering even if query fails
    notifyOnNetworkStatusChange: true,
  });

  // Enhanced debugging and error logging
  useEffect(() => {
    console.log('[BunnyFeed] Query state:', {
      loading: feedLoading,
      hasData: !!feedData,
      hasError: !!feedError,
      dataKeys: feedData ? Object.keys(feedData) : [],
      feedEdges: feedData?.feed?.edges?.length || 0,
      currentView,
      windowDefined: typeof window !== 'undefined',
    });
    
    if (feedError) {
      console.error('[BunnyFeed] GraphQL query error:', {
        error: feedError,
        message: feedError.message,
        networkError: feedError.networkError,
        graphQLErrors: feedError.graphQLErrors,
        stack: feedError.stack,
      });
    }
    
    if (feedData) {
      console.log('[BunnyFeed] Feed data received:', {
        edgesCount: feedData.feed?.edges?.length || 0,
        hasNextPage: feedData.feed?.pageInfo?.hasNextPage,
        sampleEdge: feedData.feed?.edges?.[0],
      });
    }
  }, [feedData, feedLoading, feedError, currentView]);

  // Core logic to fetch feed items
  const refreshFeed = useCallback(async () => {
    if (currentView !== 'feed') return;
    await refetchFeed();
  }, [currentView, refetchFeed]);

  // Transform GraphQL feed data to FeedItem format
  useEffect(() => {
    console.log('[BunnyFeed] Transform effect triggered:', {
      hasFeedData: !!feedData,
      hasEdges: !!feedData?.feed?.edges,
      edgesLength: feedData?.feed?.edges?.length || 0,
      feedLoading,
      initialLoadDone,
    });

    if (feedData?.feed?.edges) {
      console.log('[BunnyFeed] Processing feed edges:', feedData.feed.edges.length);
      const items: FeedItemType[] = feedData.feed.edges
        .map((edge: any, index: number) => {
          // Guard against malformed data
          if (!edge || !edge.node) {
            console.warn(`[BunnyFeed] Skipping malformed feed edge at index ${index}:`, edge);
            return null;
          }

          const node = edge.node;
          const mediaTypeMap: Record<string, MediaType> = {
            'IMAGE': MediaType.IMAGE,
            'VIDEO': MediaType.VIDEO,
            'TEXT': MediaType.TEXT,
            'image': MediaType.IMAGE,
            'video': MediaType.VIDEO,
            'text': MediaType.TEXT,
          };
          
          // Calculate aspect ratio class with safe defaults
          const width = node.width && typeof node.width === 'number' ? node.width : 600;
          const height = node.height && typeof node.height === 'number' ? node.height : 800;
          let aspectRatio = 'aspect-square';
          if (width > 0 && height > 0) {
            const ratio = width / height;
            if (ratio > 1.2) aspectRatio = 'aspect-video';
            else if (ratio < 0.8) aspectRatio = 'aspect-[3/4]';
          }
          
          // Handle unknown media types gracefully with fallback to IMAGE
          const mediaType = node.mediaType ? (mediaTypeMap[node.mediaType] || MediaType.IMAGE) : MediaType.IMAGE;
          
          // Ensure we have at least an ID and some content
          if (!node.id) {
            console.warn(`[BunnyFeed] Skipping feed item without ID at index ${index}:`, node);
            return null;
          }
          
          const item = {
            id: node.id,
            type: mediaType,
            caption: node.title || 'Untitled',
            author: {
              name: node.author?.username || 'Unknown',
              handle: node.author?.username ? `u/${node.author.username}` : '',
            },
            source: node.handle?.handle || node.subreddit?.name || 'Unknown',
            timestamp: node.publishDate || new Date().toISOString(),
            aspectRatio,
            width,
            height,
            likes: node.score && typeof node.score === 'number' ? node.score : 0,
            mediaUrl: node.imageUrl || node.sourceUrl || '',
          };
          
          if (index < 3) {
            console.log(`[BunnyFeed] Transformed item ${index}:`, {
              id: item.id,
              caption: item.caption.substring(0, 50),
              mediaUrl: item.mediaUrl?.substring(0, 80),
            });
          }
          
          return item;
        })
        .filter((item): item is FeedItemType => item !== null); // Remove null entries
      
      console.log('[BunnyFeed] Transformed items:', {
        total: items.length,
        sampleIds: items.slice(0, 5).map(i => i.id),
      });
      
      setFeedItems(items);
      setLoading(false);
      if (!initialLoadDone) {
        setInitialLoadDone(true);
      }
    } else if (feedLoading) {
      console.log('[BunnyFeed] Still loading...');
      setLoading(true);
    } else if (!feedLoading && !feedData && !feedError) {
      // Query completed but no data - might be empty result
      console.warn('[BunnyFeed] Query completed with no data and no error');
      setLoading(false);
      setFeedItems([]);
    } else if (feedError) {
      console.error('[BunnyFeed] Error state - not setting loading to false yet');
      // Keep loading state if there's an error, let error UI handle it
    }
  }, [feedData, feedLoading, feedError, initialLoadDone]);

  // Feed will auto-refetch when filters change due to useQuery variables

  useEffect(() => {
    // Only refresh on mount if we are in feed view (which is default)
    if (currentView === 'feed') refreshFeed();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className={`min-h-screen bg-app-bg text-app-text font-sans selection:bg-app-accent/30 selection:text-white transition-colors duration-300`}>
      
      <Sidebar 
        filters={filters} 
        setFilters={setFilters} 
        isMobileOpen={isMobileMenuOpen}
        savedBoards={savedBoards}
        onSelectBoard={handleSelectBoard}
        onDeleteBoard={handleDeleteBoard}
        theme={bunnyTheme}
        setTheme={handleThemeChange}
        onViewChange={setCurrentView}
        currentView={currentView}
      />
      
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 md:hidden backdrop-blur-sm"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      <main className="md:ml-64 min-h-screen flex flex-col transition-all duration-300">
        
        {currentView === 'feed' ? (
          <>
            <FilterBar 
              filters={filters} 
              setFilters={setFilters} 
              onMenuClick={() => setIsMobileMenuOpen(true)}
              onRefresh={refreshFeed}
              onSaveBoard={handleSaveBoard}
            />

            <div className="flex-1 p-6 relative">
              
              {feedError && (
                <div className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                  <p className="font-semibold mb-1">Error loading feed:</p>
                  <p className="mb-2">
                    {feedError.networkError
                      ? 'Network error - please check your connection and try again.'
                      : feedError.graphQLErrors && feedError.graphQLErrors.length > 0
                      ? feedError.graphQLErrors[0].message
                      : feedError.message || 'An unexpected error occurred'}
                  </p>
                  <button 
                    onClick={() => refetchFeed()}
                    className="mt-2 px-3 py-1 bg-red-500/20 hover:bg-red-500/30 rounded text-xs transition-colors"
                  >
                    Retry
                  </button>
                  {import.meta.env.DEV && (
                    <details className="mt-2 text-xs opacity-75">
                      <summary className="cursor-pointer">Debug info</summary>
                      <pre className="mt-2 p-2 bg-black/20 rounded overflow-auto max-h-32">
                        {JSON.stringify(feedError, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              )}
              
              {loading && feedItems.length === 0 ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-app-muted gap-4">
                  <Loader2 className="w-10 h-10 animate-spin text-app-accent" />
                  <p className="text-sm font-medium animate-pulse">Curating your feed...</p>
                </div>
              ) : (
                <>
                  {feedItems.length === 0 && !feedLoading ? (
                    <div className="flex flex-col items-center justify-center py-20 text-app-muted gap-4">
                      <div className="w-16 h-16 rounded-full bg-app-surface flex items-center justify-center mb-2">
                        <RefreshCw className="w-6 h-6" />
                      </div>
                      <div className="text-center">
                        <p className="font-medium mb-1">No posts found</p>
                        <p className="text-sm opacity-75">
                          {filters.persons.length > 0 || filters.sources.length > 0 || filters.searchQuery
                            ? 'Try adjusting your filters or search query.'
                            : 'The feed appears to be empty. Check back later!'}
                        </p>
                      </div>
                      <button 
                        onClick={refreshFeed}
                        className="px-4 py-2 bg-app-accent hover:bg-app-accent-hover text-white rounded-full text-sm font-medium transition-colors"
                      >
                        Refresh Feed
                      </button>
                    </div>
                  ) : feedItems.length > 0 ? (
                    <div className="columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-6 space-y-6 mx-auto max-w-7xl">
                      {feedItems.map((item) => (
                        <FeedItem key={item.id} item={item} onClick={setSelectedItem} />
                      ))}
                    </div>
                  ) : null}
                </>
              )}

              {loading && feedItems.length > 0 && (
                <div className="fixed bottom-8 right-8 z-50 bg-app-accent text-white px-4 py-3 rounded-full shadow-lg flex items-center gap-3 animate-bounce-in">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm font-semibold">Updating...</span>
                </div>
              )}
            </div>
          </>
        ) : (
          /* Admin View */
          <EntityManager onBack={() => setCurrentView('feed')} />
        )}

      </main>
    
    {selectedItem && (
      <Lightbox
        item={selectedItem}
        onClose={() => setSelectedItem(null)}
      />
    )}
  </div>
);
}

/**
 * BunnyFeed component - provides feed view with filtering and boards
 * 
 * Requires AppProviders (ApolloProvider + ThemeProvider) to be provided
 * at a higher level (e.g., via BunnyFeedWrapper or layout).
 */
export default function BunnyFeed() {
  return <BunnyFeedContent />;
}

