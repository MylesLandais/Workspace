import { GoogleGenAI, Type } from "@google/genai";
import { FeedItem, MediaType } from '../types';
import { findIdentity, IDENTITY_GRAPH, getIdentityImage, getContextForFilters } from './contentGraph';
import { getDemoItemsForFilters } from './fixtures';

const apiKey = typeof window !== 'undefined' ? (import.meta.env.VITE_GEMINI_API_KEY || '') : '';
const ai = apiKey ? new GoogleGenAI({ apiKey }) : null;

// --- Helper Types for Reddit API ---
interface RedditPost {
  data: {
    id: string;
    title: string;
    author: string;
    subreddit_name_prefixed: string;
    url: string;
    score: number;
    created_utc: number;
    post_hint?: string;
    preview?: {
      images: Array<{
        source: { url: string; width: number; height: number };
      }>;
    };
    is_gallery?: boolean;
    media_metadata?: Record<string, { s: { u: string; x: number; y: number } }>;
    gallery_data?: { items: Array<{ media_id: string }> };
  };
}

// --- Core Logic ---

export const generateFeedItems = async (
  query: string,
  persons: string[],
  sources: string[]
): Promise<FeedItem[]> => {
  
  try {
    // 1. Determine Fetch Strategy
    let redditPromises: Promise<FeedItem[]>[] = [];

    // Strategy A: Filter by Persons (Map to ALL Subreddits in their sources)
    if (persons.length > 0) {
      persons.forEach(personName => {
        const identity = findIdentity(personName);
        if (identity && identity.sources) {
          // Fetch ALL mapped subreddits for this person, EXCEPT hidden ones
          identity.sources
            .filter(src => src.platform === 'reddit' && !src.hidden)
            .forEach(src => {
               const sub = src.id.replace('r/', '');
               redditPromises.push(fetchSubreddit(sub));
            });
        }
      });
    }

    // Strategy B: Filter by Explicit Sources (e.g. Saved Boards with 'r/unixporn')
    if (sources.length > 0) {
      sources.forEach(src => {
        // Handle subreddit specific sources
        if (src.toLowerCase().startsWith('r/')) {
           redditPromises.push(fetchSubreddit(src.replace('r/', '')));
        }
      });
    }

    // Strategy C: Search Query
    if (query.trim().length > 0) {
      redditPromises.push(searchReddit(query));
    }

    // Strategy D: Default / Explore (If no specific filters)
    if (persons.length === 0 && query.trim().length === 0 && sources.length === 0) {
      const DEFAULT_SUBS = ['popculturechat', 'Fauxmoi', 'pics', 'itookapicture', 'StreetwearFits', 'unixporn'];
      // Randomly pick 2 to keep it fresh but not overwhelming
      const randomSubs = DEFAULT_SUBS.sort(() => 0.5 - Math.random()).slice(0, 2);
      randomSubs.forEach(sub => redditPromises.push(fetchSubreddit(sub)));
    }

    // 2. Execute Fetches
    // Note: If no API key is present or we are offline, these fetch calls might fail or return empty.
    // We catch errors per-request to ensure partial success.
    const results = await Promise.all(redditPromises);
    let items = results.flat();

    // 3. Deduplicate (by ID)
    const seen = new Set();
    items = items.filter(item => {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });

    // 4. Shuffle (Fisher-Yates) for that "organic feed" feel
    for (let i = items.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [items[i], items[j]] = [items[j], items[i]];
    }

    // 5. Fallback & Demo Mode
    // If Reddit is blocked/down/empty OR we just want to ensure we have content for specific demo scenarios:
    if (items.length === 0) {
        // Only warn if we actually tried to fetch something
        if (redditPromises.length > 0) {
            console.warn("Live data unavailable, attempting fallback.");
        }
        return await generateMockItems(query, persons, sources);
    }

    return items;

  } catch (error) {
    console.error("Error generating feed:", error);
    // Fallback to mock on crash
    return await generateMockItems(query, persons, sources);
  }
};

// --- Reddit API Helpers ---

const fetchSubreddit = async (subreddit: string): Promise<FeedItem[]> => {
  try {
    const response = await fetch(`https://www.reddit.com/r/${subreddit}/hot.json?limit=25`);
    if (!response.ok) throw new Error(`Failed to fetch r/${subreddit}`);
    const json = await response.json();
    return parseRedditResponse(json, subreddit);
  } catch (e) {
    // console.error(e); // Suppress errors for cleaner console in demo mode
    return [];
  }
};

const searchReddit = async (query: string): Promise<FeedItem[]> => {
  try {
    const response = await fetch(`https://www.reddit.com/search.json?q=${encodeURIComponent(query)}&sort=relevance&limit=25&type=link`);
    if (!response.ok) throw new Error(`Failed to search reddit for ${query}`);
    const json = await response.json();
    return parseRedditResponse(json, 'Reddit Search');
  } catch (e) {
    return [];
  }
};

