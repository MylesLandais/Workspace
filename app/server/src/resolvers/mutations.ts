import { getCreatorBySlug } from "../neo4j/queries/creators.js";
import {
  getSources,
  getFeedGroups,
  createSourceNode,
  updateSourceNode,
  deleteSourceNode,
  bulkDeleteSources,
  toggleSourcePause,
  bulkCreateSources,
  createUserFeedGroup,
} from "../neo4j/queries/sources.js";
import { ImageIngestionService } from "../services/imageIngestion.js";
import { withSession } from "../lib/session.js";
import { Resolvers } from "../schema/generated/resolvers.js";

export const mutationResolvers: Resolvers = {
  Mutation: {
    createCreator: async (_, { name, displayName }) => {
      return withSession(async (session) => {
        const slug = name.toLowerCase().replace(/\s+/g, "-");
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
          throw new Error("Failed to create creator");
        }

        return (await getCreatorBySlug(id)) as any;
      });
    },

    addHandle: async (_, { creatorId, platform, username, url }) => {
      return withSession(async (session) => {
        const id = crypto.randomUUID();
        const sourceType = platform.toLowerCase();
        let handleStr = "";

        if (platform === "REDDIT") {
          handleStr = `r/${username}`;
        } else if (platform === "YOUTUBE") {
          handleStr = username.startsWith("@") ? username : `@${username}`;
        } else {
          handleStr = username;
        }

        const query = `
          MATCH (e:Entity {id: $creatorId})
          CREATE (s:Source {
            id: $id,
            name: $username,
            source_type: $sourceType,
            subreddit_name: ${platform === "REDDIT" ? "$username" : "null"},
            youtube_channel_handle: ${platform === "YOUTUBE" ? "$username" : "null"},
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
          throw new Error("Failed to create handle");
        }

        return {
          id: handle.id,
          platform: platform as any,
          username: handle.subredditName || handle.youtubeHandle || handle.name,
          handle: handleStr,
          url: handle.name,
          verified: false,
          status: "ACTIVE" as any,
          mediaCount: 0,
          lastSynced: null,
          health: "red",
        } as any;
      });
    },

    verifyHandle: async (_, { handleId }) => {
      return withSession(async (session) => {
        const query = `
          MATCH (s:Source {id: $handleId})
          SET s.verified = true
          RETURN s
        `;

        await session.run(query, { handleId });

        const sources = await getSources();
        const handle = sources.find((s) => s.id === handleId);

        if (!handle) {
          throw new Error("Handle not found");
        }

        return {
          id: handle.id,
          platform: handle.sourceType.toUpperCase() as any,
          username: handle.subredditName || handle.youtubeHandle || handle.name,
          handle: handle.subredditName
            ? `r/${handle.subredditName}`
            : handle.name,
          url: handle.name,
          verified: true,
          status: "ACTIVE" as any,
          mediaCount: handle.mediaCount,
          lastSynced: handle.lastSynced,
          health: handle.health,
        } as any;
      });
    },

    updateHandleStatus: async (_, { handleId, status }) => {
      return withSession(async (session) => {
        const query = `
          MATCH (s:Source {id: $handleId})
          SET s.status = $status
          RETURN s
        `;

        await session.run(query, { handleId, status: status.toLowerCase() });

        const sources = await getSources();
        const handle = sources.find((s) => s.id === handleId);

        if (!handle) {
          throw new Error("Handle not found");
        }

        return {
          id: handle.id,
          platform: handle.sourceType.toUpperCase() as any,
          username: handle.subredditName || handle.youtubeHandle || handle.name,
          handle: handle.subredditName
            ? `r/${handle.subredditName}`
            : handle.name,
          url: handle.name,
          verified: false,
          status: status as any,
          mediaCount: handle.mediaCount,
          lastSynced: handle.lastSynced,
          health: handle.health,
        } as any;
      });
    },

    toggleHandlePause: async (_, { handleId }) => {
      return withSession(async (session) => {
        const query = `
          MATCH (s:Source {id: $handleId})
          SET s.is_paused = NOT s.is_paused
          RETURN s
        `;

        await session.run(query, { handleId });

        const sources = await getSources();
        const handle = sources.find((s) => s.id === handleId);

        if (!handle) {
          throw new Error("Handle not found");
        }

        return {
          id: handle.id,
          platform: handle.sourceType.toUpperCase() as any,
          username: handle.subredditName || handle.youtubeHandle || handle.name,
          handle: handle.subredditName
            ? `r/${handle.subredditName}`
            : handle.name,
          url: handle.name,
          verified: false,
          status: "ACTIVE" as any,
          mediaCount: handle.mediaCount,
          lastSynced: handle.lastSynced,
          health: handle.health,
        } as any;
      });
    },

    removeHandle: async (_, { handleId }) => {
      return withSession(async (session) => {
        const query = `
          MATCH (s:Source {id: $handleId})
          DETACH DELETE s
          RETURN count(s) as deleted
        `;

        const result = await session.run(query, { handleId });
        return result.records[0].get("deleted").toNumber() > 0;
      });
    },

    subscribeToSource: async (_, { subredditName, groupId }) => {
      return withSession(async (session) => {
        const id = crypto.randomUUID();

        let groupIdToUse = groupId;
        if (!groupIdToUse) {
          const groups = await getFeedGroups();
          groupIdToUse = groups[0]?.id;
          if (!groupIdToUse) {
            throw new Error("No feed group available");
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
          throw new Error("Failed to create source");
        }

        return source as any;
      });
    },

    createFeedGroup: async (_, { name }) => {
      return withSession(async (session) => {
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
          id: record.get("id"),
          name: record.get("name"),
          createdAt: new Date(record.get("createdAt").toString()).toISOString(),
        } as any;
      });
    },

    createUserFeedGroup: async (_, { userId, name }) => {
      const group = await createUserFeedGroup(userId, name);
      return {
        ...group,
        createdAt: new Date().toISOString(), // The query returns it but let's be safe
      } as any;
    },

    // Source Management mutations
    createSource: async (_, { input }) => {
      const source = await createSourceNode({
        name: input.name,
        sourceType: input.sourceType,
        url: input.url || undefined,
        subredditName: input.subredditName || undefined,
        youtubeHandle: input.youtubeHandle || undefined,
        twitterHandle: input.twitterHandle || undefined,
        instagramHandle: input.instagramHandle || undefined,
        tiktokHandle: input.tiktokHandle || undefined,
        groupId: input.groupId || undefined,
        description: input.description || undefined,
      });
      return source as any;
    },

    updateSource: async (_, { id, input }) => {
      const source = await updateSourceNode(id, {
        name: input.name || undefined,
        description: input.description || undefined,
        groupId: input.groupId || undefined,
        isPaused: input.isPaused ?? undefined,
        isEnabled: input.isEnabled ?? undefined,
      });
      if (!source) {
        throw new Error("Source not found");
      }
      return source as any;
    },

    deleteSource: async (_, { id }) => {
      return deleteSourceNode(id);
    },

    importOPML: async (_, { feedUrls, groupId }) => {
      const sources = feedUrls.map((url) => ({
        name: url, // Will be replaced with actual title later
        sourceType: "RSS",
        url,
      }));

      const result = await bulkCreateSources(sources, groupId || undefined);

      return {
        imported: result.imported,
        skipped: result.skipped,
        failed: result.failed,
        sources: result.sources,
        errors: [],
      } as any;
    },

    bulkDeleteSources: async (_, { ids }) => {
      return bulkDeleteSources(ids);
    },

    toggleSourcePause: async (_, { id }) => {
      const source = await toggleSourcePause(id);
      if (!source) {
        throw new Error("Source not found");
      }
      return source as any;
    },

    ingestImage: async (
      _,
      { image, postId, subreddit, author, title, createdAt },
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
        throw new Error("Image size exceeds 10MB limit");
      }

      if (!mimetype || !mimetype.startsWith("image/")) {
        throw new Error("File must be an image");
      }

      const result = await ingestionService.ingestImage(imageBuffer, {
        postId: postId || undefined,
        subreddit: subreddit || undefined,
        author: author || undefined,
        title: title || undefined,
        createdAt: createdAt ? new Date(createdAt) : undefined,
      });

      return {
        mediaId: result.mediaId,
        clusterId: result.clusterId,
        isDuplicate: result.isDuplicate,
        isRepost: result.isRepost,
        confidence: result.confidence,
        matchedMethod: result.matchedMethod,
        original: result.original
          ? {
              mediaId: result.original.mediaId,
              firstSeen: result.original.firstSeen.toISOString(),
              postId: result.original.postId,
            }
          : null,
      } as any;
    },
  },
};
