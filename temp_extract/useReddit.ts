import { useState, useEffect, useCallback } from 'react';
import type { 
  RedditPost, 
  RedditPostDetails, 
  RedditSubreddit, 
  RedditStats,
  PostsQueryParams 
} from '@/lib/types/reddit';

const API_BASE = process.env.NEXT_PUBLIC_REDDIT_API_URL || 'http://localhost:8001';

interface UseRedditOptions {
  /** Auto-fetch on mount */
  immediate?: boolean;
  /** Retry failed requests */
  retryCount?: number;
  /** Retry delay in ms */
  retryDelay?: number;
}

interface UseRedditResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

/**
 * Custom fetch wrapper with error handling and retries
 */
async function redditFetch<T>(
  endpoint: string, 
  retries = 3, 
  delay = 1000
): Promise<T> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      if (attempt < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * (attempt + 1)));
      }
    }
  }
  
  throw lastError || new Error('Request failed');
}

/**
 * Hook: Fetch all posts with optional filters
 */
export function useRedditPosts(
  params: PostsQueryParams = {},
  options: UseRedditOptions = {}
): UseRedditResult<RedditPost[]> {
  const { immediate = true, retryCount = 3, retryDelay = 1000 } = options;
  const [data, setData] = useState<RedditPost[] | null>(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<Error | null>(null);

  const buildQueryString = useCallback(() => {
    const searchParams = new URLSearchParams();
    if (params.subreddit) searchParams.set('subreddit', params.subreddit);
    if (params.min_score !== undefined) searchParams.set('min_score', String(params.min_score));
    if (params.is_image !== undefined) searchParams.set('is_image', String(params.is_image));
    if (params.limit !== undefined) searchParams.set('limit', String(params.limit));
    if (params.offset !== undefined) searchParams.set('offset', String(params.offset));
    const qs = searchParams.toString();
    return qs ? `?${qs}` : '';
  }, [params.subreddit, params.min_score, params.is_image, params.limit, params.offset]);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await redditFetch<RedditPost[]>(
        `/posts${buildQueryString()}`,
        retryCount,
        retryDelay
      );
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [buildQueryString, retryCount, retryDelay]);

  useEffect(() => {
    if (immediate) {
      refetch();
    }
  }, [immediate, refetch]);

  return { data, loading, error, refetch };
}

/**
 * Hook: Fetch single post with comments and images
 */
export function useRedditPost(
  postId: string | null,
  options: UseRedditOptions = {}
): UseRedditResult<RedditPostDetails> {
  const { immediate = true, retryCount = 3, retryDelay = 1000 } = options;
  const [data, setData] = useState<RedditPostDetails | null>(null);
  const [loading, setLoading] = useState(immediate && !!postId);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    if (!postId) {
      setData(null);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await redditFetch<RedditPostDetails>(
        `/post/${postId}`,
        retryCount,
        retryDelay
      );
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [postId, retryCount, retryDelay]);

  useEffect(() => {
    if (immediate && postId) {
      refetch();
    }
  }, [immediate, postId, refetch]);

  return { data, loading, error, refetch };
}

/**
 * Hook: Fetch posts by subreddit
 */
export function useSubredditPosts(
  subredditName: string | null,
  limit = 20,
  options: UseRedditOptions = {}
): UseRedditResult<RedditPost[]> {
  const { immediate = true, retryCount = 3, retryDelay = 1000 } = options;
  const [data, setData] = useState<RedditPost[] | null>(null);
  const [loading, setLoading] = useState(immediate && !!subredditName);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    if (!subredditName) {
      setData(null);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await redditFetch<RedditPost[]>(
        `/subreddit/${subredditName}/posts?limit=${limit}`,
        retryCount,
        retryDelay
      );
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [subredditName, limit, retryCount, retryDelay]);

  useEffect(() => {
    if (immediate && subredditName) {
      refetch();
    }
  }, [immediate, subredditName, refetch]);

  return { data, loading, error, refetch };
}

/**
 * Hook: Fetch all subreddits
 */
export function useSubreddits(
  options: UseRedditOptions = {}
): UseRedditResult<RedditSubreddit[]> {
  const { immediate = true, retryCount = 3, retryDelay = 1000 } = options;
  const [data, setData] = useState<RedditSubreddit[] | null>(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await redditFetch<RedditSubreddit[]>(
        '/subreddits',
        retryCount,
        retryDelay
      );
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [retryCount, retryDelay]);

  useEffect(() => {
    if (immediate) {
      refetch();
    }
  }, [immediate, refetch]);

  return { data, loading, error, refetch };
}

/**
 * Hook: Fetch API stats
 */
export function useRedditStats(
  options: UseRedditOptions = {}
): UseRedditResult<RedditStats> {
  const { immediate = true, retryCount = 3, retryDelay = 1000 } = options;
  const [data, setData] = useState<RedditStats | null>(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await redditFetch<RedditStats>(
        '/stats',
        retryCount,
        retryDelay
      );
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [retryCount, retryDelay]);

  useEffect(() => {
    if (immediate) {
      refetch();
    }
  }, [immediate, refetch]);

  return { data, loading, error, refetch };
}
