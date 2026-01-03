import {
  getSavedBoards,
  createSavedBoard,
  updateSavedBoard,
  deleteSavedBoard,
  getIdentityProfiles,
  getIdentityProfileById,
  getRelationships,
} from './queries.js';
import { creatorToIdentityProfile } from './adapters.js';
import { getCreators, getCreatorBySlug, getHandlesForCreator } from '../neo4j/queries/creators.js';
import { withSession } from '../lib/session.js';
import { Resolvers } from '../schema/generated/resolvers.js';

export const bunnyResolvers: Resolvers = {
  Query: {
    getSavedBoards: async (_, { userId }) => {
      return (await getSavedBoards(userId)) as any;
    },

    getIdentityProfiles: async (_, { query, limit }) => {
      const profiles = await getIdentityProfiles(query || undefined, limit || 20);
      // For now, return basic data. Full IdentityProfile requires handles which we'll add later
      return profiles.map(profile => ({
        ...profile,
        sources: [],
        relationships: [],
      })) as any;
    },

    getIdentityProfile: async (_, { id }) => {
      const profile = await getIdentityProfileById(id);
      if (!profile) return null;
      
      return withSession(async (session) => {
        // Get sources (handles) for this entity
        const sourcesQuery = `
          MATCH (e:Entity {id: $id})-[:HAS_SOURCE]->(s:Source)
          RETURN s
        `;
        const sourcesResult = await session.run(sourcesQuery, { id });
        const sources = sourcesResult.records.map(record => {
          const source = record.get('s').properties;
          return {
            platform: (source.source_type || 'REDDIT').toUpperCase() as any,
            id: source.subreddit_name || source.youtube_channel_handle || source.name,
            databaseId: source.id, // Include database ID for mutations
            label: source.label || undefined,
            hidden: source.hidden || false,
          };
        });
        
        const relationships = await getRelationships(id);
        
        return {
          ...profile,
          sources,
          relationships: relationships.map(r => ({
            targetId: r.targetId,
            type: r.type,
          })),
        } as any;
      });
    },
  },

  Mutation: {
    createSavedBoard: async (_, { userId, input }) => {
      return (await createSavedBoard(userId, input.name, input.filters)) as any;
    },

    updateSavedBoard: async (_, { id, input }) => {
      return (await updateSavedBoard(id, input.name, input.filters)) as any;
    },

    deleteSavedBoard: async (_, { id }) => {
      return await deleteSavedBoard(id);
    },

    createIdentityProfile: async (_, { userId, input }) => {
      return withSession(async (session) => {
        const id = input.id || input.name.toLowerCase().replace(/\s+/g, '-');
        
        // Create Entity (Creator) node
        const createQuery = `
          MERGE (e:Entity {id: $id})
          ON CREATE SET
            e.name = $name,
            e.display_name = $name,
            e.type = 'person',
            e.verified = false,
            e.bio = $bio,
            e.avatar_url = $avatarUrl,
            e.aliases = $aliases,
            e.context_keywords = $contextKeywords,
            e.image_pool = $imagePool
          RETURN e
        `;
        
        await session.run(createQuery, {
          id,
          name: input.name,
          bio: input.bio || '',
          avatarUrl: input.avatarUrl || '',
          aliases: JSON.stringify(input.aliases || []),
          contextKeywords: JSON.stringify(input.contextKeywords || []),
          imagePool: JSON.stringify(input.imagePool || []),
        });
        
        // Create Source (Handle) nodes
        if (input.sources && input.sources.length > 0) {
          for (const source of input.sources) {
            const sourceId = `source-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            const platform = source.platform.toUpperCase();
            const username = source.id;
            
            const sourceQuery = `
              MATCH (e:Entity {id: $entityId})
              CREATE (s:Source {
                id: $sourceId,
                name: $username,
                source_type: $platform,
                subreddit_name: ${platform === 'REDDIT' ? '$username' : 'null'},
                youtube_channel_handle: ${platform === 'YOUTUBE' ? '$username' : 'null'},
                url: $url,
                label: $label,
                hidden: $hidden,
                is_paused: false,
                media_count: 0,
                verified: false,
                status: 'active'
              })
              CREATE (e)-[:HAS_SOURCE]->(s)
              RETURN s
            `;
            
            await session.run(sourceQuery, {
              entityId: id,
              sourceId,
              platform: platform.toLowerCase(),
              username,
              url: `https://${source.platform.toLowerCase()}.com/${username}`,
              label: source.label || null,
              hidden: source.hidden || false,
            });
          }
        }
        
        // Create relationships
        if (input.relationships && input.relationships.length > 0) {
          for (const rel of input.relationships) {
            const relQuery = `
              MATCH (c1:Entity {id: $profileId})
              MATCH (c2:Entity {id: $targetId})
              MERGE (c1)-[r:RELATED_TO]->(c2)
              SET r.type = $type,
                  r.created_at = datetime(),
                  r.updated_at = datetime()
              RETURN r
            `;
            
            await session.run(relQuery, {
              profileId: id,
              targetId: rel.targetId,
              type: rel.type,
            });
          }
        }
        
        return (await getIdentityProfileById(id)) as any;
      });
    },

    updateIdentityProfile: async (_, { id, input }) => {
      return withSession(async (session) => {
        const updateQuery = `
          MATCH (e:Entity {id: $id})
          SET e.name = COALESCE($name, e.name),
              e.display_name = COALESCE($name, e.display_name),
              e.bio = COALESCE($bio, e.bio),
              e.avatar_url = COALESCE($avatarUrl, e.avatar_url),
              e.aliases = COALESCE($aliases, e.aliases),
              e.context_keywords = COALESCE($contextKeywords, e.context_keywords),
              e.image_pool = COALESCE($imagePool, e.image_pool)
          RETURN e
        `;
        
        await session.run(updateQuery, {
          id,
          name: input.name || null,
          bio: input.bio || null,
          avatarUrl: input.avatarUrl || null,
          aliases: input.aliases ? JSON.stringify(input.aliases) : null,
          contextKeywords: input.contextKeywords ? JSON.stringify(input.contextKeywords) : null,
          imagePool: input.imagePool ? JSON.stringify(input.imagePool) : null,
        });
        
        return (await getIdentityProfileById(id)) as any;
      });
    },

    deleteIdentityProfile: async (_, { id }) => {
      return withSession(async (session) => {
        const query = `
          MATCH (e:Entity {id: $id})
          DETACH DELETE e
          RETURN count(e) as deleted
        `;
        
        const result = await session.run(query, { id });
        return result.records[0].get('deleted').toNumber() > 0;
      });
    },

    createRelationship: async (_, { profileId, input }) => {
      return withSession(async (session) => {
        const query = `
          MATCH (c1:Entity {id: $profileId})
          MATCH (c2:Entity {id: $targetId})
          MERGE (c1)-[r:RELATED_TO]->(c2)
          SET r.type = $type,
              r.created_at = datetime(),
              r.updated_at = datetime()
          RETURN r
        `;
        
        await session.run(query, {
          profileId,
          targetId: input.targetId,
          type: input.type,
        });
        
        const relationships = await getRelationships(profileId);
        return (relationships.find(r => r.targetId === input.targetId) || { targetId: input.targetId, type: input.type }) as any;
      });
    },

    deleteRelationship: async (_, { profileId, targetId }) => {
      return withSession(async (session) => {
        const query = `
          MATCH (c1:Entity {id: $profileId})-[r:RELATED_TO]->(c2:Entity {id: $targetId})
          DELETE r
          RETURN count(r) as deleted
        `;
        
        const result = await session.run(query, { profileId, targetId });
        return result.records[0].get('deleted').toNumber() > 0;
      });
    },
  },
};

