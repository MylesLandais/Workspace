import { graphql, http, HttpResponse } from 'msw';
import { DEMO_BOARDS, DEMO_FEED_ITEMS } from '../../bunny/services/fixtures';
import { FEED_WITH_FILTERS, GET_SAVED_BOARDS } from '../queries';
import { CREATE_SAVED_BOARD, DELETE_SAVED_BOARD } from '../mutations';
import { loadSubredditData, type TransformedMedia } from '../../mock-data/loader';
import { loadPreTransformedMockData, type GraphQLFeedNode } from './pre-transformed-loader';
import type { FeedItem } from '../../bunny/types';

/**
 * MSW GraphQL handlers for development mocking
 * Uses actual mock data from /temp/mock_data/ when available, falls back to demo fixtures
 */

// Cache for loaded mock data
let cachedMockData: FeedItem[] | null = null;
let loadingPromise: Promise<FeedItem[]> | null = null;

// Load mock data from filesystem (async, lazy-loaded on first request)
// Start with a subset to avoid timeouts, can expand later
async function loadMockDataFromFiles(): Promise<FeedItem[]> {
  const startTime = performance.now();
  console.log('[MSW] loadMockDataFromFiles() called', {
    hasCache: !!cachedMockData,
    hasLoadingPromise: !!loadingPromise,
    cacheSize: cachedMockData?.length || 0,
    stack: new Error().stack?.split('\n').slice(1, 4).join('\n'),
  });
  
  if (cachedMockData) {
    console.log('[MSW] Returning cached data', { count: cachedMockData.length });
    return cachedMockData;
  }
  
  // If already loading, return the existing promise
  if (loadingPromise) {
    console.log('[MSW] Already loading, returning existing promise');
    return loadingPromise;
  }

  loadingPromise = (async () => {
    const loadStartTime = performance.now();
    try {
      console.log('[MSW] ========== Starting mock data load ==========');
      console.log('[MSW] Timestamp:', new Date().toISOString());
      console.log('[MSW] Call stack:', new Error().stack);
      
      // Load all posts from subreddits (not just latest 5)
      // Start with priority subreddits to avoid initial timeouts
      const prioritySubreddits = [
        'SelenaGomez',
        'TaylorSwift',
        'TaylorSwiftCandids',
        'TaylorSwiftMidriff',
        'Taylorhillfantasy',
        'ArianaGrande',
        'Pokimane',
        'SydneySweeney',
        'AddisonRae',
      ];
      
      console.log('[MSW] Priority subreddits:', prioritySubreddits);
      const feedItems: FeedItem[] = [];
      
      // Load subreddits sequentially to avoid overwhelming the browser
      for (let i = 0; i < prioritySubreddits.length; i++) {
        const subreddit = prioritySubreddits[i];
        const subredditStartTime = performance.now();
        try {
          console.log(`[MSW] [${i + 1}/${prioritySubreddits.length}] Loading ${subreddit}...`);
          const url = `/temp/mock_data/${subreddit}/json/${subreddit}_posts.json`;
          console.log(`[MSW] Fetching: ${url}`);
          
          const fetchStartTime = performance.now();
          const response = await fetch(url);
          const fetchTime = performance.now() - fetchStartTime;
          
          console.log(`[MSW] Fetch response for ${subreddit}:`, {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok,
            contentType: response.headers.get('content-type'),
            fetchTime: `${fetchTime.toFixed(2)}ms`,
          });
          
          if (!response.ok) {
            console.error(`[MSW] Failed to load ${subreddit}:`, {
              status: response.status,
              statusText: response.statusText,
              url,
            });
            continue;
          }
          
          const parseStartTime = performance.now();
          const data = await response.json();
          const parseTime = performance.now() - parseStartTime;
          
          console.log(`[MSW] Parsed JSON for ${subreddit}:`, {
            totalPosts: data.posts?.length || 0,
            subreddit: data.subreddit,
            parseTime: `${parseTime.toFixed(2)}ms`,
          });
          
          // Process all posts, not just latest 5
          const filterStartTime = performance.now();
          const imagePosts = data.posts?.filter((post: any) => {
            const hasImage = post.is_image && post.image_url;
            if (!hasImage && data.posts?.length < 10) {
              console.debug(`[MSW] Skipping post ${post.id}: is_image=${post.is_image}, image_url=${!!post.image_url}`);
            }
            return hasImage;
          }) || [];
          const filterTime = performance.now() - filterStartTime;
          
          console.log(`[MSW] Filtered image posts for ${subreddit}:`, {
            totalPosts: data.posts?.length || 0,
            imagePosts: imagePosts.length,
            filterTime: `${filterTime.toFixed(2)}ms`,
          });
          
          const mapStartTime = performance.now();
          const allPosts = imagePosts.map((post: any, idx: number) => {
            try {
              return {
                id: post.id,
                type: 'image' as const,
                caption: post.title || 'Untitled',
                author: {
                  name: post.author?.replace('/u/', '').replace('u/', '') || 'Unknown',
                  handle: post.author ? `u/${post.author.replace('/u/', '').replace('u/', '')}` : '',
                },
                source: `r/${data.subreddit}`,
                timestamp: new Date(post.created_utc).toISOString(),
                aspectRatio: 'aspect-square' as const,
                width: 600,
                height: 800,
                likes: post.score || 0,
                mediaUrl: post.image_url,
              };
            } catch (mapErr) {
              console.error(`[MSW] Error mapping post ${post.id} (index ${idx}):`, mapErr);
              if (mapErr instanceof Error) {
                console.error(`[MSW] Map error stack:`, mapErr.stack);
              }
              return null;
            }
          }).filter((item): item is FeedItem => item !== null);
          const mapTime = performance.now() - mapStartTime;
          
          if (allPosts.length > 0) {
            feedItems.push(...allPosts);
            const subredditTime = performance.now() - subredditStartTime;
            console.log(`[MSW] ✓ Loaded ${allPosts.length} items from ${subreddit}`, {
              totalSoFar: feedItems.length,
              subredditTime: `${subredditTime.toFixed(2)}ms`,
              sampleId: allPosts[0]?.id,
            });
          } else {
            console.warn(`[MSW] ⚠ No valid image posts found in ${subreddit}`, {
              totalPosts: data.posts?.length || 0,
              imagePosts: imagePosts.length,
            });
          }
        } catch (err) {
          const subredditTime = performance.now() - subredditStartTime;
          console.error(`[MSW] ✗ Failed to load ${subreddit}:`, {
            error: err,
            errorType: err?.constructor?.name,
            message: err instanceof Error ? err.message : String(err),
            stack: err instanceof Error ? err.stack : undefined,
            subredditTime: `${subredditTime.toFixed(2)}ms`,
          });
        }
      }
      
      const totalLoadTime = performance.now() - loadStartTime;
      
      if (feedItems.length === 0) {
        console.warn('[MSW] ⚠ No items loaded, falling back to demo fixtures', {
          totalLoadTime: `${totalLoadTime.toFixed(2)}ms`,
          attemptedSubreddits: prioritySubreddits.length,
        });
        return DEMO_FEED_ITEMS;
      }
      
      cachedMockData = feedItems;
      console.log('[MSW] ========== Mock data load complete ==========', {
        totalItems: feedItems.length,
        totalLoadTime: `${totalLoadTime.toFixed(2)}ms`,
        avgTimePerSubreddit: `${(totalLoadTime / prioritySubreddits.length).toFixed(2)}ms`,
      });
      console.log('[MSW] Sample items:', feedItems.slice(0, 3).map(item => ({
        id: item.id,
        source: item.source,
        caption: item.caption.substring(0, 50),
        mediaUrl: item.mediaUrl?.substring(0, 80),
      })));
      return feedItems;
    } catch (error) {
      const totalLoadTime = performance.now() - loadStartTime;
      console.error('[MSW] ========== CRITICAL ERROR loading mock data ==========', {
        error,
        errorType: error?.constructor?.name,
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        totalLoadTime: `${totalLoadTime.toFixed(2)}ms`,
      });
      console.warn('[MSW] Falling back to demo fixtures');
      return DEMO_FEED_ITEMS;
    } finally {
      loadingPromise = null;
      const totalTime = performance.now() - startTime;
      console.log('[MSW] loadMockDataFromFiles() completed', {
        totalTime: `${totalTime.toFixed(2)}ms`,
      });
    }
  })();
  
  return loadingPromise;
}

