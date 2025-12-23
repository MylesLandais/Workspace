/**
 * Board Configuration System
 * 
 * Manages filter configurations for different feed views/boards.
 * Supports entity-level filtering (e.g., "hide Brooke Monk from tiktokfeet")
 */

export interface EntityFilter {
  entityId: string;
  entityName: string;
  blockedSources: Set<string>; // Sources/subreddits where this entity is blocked
}

export interface BoardConfig {
  id: string;
  name: string;
  enabledSources: Set<string>; // Subreddit/platform handles that are enabled
  blockedEntities: Map<string, EntityFilter>; // entityId -> EntityFilter
  createdAt: string;
  updatedAt: string;
}

const DEFAULT_BOARD_ID = 'default';
const STORAGE_KEY_PREFIX = 'feed-board-config-';

export function getBoardConfig(boardId: string = DEFAULT_BOARD_ID): BoardConfig {
  // Guard against SSR - localStorage is only available in the browser
  if (typeof window === 'undefined') {
    return {
      id: boardId,
      name: boardId === DEFAULT_BOARD_ID ? 'Default Feed' : boardId,
      enabledSources: new Set(),
      blockedEntities: new Map(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  }

  try {
    const saved = localStorage.getItem(`${STORAGE_KEY_PREFIX}${boardId}`);
    if (saved) {
      const parsed = JSON.parse(saved);
      return {
        ...parsed,
        enabledSources: new Set(parsed.enabledSources || []),
        blockedEntities: new Map(
          Object.entries(parsed.blockedEntities || {}).map(([k, v]: [string, any]) => [
            k,
            {
              ...v,
              blockedSources: new Set(v.blockedSources || []),
            },
          ])
        ),
      };
    }
  } catch (e) {
    console.warn('Failed to load board config:', e);
  }

  // Default: all sources enabled, no blocked entities
  return {
    id: boardId,
    name: boardId === DEFAULT_BOARD_ID ? 'Default Feed' : boardId,
    enabledSources: new Set(),
    blockedEntities: new Map(),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

export function saveBoardConfig(config: BoardConfig): void {
  // Guard against SSR - localStorage is only available in the browser
  if (typeof window === 'undefined') {
    return;
  }

  try {
    const serializable = {
      ...config,
      enabledSources: Array.from(config.enabledSources),
      blockedEntities: Object.fromEntries(
        Array.from(config.blockedEntities.entries()).map(([k, v]) => [
          k,
          {
            ...v,
            blockedSources: Array.from(v.blockedSources),
          },
        ])
      ),
    };
    localStorage.setItem(`${STORAGE_KEY_PREFIX}${config.id}`, JSON.stringify(serializable));
  } catch (e) {
    console.warn('Failed to save board config:', e);
  }
}

export function getAllBoards(): string[] {
  // Guard against SSR - localStorage is only available in the browser
  if (typeof window === 'undefined') {
    return [DEFAULT_BOARD_ID];
  }

  const boards: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key?.startsWith(STORAGE_KEY_PREFIX)) {
      const boardId = key.replace(STORAGE_KEY_PREFIX, '');
      boards.push(boardId);
    }
  }
  return boards.length > 0 ? boards : [DEFAULT_BOARD_ID];
}

/**
 * Check if a post should be visible based on board configuration
 */
export function isPostVisible(
  post: {
    subreddit?: { name: string };
    handle?: { creatorName?: string; name: string };
    platform: string;
  },
  config: BoardConfig
): boolean {
  const sourceName = post.subreddit?.name || post.handle?.name || '';
  
  // Debug logging for howdyhowdyyallhot
  if (sourceName === 'howdyhowdyyallhot' || sourceName.includes('howdy')) {
    console.log(`[board-config] Checking howdyhowdyyallhot post visibility:`, {
      sourceName,
      sourceNameType: typeof sourceName,
      sourceNameLength: sourceName.length,
      enabledSources: Array.from(config.enabledSources),
      enabledSourcesTypes: Array.from(config.enabledSources).map(s => ({ s, type: typeof s, length: s.length })),
      hasSource: config.enabledSources.has(sourceName),
      subreddit: post.subreddit,
      handle: post.handle,
    });
  }
  
  // Check if source is enabled (if any sources are configured)
  if (config.enabledSources.size > 0 && !config.enabledSources.has(sourceName)) {
    // Only log if it's not the expected source to reduce noise
    if (sourceName && sourceName !== 'howdyhowdyyallhot') {
      console.debug(`[board-config] Post filtered: source "${sourceName}" not in enabledSources:`, Array.from(config.enabledSources));
    } else if (sourceName === 'howdyhowdyyallhot') {
      console.warn(`[board-config] Post from howdyhowdyyallhot filtered! sourceName="${sourceName}", enabledSources:`, Array.from(config.enabledSources), 'Post:', post);
    }
    return false;
  }
  
  // Log successful matches for howdyhowdyyallhot to verify it's working
  if (sourceName === 'howdyhowdyyallhot') {
    console.log(`[board-config] Post from howdyhowdyyallhot PASSED filter:`, post);
  }

  // Check if entity is blocked from this source
  const creatorName = post.handle?.creatorName;
  if (creatorName) {
    const entityFilter = config.blockedEntities.get(creatorName.toLowerCase());
    if (entityFilter && entityFilter.blockedSources.has(sourceName)) {
      return false; // This entity is blocked from this source
    }
  }

  return true;
}