const parseRedditResponse = (json: any, sourceLabel: string): FeedItem[] => {
  const posts: RedditPost[] = json?.data?.children || [];
  
  return posts
    .map((post): FeedItem | null => {
      const { data } = post;
      
      // Determine Media Type & URL
      let mediaUrl: string | null = null;
      let width = 600;
      let height = 800; // Default
      let type = MediaType.IMAGE;

      // Case 1: Direct Image
      if (data.url.match(/\.(jpg|jpeg|png|gif)$/i)) {
        mediaUrl = data.url;
        if (data.url.endsWith('.gif')) type = MediaType.GIF;
      } 
      // Case 2: Reddit Gallery (Take first image)
      else if (data.is_gallery && data.media_metadata) {
        // Try to get the highest res image from the first gallery item
        const firstId = data.gallery_data?.items[0]?.media_id;
        if (firstId && data.media_metadata[firstId]) {
            const meta = data.media_metadata[firstId];
            // 's' is the source (highest res), usually has 'u' (url)
            mediaUrl = meta.s.u.replace(/&amp;/g, '&'); // Fix Reddit XML encoding
            width = meta.s.x;
            height = meta.s.y;
        }
      }
      // Case 3: Reddit Video / Preview Image fallback
      else if (data.preview?.images?.[0]?.source) {
        const source = data.preview.images[0].source;
        mediaUrl = source.url.replace(/&amp;/g, '&');
        width = source.width;
        height = source.height;
        if (data.post_hint === 'hosted:video') type = MediaType.SHORT;
      }

      if (!mediaUrl) return null; // Skip text-only posts

      return {
        id: data.id,
        type: type,
        caption: data.title,
        author: {
          name: data.author,
          handle: `u/${data.author}`,
        },
        source: `r/${data.subreddit_name_prefixed.replace('r/', '') || sourceLabel}`, // Ensure clean r/Name
        timestamp: new Date(data.created_utc * 1000).toISOString(),
        aspectRatio: calculateAspectRatioClass(width, height),
        width: width,
        height: height,
        likes: data.score,
        mediaUrl: mediaUrl
      };
    })
    .filter((item): item is FeedItem => item !== null);
};

const calculateAspectRatioClass = (w: number, h: number): string => {
  if (!w || !h) return 'aspect-square';
  const ratio = w / h;
  if (ratio > 1.2) return 'aspect-video'; // Landscape
  if (ratio < 0.8) return 'aspect-[3/4]'; // Portrait
  return 'aspect-square'; // Squareish
};

// --- Mock Fallback (Hybrid: Local Fixtures + Gemini) ---

const feedResponseSchema = {
    type: Type.OBJECT,
    properties: {
      items: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            id: { type: Type.STRING },
            type: { type: Type.STRING, enum: ['image', 'short', 'gif'] },
            caption: { type: Type.STRING },
            authorName: { type: Type.STRING },
            authorHandle: { type: Type.STRING },
            sourcePlatform: { type: Type.STRING },
            likes: { type: Type.INTEGER },
            width: { type: Type.INTEGER },
            height: { type: Type.INTEGER },
            identityMatch: { type: Type.STRING }
          },
          required: ['id', 'type', 'caption', 'authorName', 'sourcePlatform'],
        },
      },
    },
  };

const generateMockItems = async (query: string, persons: string[], sources: string[]): Promise<FeedItem[]> => {
    
    // 1. Try Local Fixtures First (Deterministic, Offline-Capable)
    // This ensures specific demos (like "Linux Rice") always return realistic looking high-quality data
    // even without an internet connection or API keys.
    const localMatches = getDemoItemsForFilters(query, persons, sources);
    if (localMatches.length > 0) {
        console.log("Serving offline/demo content from fixtures.");
        return localMatches;
    }

    // 2. Try Gemini Generation (If API Key exists)
    if (ai && apiKey) {
      const graphContext = getContextForFilters(persons);
      const contextDescription = `
        Generate 8 mock social media posts.
        Filters: ${persons.join(', ')} ${query}
        Sources: ${sources.join(', ')}
        Context: ${graphContext}
      `;
    
      try {
        const response = await ai.models.generateContent({
          model: "gemini-3-flash-preview",
          contents: contextDescription,
          config: {
            responseMimeType: "application/json",
            responseSchema: feedResponseSchema,
          }
        });
    
        const text = response.text;
        if (text) {
           const data = JSON.parse(text);
           return data.items.map((item: any, index: number) => {
            let imageUrl = `https://picsum.photos/seed/${item.id}/${item.width || 600}/${item.height || 800}`;
            let identity = item.identityMatch ? IDENTITY_GRAPH[item.identityMatch] : null;
            if (!identity) identity = findIdentity(item.authorName) || findIdentity(item.caption);
            if (identity) imageUrl = getIdentityImage(identity.id);
      
            return {
              id: item.id || `gen-${Date.now()}-${index}`,
              type: MediaType.IMAGE,
              caption: item.caption,
              author: { name: item.authorName, handle: item.authorHandle },
              source: item.sourcePlatform,
              timestamp: new Date().toISOString(),
              aspectRatio: calculateAspectRatioClass(item.width, item.height),
              width: item.width || 600,
              height: item.height || 800,
              likes: item.likes || 100,
              mediaUrl: imageUrl 
            };
          });
        }
      } catch (e) {
        console.error("Mock gen failed", e);
      }
    }
    
    // 3. Fallback to generic randomness if all else fails
    return [];
};