// Transform FeedItem array to GraphQL feed format
function transformFeedItems(feedItems: FeedItem[]) {
  return feedItems.map((item) => ({
    id: item.id,
    title: item.caption,
    imageUrl: item.mediaUrl,
    sourceUrl: `https://reddit.com/r/${item.source}`,
    publishDate: item.timestamp,
    score: item.likes,
    width: item.width,
    height: item.height,
    subreddit: {
      name: item.source.replace('r/', ''),
    },
    author: {
      username: item.author.name,
    },
    platform: 'REDDIT',
    handle: {
      name: item.source,
      handle: item.source,
    },
    mediaType: item.type.toUpperCase(), // Convert to uppercase to match backend enum
    viewCount: 0,
  }));
}

// Map person names to their subreddit names for filtering
function getSubredditsForPerson(personName: string): string[] {
  const personLower = personName.toLowerCase().trim();
  const mapping: Record<string, string[]> = {
    'taylor swift': ['TaylorSwift', 'TaylorSwiftCandids', 'TaylorSwiftMidriff', 'Taylorhillfantasy'],
    'selena gomez': ['SelenaGomez'],
    'ariana grande': ['ArianaGrande'],
    'addison rae': ['AddisonRae'],
    'pokimane': ['Pokimane'],
    'sydney sweeney': ['SydneySweeney'],
    'margot robbie': ['MargotRobbie'],
    'kendall jenner': ['kendalljenner'],
    'nina dobrev': ['NinaDobrev'],
    'natalie dormer': ['NatalieDormer'],
    'natalie portman': ['natalieportman'],
    'blake lively': ['blakelively'],
    'miranda kerr': ['MirandaKerr'],
    'vanessa hudgens': ['VanessaHudgens'],
    'victoria justice': ['victoriajustice'],
    'karlie kloss': ['karliekloss'],
    'kate upton': ['kateupton'],
    'jessica alba': ['jessicaalba'],
    'minka kelly': ['MinkaKelly'],
    'phoebe tonkin': ['PhoebeTonkin'],
    'shailene woodley': ['ShaileneWoodley'],
    'melissa benoist': ['MelissaBenoist'],
    'leighton meester': ['LeightonMeester'],
    'rachel mcadams': ['RachelMcAdams'],
    'anna kendrick': ['annakendrick'],
    'kristen bell': ['kristenbell'],
    'sophie turner': ['sophieturner'],
    'mckayla maroney': ['McKaylaMaroney'],
    'olivia rodrigo': ['OliviaRodrigoNSFW'],
    'hayden panettiere': ['haydenpanettiere'],
  };
  return mapping[personLower] || [];
}

