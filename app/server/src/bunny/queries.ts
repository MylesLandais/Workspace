import { withSession } from '../lib/session.js';
import logger from '../lib/logger.js';

export interface SavedBoardData {
  id: string;
  name: string;
  filters: {
    persons: string[];
    sources: string[];
    searchQuery: string;
  };
  createdAt: string;
  userId: string;
}

export interface IdentityProfileData {
  id: string;
  name: string;
  bio: string;
  avatarUrl: string;
  aliases: string[];
  contextKeywords: string[];
  imagePool: string[];
}

export interface RelationshipData {
  targetId: string;
  type: string;
}

/**
 * Get all saved boards for a user
 */
export async function getSavedBoards(userId: string): Promise<SavedBoardData[]> {
  return withSession(async (session) => {
    const query = `
      MATCH (sb:SavedBoard {userId: $userId})
      RETURN sb
      ORDER BY sb.createdAt DESC
    `;
    
    const result = await session.run(query, { userId });
    
    return result.records.map(record => {
      const board = record.get('sb').properties;
      return {
        id: board.id,
        name: board.name,
        filters: board.filters ? JSON.parse(board.filters) : { persons: [], sources: [], searchQuery: '' },
        createdAt: board.createdAt ? new Date(board.createdAt.toString()).toISOString() : new Date().toISOString(),
        userId: board.userId,
      };
    });
  });
}

/**
 * Create a saved board
 */
export async function createSavedBoard(userId: string, name: string, filters: any): Promise<SavedBoardData> {
  return withSession(async (session) => {
    const id = `board-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const createdAt = new Date().toISOString();
    
    const query = `
      CREATE (sb:SavedBoard {
        id: $id,
        userId: $userId,
        name: $name,
        filters: $filters,
        createdAt: $createdAt
      })
      RETURN sb
    `;
    
    const result = await session.run(query, {
      id,
      userId,
      name,
      filters: JSON.stringify(filters),
      createdAt,
    });
    
    const board = result.records[0].get('sb').properties;
    return {
      id: board.id,
      name: board.name,
      filters: JSON.parse(board.filters),
      createdAt: board.createdAt ? new Date(board.createdAt.toString()).toISOString() : createdAt,
      userId: board.userId,
    };
  });
}

/**
 * Update a saved board
 */
export async function updateSavedBoard(id: string, name: string, filters: any): Promise<SavedBoardData | null> {
  return withSession(async (session) => {
    const query = `
      MATCH (sb:SavedBoard {id: $id})
      SET sb.name = $name, sb.filters = $filters
      RETURN sb
    `;
    
    const result = await session.run(query, {
      id,
      name,
      filters: JSON.stringify(filters),
    });
    
    if (result.records.length === 0) return null;
    
    const board = result.records[0].get('sb').properties;
    return {
      id: board.id,
      name: board.name,
      filters: JSON.parse(board.filters),
      createdAt: board.createdAt ? new Date(board.createdAt.toString()).toISOString() : new Date().toISOString(),
      userId: board.userId,
    };
  });
}

/**
 * Delete a saved board
 */
export async function deleteSavedBoard(id: string): Promise<boolean> {
  return withSession(async (session) => {
    const query = `
      MATCH (sb:SavedBoard {id: $id})
      DELETE sb
      RETURN count(sb) as deleted
    `;
    
    const result = await session.run(query, { id });
    return result.records[0].get('deleted').toNumber() > 0;
  });
}

/**
 * Get identity profiles with optional query filter
 */
export async function getIdentityProfiles(query?: string, limit: number = 20): Promise<IdentityProfileData[]> {
  return withSession(async (session) => {
    let cypherQuery = `
      MATCH (e:Entity)
      WHERE e.type = 'person'
    `;
    
    const params: any = { limit };
    
    if (query) {
      cypherQuery += `
        AND (toLower(e.name) CONTAINS toLower($query)
           OR (e.aliases IS NOT NULL AND any(alias IN e.aliases WHERE toLower(alias) CONTAINS toLower($query))))
      `;
      params.query = query;
    }
    
    cypherQuery += `
      RETURN e
      ORDER BY e.name
      LIMIT $limit
    `;
    
    const result = await session.run(cypherQuery, params);
    
    return result.records.map(record => {
      const entity = record.get('e').properties;
      return {
        id: entity.id,
        name: entity.name || entity.display_name,
        bio: entity.bio || '',
        avatarUrl: entity.avatar_url || '',
        aliases: typeof entity.aliases === 'string' ? JSON.parse(entity.aliases) : (entity.aliases || []),
        contextKeywords: typeof entity.context_keywords === 'string' ? JSON.parse(entity.context_keywords) : (entity.context_keywords || []),
        imagePool: typeof entity.image_pool === 'string' ? JSON.parse(entity.image_pool) : (entity.image_pool || []),
      };
    });
  });
}

/**
 * Get a single identity profile by ID
 */
export async function getIdentityProfileById(id: string): Promise<IdentityProfileData | null> {
  return withSession(async (session) => {
    const query = `
      MATCH (e:Entity {id: $id})
      WHERE e.type = 'person'
      RETURN e
    `;
    
    const result = await session.run(query, { id });
    
    if (result.records.length === 0) return null;
    
    const entity = result.records[0].get('e').properties;
    return {
      id: entity.id,
      name: entity.name || entity.display_name,
      bio: entity.bio || '',
      avatarUrl: entity.avatar_url || '',
      aliases: typeof entity.aliases === 'string' ? JSON.parse(entity.aliases) : (entity.aliases || []),
      contextKeywords: typeof entity.context_keywords === 'string' ? JSON.parse(entity.context_keywords) : (entity.context_keywords || []),
      imagePool: typeof entity.image_pool === 'string' ? JSON.parse(entity.image_pool) : (entity.image_pool || []),
    };
  });
}

/**
 * Get relationships for a creator
 */
export async function getRelationships(creatorId: string): Promise<RelationshipData[]> {
  return withSession(async (session) => {
    const query = `
      MATCH (e:Entity {id: $creatorId})-[r:RELATED_TO]->(target:Entity)
      WHERE e.type = 'person' AND target.type = 'person'
      RETURN target.id as targetId, r.type as type
    `;
    
    const result = await session.run(query, { creatorId });
    
    return result.records.map(record => ({
      targetId: record.get('targetId'),
      type: record.get('type'),
    }));
  });
}

