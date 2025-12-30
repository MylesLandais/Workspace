import { getSession } from '../neo4j/driver.js';
import { getCreatorBySlug } from '../neo4j/queries/creators.js';
import { getSources } from '../neo4j/queries/sources.js';
import { ImageIngestionService } from '../services/imageIngestion.js';
import { Readable } from 'stream';

export const mutationResolvers = {
  Mutation: {
    createCreator: async (_: any, { name, displayName }: { name: string; displayName: string }) => {
      const session = getSession();
      try {
        const slug = name.toLowerCase().replace(/\s+/g, '-');
        const id = slug;

        const query = `
          MERGE (e:Entity {id: $id})
          ON CREATE SET
            e.name = $name,
            e.display_name = $displayName,
            e.type = 'person',
            e.verified = false
          RETURN e
        `;

        const result = await session.run(query, { id, name, displayName });

        if (result.records.length === 0) {
          throw new Error('Failed to create creator');
        }

        return await getCreatorBySlug(id);
      } finally {
        await session.close();
      }
    },

    addHandle: async (
      _: any,
      { creatorId, platform, username, url }: { creatorId: string; platform: string; username: string; url: string }
    ) => {
      const session = getSession();
      try {
        const id = crypto.randomUUID();
        const sourceType = platform.toLowerCase();
        let handleStr = '';
        
        if (platform === 'REDDIT') {
          handleStr = `r/${username}`;
        } else if (platform === 'YOUTUBE') {
          handleStr = username.startsWith('@') ? username : `@${username}`;
        } else {
          handleStr = username;
        }

        const query = `
          MATCH (e:Entity {id: $creatorId})
          CREATE (s:Source {
            id: $id,
            name: $username,
            source_type: $sourceType,
            subreddit_name: ${platform === 'REDDIT' ? '$username' : 'null'},
            youtube_channel_handle: ${platform === 'YOUTUBE' ? '$username' : 'null'},
            url: $url,
            is_paused: false,
            media_count: 0,
            verified: false,
            status: 'active'
          })
          CREATE (e)-[:HAS_SOURCE]->(s)
          RETURN s
        `;

        await session.run(query, { creatorId, id, username, sourceType, url });

        const sources = await getSources();
        const handle = sources.find((s) => s.id === id);
        
        if (!handle) {
          throw new Error('Failed to create handle');
        }

        return {
          id: handle.id,
          platform: platform as any,
          username: handle.subredditName || handle.youtubeHandle || handle.name,
          handle: handleStr,
          url: handle.name,
          verified: false,
          status: 'ACTIVE' as any,
          mediaCount: 0,
          lastSynced: null,
          health: 'red',
        };
      } finally {
        await session.close();
      }
    },

    verifyHandle: async (_: any, { handleId }: { handleId: string }) => {
      const session = getSession();
      try {
        const query = `
          MATCH (s:Source {id: $handleId})
          SET s.verified = true
          RETURN s
        `;

        await session.run(query, { handleId });

        const sources = await getSources();
        const handle = sources.find((s) => s.id === handleId);
        
        if (!handle) {
          throw new Error('Handle not found');
        }

        return {
          id: handle.id,
          platform: handle.sourceType.toUpperCase() as any,
          username: handle.subredditName || handle.youtubeHandle || handle.name,
          handle: handle.subredditName ? `r/${handle.subredditName}` : handle.name,
          url: handle.name,
          verified: true,
          status: 'ACTIVE' as any,
          mediaCount: handle.mediaCount,
          lastSynced: handle.lastSynced,
          health: handle.health,
        };
      } finally {
        await session.close();
      }
    },

    updateHandleStatus: async (
      _: any,
      { handleId, status }: { handleId: string; status: string }
    ) => {
      const session = getSession();
      try {
        const query = `
          MATCH (s:Source {id: $handleId})
          SET s.status = $status
          RETURN s
        `;

        await session.run(query, { handleId, status: status.toLowerCase() });

        const sources = await getSources();
        const handle = sources.find((s) => s.id === handleId);
        
        if (!handle) {
          throw new Error('Handle not found');
        }

        return {
          id: handle.id,
          platform: handle.sourceType.toUpperCase() as any,
          username: handle.subredditName || handle.youtubeHandle || handle.name,
          handle: handle.subredditName ? `r/${handle.subredditName}` : handle.name,
          url: handle.name,
          verified: false,
          status: status as any,
          mediaCount: handle.mediaCount,
          lastSynced: handle.lastSynced,
          health: handle.health,
        };
      } finally {
        await session.close();
      }
    },

    toggleHandlePause: async (_: any, { handleId }: { handleId: string }) => {
      const session = getSession();
      try {
        const query = `
          MATCH (s:Source {id: $handleId})
          SET s.is_paused = NOT s.is_paused
          RETURN s
        `;

        await session.run(query, { handleId });

        const sources = await getSources();
        const handle = sources.find((s) => s.id === handleId);
        
        if (!handle) {
          throw new Error('Handle not found');
        }

        return {
          id: handle.id,
          platform: handle.sourceType.toUpperCase() as any,
          username: handle.subredditName || handle.youtubeHandle || handle.name,
          handle: handle.subredditName ? `r/${handle.subredditName}` : handle.name,
          url: handle.name,
          verified: false,
          status: 'ACTIVE' as any,
          mediaCount: handle.mediaCount,
          lastSynced: handle.lastSynced,
          health: handle.health,
        };
      } finally {
        await session.close();
      }
    },

    removeHandle: async (_: any, { handleId }: { handleId: string }) => {
      const session = getSession();
      try {
        const query = `
          MATCH (s:Source {id: $handleId})
          DETACH DELETE s
          RETURN count(s) as deleted
        `;

        const result = await session.run(query, { handleId });
        return result.records[0].get('deleted').toNumber() > 0;
      } finally {
        await session.close();
      }
    },

    subscribeToSource: async (
      _: any,
      { subredditName, groupId }: { subredditName: string; groupId?: string }
    ) => {
      const session = getSession();
      try {
        const id = crypto.randomUUID();

        let groupIdToUse = groupId;
        if (!groupIdToUse) {
          const groups = await getFeedGroups();
          groupIdToUse = groups[0]?.id;
          if (!groupIdToUse) {
            throw new Error('No feed group available');
          }
        }

        const query = `
          MERGE (s:Subreddit {name: $subredditName})
          ON CREATE SET
            s.display_name = $subredditName,
            s.subscribers = 0,
            s.created_at = datetime()
          
          MERGE (fg:FeedGroup {id: $groupId})
          
          CREATE (source:Source {
            id: $id,
            name: $subredditName,
            source_type: 'reddit',
            subreddit_name: $subredditName,
            is_paused: false,
            media_count: 0,
            verified: false,
            status: 'active'
          })
          
          CREATE (fg)-[:CONTAINS]->(source)
          CREATE (source)-[:POSTED_IN]->(s)
          
          RETURN source, fg.name AS groupName
        `;

        await session.run(query, { subredditName, groupId: groupIdToUse, id });

        const sources = await getSources(groupIdToUse);
        const source = sources.find((s) => s.id === id);
        
        if (!source) {
          throw new Error('Failed to create source');
        }

        return source;
      } finally {
        await session.close();
      }
    },

    createFeedGroup: async (_: any, { name }: { name: string }) => {
      const session = getSession();
      try {
        const id = crypto.randomUUID();
        const query = `
          CREATE (fg:FeedGroup {
            id: $id,
            name: $name,
            created_at: datetime()
          })
          RETURN fg.id AS id, fg.name AS name, fg.created_at AS createdAt
        `;

        const result = await session.run(query, { id, name });
        const record = result.records[0];

        return {
          id: record.get('id'),
          name: record.get('name'),
          createdAt: new Date(record.get('createdAt').toString()).toISOString(),
        };
      } finally {
        await session.close();
      }
    },

    ingestImage: async (
      _: any,
      {
        image,
        postId,
        subreddit,
        author,
        title,
        createdAt,
      }: {
        image: Promise<any>;
        postId?: string;
        subreddit?: string;
        author?: string;
        title?: string;
        createdAt?: string;
      }
    ) => {
      const ingestionService = new ImageIngestionService();
      
      const file = await image;
      const { createReadStream, mimetype } = await file;
      const stream = createReadStream();
      const chunks: Buffer[] = [];

      for await (const chunk of stream) {
        chunks.push(chunk);
      }

      const imageBuffer = Buffer.concat(chunks);

      if (imageBuffer.length > 10 * 1024 * 1024) {
        throw new Error('Image size exceeds 10MB limit');
      }

      if (!mimetype || !mimetype.startsWith('image/')) {
        throw new Error('File must be an image');
      }

      const result = await ingestionService.ingestImage(imageBuffer, {
        postId,
        subreddit,
        author,
        title,
        createdAt: createdAt ? new Date(createdAt) : undefined,
      });

      return {
        mediaId: result.mediaId,
        clusterId: result.clusterId,
        isDuplicate: result.isDuplicate,
        isRepost: result.isRepost,
        confidence: result.confidence,
        matchedMethod: result.matchedMethod,
        original: result.original ? {
          mediaId: result.original.mediaId,
          firstSeen: result.original.firstSeen.toISOString(),
          postId: result.original.postId,
        } : null,
      };
    },
  },
};


