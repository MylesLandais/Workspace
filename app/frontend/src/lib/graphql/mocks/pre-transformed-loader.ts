/**
 * Load pre-transformed GraphQL mock data
 * 
 * This module loads pre-transformed GraphQL-formatted data files that were
 * generated from raw Reddit JSON using the generate-graphql-mock-data script.
 * 
 * This provides:
 * - Faster loading (no runtime transformation)
 * - Guaranteed schema compliance (data matches GraphQL schema exactly)
 * - Easier testing (same data structure as real API)
 */

export interface GraphQLFeedNode {
  id: string;
  title: string;
  imageUrl: string | null;
  sourceUrl: string;
  publishDate: string;
  score: number;
  width: number | null;
  height: number | null;
  subreddit: {
    name: string;
  };
  author: {
    username: string;
  };
  platform: 'REDDIT';
  handle: {
    name: string;
    handle: string;
  };
  mediaType: 'IMAGE' | 'VIDEO' | 'TEXT';
  viewCount: number;
}

export interface GraphQLFeedEdge {
  node: GraphQLFeedNode;
  cursor: string;
}

export interface GraphQLFeedConnection {
  edges: GraphQLFeedEdge[];
  pageInfo: {
    hasNextPage: boolean;
    endCursor: string | null;
  };
}

let cachedPreTransformedData: GraphQLFeedNode[] | null = null;
let loadingPreTransformedPromise: Promise<GraphQLFeedNode[]> | null = null;

/**
 * Load pre-transformed GraphQL mock data
 * 
 * @param size Dataset size: 'small', 'medium', or 'large' (default: 'medium')
 * @returns Array of GraphQL feed nodes
 */
export async function loadPreTransformedMockData(
  size: 'small' | 'medium' | 'large' = 'medium'
): Promise<GraphQLFeedNode[]> {
  // Return cache if available
  if (cachedPreTransformedData) {
    console.log('[MSW] Using cached pre-transformed data', {
      count: cachedPreTransformedData.length,
    });
    return cachedPreTransformedData;
  }

  // Return existing promise if already loading
  if (loadingPreTransformedPromise) {
    console.log('[MSW] Already loading pre-transformed data, returning existing promise');
    return loadingPreTransformedPromise;
  }

  // Start loading
  loadingPreTransformedPromise = (async () => {
    const startTime = performance.now();
    console.log('[MSW] ========== Loading pre-transformed GraphQL mock data ==========');
    console.log('[MSW] Dataset size:', size);

    try {
      const url = `/temp/graphql-mock-data/feed-${size}.json`;
      console.log('[MSW] Fetching pre-transformed data from:', url);

      const response = await fetch(url);

      if (!response.ok) {
        console.warn(
          `[MSW] Pre-transformed data not found (${response.status}), will use runtime transformation`,
          { url }
        );
        // Return empty array to trigger fallback to runtime transformation
        return [];
      }

      const feedConnection: GraphQLFeedConnection = await response.json();

      // Extract nodes from edges
      const nodes = feedConnection.edges.map((edge) => edge.node);

      console.log(`[MSW] ✓ Loaded ${nodes.length} pre-transformed nodes in ${(performance.now() - startTime).toFixed(2)}ms`);
      console.log('[MSW] Sample nodes:', nodes.slice(0, 3).map((n) => ({ id: n.id, title: n.title.substring(0, 50) })));

      // Cache the data
      cachedPreTransformedData = nodes;
      return nodes;
    } catch (error) {
      console.error('[MSW] Failed to load pre-transformed data, will use runtime transformation:', error);
      // Return empty array to trigger fallback to runtime transformation
      return [];
    }
  })();

  return loadingPreTransformedPromise;
}

/**
 * Check if pre-transformed data is available
 */
export async function hasPreTransformedData(
  size: 'small' | 'medium' | 'large' = 'medium'
): Promise<boolean> {
  try {
    const url = `/temp/graphql-mock-data/feed-${size}.json`;
    const response = await fetch(url, { method: 'HEAD' });
    return response.ok;
  } catch {
    return false;
  }
}




