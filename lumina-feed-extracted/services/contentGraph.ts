import { IdentityProfile, MediaType, SourceLink } from '../types';
import { DEMO_IDENTITIES } from './fixtures';

const DEFAULT_GRAPH: Record<string, IdentityProfile> = DEMO_IDENTITIES;

const GENERAL_IMAGES = [
  "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1551806235-a79ac77aa5b1?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1469334031218-e382a71b716b?auto=format&fit=crop&w=800&q=80",
];

const STORAGE_KEY = 'lumina_identity_graph';

// --- Persistent Accessors ---

export const getIdentityGraph = (): Record<string, IdentityProfile> => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : DEFAULT_GRAPH;
  } catch {
    return DEFAULT_GRAPH;
  }
};

export const saveIdentityGraph = (graph: Record<string, IdentityProfile>) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(graph));
  window.dispatchEvent(new Event('lumina_graph_update'));
};

// --- Helpers ---

/**
 * Finds a matching profile from a search string or name
 */
export const findIdentity = (query: string): IdentityProfile | null => {
  const graph = getIdentityGraph();
  const normalized = query.toLowerCase().trim();
  const foundKey = Object.keys(graph).find(key => {
    const profile = graph[key];
    return profile.aliases.some(alias => normalized.includes(alias));
  });
  return foundKey ? graph[foundKey] : null;
};

/**
 * Gets a randomized image from the pool
 */
export const getIdentityImage = (profileId: string): string => {
  const graph = getIdentityGraph();
  const profile = graph[profileId];
  if (!profile || profile.imagePool.length === 0) return GENERAL_IMAGES[Math.floor(Math.random() * GENERAL_IMAGES.length)];
  
  const randomIndex = Math.floor(Math.random() * profile.imagePool.length);
  return profile.imagePool[randomIndex];
};

/**
 * Helper to build AI Context
 */
export const getContextForFilters = (persons: string[]): string => {
  const graph = getIdentityGraph();
  const contexts: string[] = [];
  persons.forEach(p => {
    const profile = findIdentity(p);
    if (profile) {
      // Find main handles
      const insta = profile.sources.find(s => s.platform === 'instagram')?.id || '';
      const reddit = profile.sources.find(s => s.platform === 'reddit')?.id || '';
      contexts.push(`For ${profile.name}, focus on: ${profile.contextKeywords.join(', ')}. Use handles like ${insta} or subreddit r/${reddit}.`);
    }
  });
  return contexts.join('\n');
};

export const IDENTITY_GRAPH = DEFAULT_GRAPH;