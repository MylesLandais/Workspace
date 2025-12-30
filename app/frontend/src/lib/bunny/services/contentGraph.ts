import { IdentityProfile } from '../types';
import { DEMO_IDENTITIES } from './fixtures';
import { apolloClient } from '../../graphql/client';
import { GET_IDENTITY_PROFILES, GET_IDENTITY_PROFILE } from '../../graphql/queries';

const DEFAULT_GRAPH: Record<string, IdentityProfile> = DEMO_IDENTITIES;

const GENERAL_IMAGES = [
  "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1551806235-a79ac77aa5b1?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1469334031218-e382a71b716b?auto=format&fit=crop&w=800&q=80",
];

// --- GraphQL-based Accessors ---

let identityGraphCache: Record<string, IdentityProfile> | null = null;

export const getIdentityGraph = async (): Promise<Record<string, IdentityProfile>> => {
  if (typeof window === 'undefined') return DEFAULT_GRAPH;
  
  // Return cache if available
  if (identityGraphCache) return identityGraphCache;
  
  try {
    const { data } = await apolloClient.query({
      query: GET_IDENTITY_PROFILES,
      variables: { limit: 100 },
      fetchPolicy: 'cache-first',
    });
    
    if (data?.getIdentityProfiles) {
      const graph: Record<string, IdentityProfile> = {};
      data.getIdentityProfiles.forEach((profile: IdentityProfile) => {
        graph[profile.id] = profile;
      });
      identityGraphCache = graph;
      return graph;
    }
  } catch (error) {
    console.warn('Failed to load identity profiles from GraphQL, using demo data:', error);
  }
  
  return DEFAULT_GRAPH;
};

export const saveIdentityGraph = async (graph: Record<string, IdentityProfile>) => {
  // GraphQL mutations handle persistence, this is just for cache invalidation
  if (typeof window === 'undefined') return;
  identityGraphCache = graph;
  window.dispatchEvent(new Event('bunny_graph_update'));
};

// --- Helpers ---

/**
 * Finds a matching profile from a search string or name
 */
export const findIdentity = async (query: string): Promise<IdentityProfile | null> => {
  const graph = await getIdentityGraph();
  const normalized = query.toLowerCase().trim();
  const foundKey = Object.keys(graph).find(key => {
    const profile = graph[key];
    return profile.name.toLowerCase().includes(normalized) ||
           profile.aliases.some(alias => alias.toLowerCase().includes(normalized));
  });
  return foundKey ? graph[foundKey] : null;
};

/**
 * Gets a randomized image from the pool
 */
export const getIdentityImage = async (profileId: string): Promise<string> => {
  const graph = await getIdentityGraph();
  const profile = graph[profileId];
  if (!profile || profile.imagePool.length === 0) return GENERAL_IMAGES[Math.floor(Math.random() * GENERAL_IMAGES.length)];
  
  const randomIndex = Math.floor(Math.random() * profile.imagePool.length);
  return profile.imagePool[randomIndex];
};

/**
 * Helper to build AI Context
 */
export const getContextForFilters = async (persons: string[]): Promise<string> => {
  const graph = await getIdentityGraph();
  const contexts: string[] = [];
  for (const p of persons) {
    const profile = await findIdentity(p);
    if (profile) {
      // Find main handles
      const insta = profile.sources.find(s => s.platform === 'instagram')?.id || '';
      const reddit = profile.sources.find(s => s.platform === 'reddit')?.id || '';
      contexts.push(`For ${profile.name}, focus on: ${profile.contextKeywords.join(', ')}. Use handles like ${insta} or subreddit r/${reddit}.`);
    }
  }
  return contexts.join('\n');
};

export const IDENTITY_GRAPH = DEFAULT_GRAPH;