// Filter GraphQL nodes based on filters (for pre-transformed data)
function filterGraphQLNodes(
  nodes: GraphQLFeedNode[],
  filters?: {
    persons?: string[];
    sources?: string[];
    searchQuery?: string;
  } | null
) {
  // Handle undefined, null, or empty filters - return all items
  if (!filters || Object.keys(filters).length === 0) {
    return nodes;
  }

  // Check if any filters are actually set
  const hasFilters = 
    (filters.persons && filters.persons.length > 0) ||
    (filters.sources && filters.sources.length > 0) ||
    (filters.searchQuery && filters.searchQuery.trim().length > 0);

  if (!hasFilters) {
    return nodes;
  }

  const queryLower = filters.searchQuery?.toLowerCase().trim() || '';

  return nodes.filter((node) => {
    // Person filter: check if subreddit matches any person's subreddits
    let personMatch = true;
    if (filters.persons && filters.persons.length > 0) {
      const matchingSubreddits = filters.persons.flatMap((person) =>
        getSubredditsForPerson(person)
      );
      personMatch = matchingSubreddits.includes(node.subreddit.name);
    }

    // Source filter: check if subreddit name matches
    const sourceMatch =
      !filters.sources ||
      filters.sources.length === 0 ||
      filters.sources.some((source) => {
        const sourceClean = source.replace(/^r\//, '').toLowerCase();
        return node.subreddit.name.toLowerCase() === sourceClean;
      });

    // Search query filter
    const searchMatch =
      !queryLower ||
      node.title.toLowerCase().includes(queryLower) ||
      node.subreddit.name.toLowerCase().includes(queryLower) ||
      node.author.username.toLowerCase().includes(queryLower);

    return personMatch && sourceMatch && searchMatch;
  });
}

// Filter feed items based on GraphQL filters (for runtime-transformed data)
function filterFeedItems(
  items: FeedItem[],
  filters?: {
    persons?: string[];
    sources?: string[];
    searchQuery?: string;
  } | null
) {
  // Handle undefined, null, or empty filters - return all items
  if (!filters || Object.keys(filters).length === 0) {
    return items;
  }

  // Check if any filters are actually set
  const hasFilters = 
    (filters.persons && filters.persons.length > 0) ||
    (filters.sources && filters.sources.length > 0) ||
    (filters.searchQuery && filters.searchQuery.trim().length > 0);

  if (!hasFilters) {
    return items;
  }

  const queryLower = filters.searchQuery?.toLowerCase().trim() || '';
  const personsLower = (filters.persons || []).map((p) => p.toLowerCase().trim());
  const sourcesLower = (filters.sources || []).map((s) => s.toLowerCase().replace('r/', '').trim());
  
  // Build set of subreddit names that match person filters
  const personSubreddits = new Set<string>();
  personsLower.forEach(person => {
    getSubredditsForPerson(person).forEach(sub => {
      personSubreddits.add(sub.toLowerCase());
    });
  });

  return items.filter((item) => {
    // Person filter - match by subreddit name (primary) or author/caption (fallback)
    const itemSourceName = item.source.toLowerCase().replace('r/', '');
    const personMatch =
      personsLower.length === 0 ||
      personSubreddits.has(itemSourceName) ||
      personsLower.some(
        (p) =>
          item.author.name.toLowerCase().includes(p.replace(/\s+/g, '')) ||
          item.caption.toLowerCase().includes(p)
      );

    // Source filter - match by source name (with or without r/ prefix)
    const sourceMatch =
      sourcesLower.length === 0 ||
      sourcesLower.some((s) => {
        const itemSourceLower = item.source.toLowerCase().replace('r/', '');
        return itemSourceLower.includes(s) || item.source.toLowerCase().includes(s);
      });

    // Search query filter
    const searchMatch =
      !queryLower ||
      item.caption.toLowerCase().includes(queryLower) ||
      item.source.toLowerCase().includes(queryLower) ||
      item.author.name.toLowerCase().includes(queryLower);

    return personMatch && sourceMatch && searchMatch;
  });
}

/**
 * Scenario-based testing support
 * Set via query variable: { scenario: 'empty-feed' }
 * Or via header: x-test-scenario: 'large-feed'
 */
async function getScenarioData(
  scenario: string | undefined,
  templates: any[]
): Promise<any[] | null> {
  if (!scenario) return null;
  
  // Import scenarios dynamically to avoid circular deps
  const { Scenarios } = await import('../../mock-data/article-factory');
  
  switch (scenario) {
    case 'empty-feed':
      return Scenarios.emptyFeed();
    case 'large-feed':
      return Scenarios.largeFeed(templates);
    case 'recent-only':
      return Scenarios.recentArticles(templates);
    case 'top-scoring':
      return Scenarios.topScoring(templates, 100);
    default:
      console.warn(`[MSW] Unknown scenario: ${scenario}`);
      return null;
  }
}

export const handlers = [
  // Feed query with filters
  graphql.query('FeedWithFilters', async (req, res, ctx) => {
    const handlerStartTime = performance.now();
    console.log('[MSW] ========== FeedWithFilters handler called ==========');
    console.log('[MSW] Request details:', {
      variables: req.variables,
      operationName: req.operationName,
      id: req.id,
      timestamp: new Date().toISOString(),
      url: req.url?.href,
      method: req.method,
      headers: Object.fromEntries(Object.entries(req.headers || {})),
    });
    console.log('[MSW] Handler call stack:', new Error().stack);
    
    try {
      const { filters, limit = 50, scenario } = req.variables || {};
      const scenarioHeader = req.headers.get('x-test-scenario');
      const activeScenario = scenario || scenarioHeader;
      
      console.log('[MSW] Processing with filters:', {
        filters: filters ? JSON.stringify(filters, null, 2) : 'none',
        limit,
        scenario: activeScenario || 'none',
      });
      
      // Check for scenario-based testing
      if (activeScenario) {
        // Load templates first (for scenario generation)
        const templates = await loadPreTransformedMockData('medium');
        if (templates.length === 0) {
          const feedItems = await loadMockDataFromFiles();
          // Transform to templates format
          const templateTemplates = transformFeedItems(feedItems);
          const scenarioData = await getScenarioData(activeScenario, templateTemplates);
          if (scenarioData) {
            const filtered = filterGraphQLNodes(scenarioData, filters);
            const response = {
              feed: {
                edges: filtered.slice(0, limit).map((node) => ({
                  node,
                  cursor: node.publishDate,
                })),
                pageInfo: {
                  hasNextPage: filtered.length > limit,
                  endCursor: filtered.length > 0 ? filtered[filtered.length - 1].publishDate : null,
                },
              },
            };
            console.log(`[MSW] Using scenario: ${activeScenario} (${filtered.length} items)`);
            return res(ctx.data(response));
          }
        } else {
          const scenarioData = await getScenarioData(activeScenario, templates);
          if (scenarioData) {
            const filtered = filterGraphQLNodes(scenarioData, filters);
            const response = {
              feed: {
                edges: filtered.slice(0, limit).map((node) => ({
                  node,
                  cursor: node.publishDate,
                })),
                pageInfo: {
                  hasNextPage: filtered.length > limit,
                  endCursor: filtered.length > 0 ? filtered[filtered.length - 1].publishDate : null,
                },
              },
            };
            console.log(`[MSW] Using scenario: ${activeScenario} (${filtered.length} items)`);
            return res(ctx.data(response));
          }
        }
      }
      
      // Try loading pre-transformed GraphQL data first (faster, schema-compliant)
      const loadStartTime = performance.now();
      console.log('[MSW] Attempting to load pre-transformed GraphQL data...');
      let preTransformedNodes = await loadPreTransformedMockData('medium');
      
      let transformed: any[];
      let filteredCount = 0;
      let loadTime = 0;
      let filterTime = 0;
      let transformTime = 0;
      
      if (preTransformedNodes.length > 0) {
        // Use pre-transformed data (already in GraphQL format)
        console.log('[MSW] Using pre-transformed GraphQL data');
        loadTime = performance.now() - loadStartTime;
        
        // Filter pre-transformed nodes
        const filterStartTime = performance.now();
        const filtered = filterGraphQLNodes(preTransformedNodes, filters);
        filterTime = performance.now() - filterStartTime;
        filteredCount = filtered.length;
        console.log(`[MSW] After filtering: ${filtered.length} items`, {
          originalCount: preTransformedNodes.length,
          filterTime: `${filterTime.toFixed(2)}ms`,
        });
        
        // Already in GraphQL format, just slice
        transformed = filtered.slice(0, limit);
        transformTime = 0; // No transformation needed
      } else {
        // Fallback to runtime transformation from raw Reddit JSON
        console.log('[MSW] Pre-transformed data not available, using runtime transformation');
        const feedItems = await loadMockDataFromFiles();
        loadTime = performance.now() - loadStartTime;
        console.log(`[MSW] Loaded ${feedItems.length} total items`, {
          loadTime: `${loadTime.toFixed(2)}ms`,
        });
        
        const filterStartTime = performance.now();
        const filtered = filterFeedItems(feedItems, filters);
        filterTime = performance.now() - filterStartTime;
        filteredCount = filtered.length;
        console.log(`[MSW] After filtering: ${filtered.length} items`, {
          originalCount: feedItems.length,
          filterTime: `${filterTime.toFixed(2)}ms`,
        });
        
        const transformStartTime = performance.now();
        transformed = transformFeedItems(filtered.slice(0, limit));
        transformTime = performance.now() - transformStartTime;
        console.log(`[MSW] Transformed ${transformed.length} items`, {
          transformTime: `${transformTime.toFixed(2)}ms`,
        });
      }

      const response = {
        feed: {
          edges: transformed.map((node) => ({
            node,
            cursor: node.publishDate,
          })),
          pageInfo: {
            hasNextPage: filteredCount > limit,
            endCursor: transformed.length > 0 ? transformed[transformed.length - 1].publishDate : null,
          },
        },
      };
      
      const totalTime = performance.now() - handlerStartTime;
      console.log('[MSW] ========== FeedWithFilters response ready ==========', {
        edgesCount: response.feed.edges.length,
        hasNextPage: response.feed.pageInfo.hasNextPage,
        endCursor: response.feed.pageInfo.endCursor,
        totalTime: `${totalTime.toFixed(2)}ms`,
        breakdown: {
          load: `${loadTime.toFixed(2)}ms`,
          filter: `${filterTime.toFixed(2)}ms`,
          transform: `${transformTime.toFixed(2)}ms`,
        },
      });
      console.log('[MSW] Sample response nodes:', response.feed.edges.slice(0, 2).map(edge => ({
        id: edge.node.id,
        title: edge.node.title?.substring(0, 50),
        imageUrl: edge.node.imageUrl?.substring(0, 80),
      })));
      
      return res(ctx.data(response));
    } catch (error) {
      const totalTime = performance.now() - handlerStartTime;
      console.error('[MSW] ========== ERROR in FeedWithFilters handler ==========', {
        error,
        errorType: error?.constructor?.name,
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        totalTime: `${totalTime.toFixed(2)}ms`,
        variables: req.variables,
      });
      return res(ctx.errors([{ 
        message: `Failed to load feed data: ${error instanceof Error ? error.message : String(error)}`,
        extensions: {
          code: 'INTERNAL_SERVER_ERROR',
          stack: error instanceof Error ? error.stack : undefined,
        },
      }]));
    }
  }),

  // Feed query without filters (legacy)
  graphql.query('Feed', async (req, res, ctx) => {
    try {
      const { limit = 50 } = req.variables || {};
      // Load real mock data (lazy-loaded and cached)
      const feedItems = await loadMockDataFromFiles();
      const transformed = transformFeedItems(feedItems.slice(0, limit));

      return res(
        ctx.data({
          feed: {
            edges: transformed.map((node) => ({
              node,
              cursor: node.publishDate,
            })),
            pageInfo: {
              hasNextPage: feedItems.length > limit,
              endCursor: transformed.length > 0 ? transformed[transformed.length - 1].publishDate : null,
            },
          },
        })
      );
    } catch (error) {
      console.error('[MSW] Error in Feed handler:', error);
      return res(ctx.errors([{ message: 'Failed to load feed data' }]));
    }
  }),

  // Get saved boards
  graphql.query('GetSavedBoards', (req, res, ctx) => {
    const { userId } = req.variables || {};
    const boards = DEMO_BOARDS.map((board) => ({
      id: board.id,
      name: board.name,
      filters: board.filters,
      createdAt: new Date(board.createdAt).toISOString(),
      userId: userId || 'default-user',
    }));

    return res(
      ctx.data({
        getSavedBoards: boards,
      })
    );
  }),

  // Create saved board
  graphql.mutation('CreateSavedBoard', (req, res, ctx) => {
    const { userId, input } = req.variables || {};
    const newBoard = {
      id: `board-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: input.name,
      filters: input.filters,
      createdAt: new Date().toISOString(),
      userId: userId || 'default-user',
    };

    return res(
      ctx.data({
        createSavedBoard: newBoard,
      })
    );
  }),

  // Update saved board
  graphql.mutation('UpdateSavedBoard', (req, res, ctx) => {
    const { id, input } = req.variables || {};
    const updatedBoard = {
      id,
      name: input.name,
      filters: input.filters,
      createdAt: new Date().toISOString(),
      userId: 'default-user',
    };

    return res(
      ctx.data({
        updateSavedBoard: updatedBoard,
      })
    );
  }),

  // Delete saved board
  graphql.mutation('DeleteSavedBoard', (req, res, ctx) => {
    return res(
      ctx.data({
        deleteSavedBoard: true,
      })
    );
  }),

  // Fallback HTTP handler to catch any GraphQL requests that might not match the graphql.query handlers
  // This ensures MSW intercepts all requests to the GraphQL endpoint
  http.post('*/api/graphql', async ({ request }) => {
    console.log('[MSW] ========== HTTP fallback handler caught GraphQL request ==========');
    console.log('[MSW] Request URL:', request.url);
    console.log('[MSW] Request method:', request.method);
    
    try {
      const body = await request.json() as any;
      const operationName = body.operationName || body.query?.match(/query\s+(\w+)/)?.[1];
      
      console.log('[MSW] Fallback handler - operation:', operationName);
      console.log('[MSW] Fallback handler - body:', JSON.stringify(body, null, 2));
      
      // If it's FeedWithFilters, we should handle it, but this means graphql.query handler didn't match
      if (operationName === 'FeedWithFilters' || body.query?.includes('FeedWithFilters')) {
        console.warn('[MSW] WARNING: FeedWithFilters request caught by fallback handler - graphql.query handler should have caught this!');
        
        // Load and return actual data
        const feedItems = await loadMockDataFromFiles();
        const filtered = filterFeedItems(feedItems, body.variables?.filters);
        const transformed = transformFeedItems(filtered.slice(0, body.variables?.limit || 50));
        
        return HttpResponse.json({
          data: {
            feed: {
              edges: transformed.map((node) => ({ node, cursor: node.publishDate })),
              pageInfo: {
                hasNextPage: filtered.length > (body.variables?.limit || 50),
                endCursor: transformed.length > 0 ? transformed[transformed.length - 1].publishDate : null,
              },
            },
          },
        });
      }
      
      // For other operations, return empty
      console.warn('[MSW] Unhandled operation in fallback:', operationName);
      return HttpResponse.json({ data: {} });
    } catch (error) {
      console.error('[MSW] Fallback handler error:', error);
      return HttpResponse.json(
        { errors: [{ message: 'MSW fallback handler error' }] },
        { status: 500 }
      );
    }
  }),
];

