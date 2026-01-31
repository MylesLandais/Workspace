import { getFeed } from "../neo4j/queries/feed.js";
import { getFeedHybrid } from "../neo4j/queries/feed-compat.js";
import { getCreators, getCreatorBySlug } from "../neo4j/queries/creators.js";
import {
  getSources,
  getFeedGroups,
  searchSubreddits,
  getUserSources,
  getSourceById,
} from "../neo4j/queries/sources.js";
import { parseOPMLContent, discoverFeeds } from "../services/opmlParser.js";
import {
  getClusterById,
  getMediaById,
  getImageLineage,
  getSimilarImages,
} from "../neo4j/queries/images.js";
import logger from "../lib/logger.js";
import { withSession } from "../lib/session.js";
import { getPresignedUrlService } from "../lib/serviceRegistry.js";
import { Resolvers } from "../schema/generated/resolvers.js";

export const queryResolvers: Resolvers = {
  Query: {
    feed: async (_, { cursor, limit = 20, filters }) => {
      try {
        // Use hybrid feed that auto-detects Media vs Post nodes
        const feedResult = await getFeedHybrid(
          cursor || null,
          limit || 20,
          filters || undefined,
        );

        if (!feedResult || !feedResult.posts) {
          return {
            edges: [],
            pageInfo: {
              hasNextPage: false,
              endCursor: null,
            },
          };
        }

        const urlService = getPresignedUrlService();

        const items = feedResult.posts
          .filter((post) => post.sha256 && post.mimeType)
          .map((post) => ({
            sha256: post.sha256!,
            mimeType: post.mimeType!,
          }));

        let presignedUrls: Map<string, { url: string; expiresAt: Date }> =
          new Map();

        if (items.length > 0) {
          try {
            const urlResults = await urlService.batchGetPresignedUrls(items);
            presignedUrls = new Map(
              urlResults.map((result) => [
                result.sha256,
                { url: result.url, expiresAt: result.expiresAt },
              ]),
            );
          } catch (error: any) {
            logger.error("Error generating presigned URLs", error);
          }
        }

        const postsWithUrls = feedResult.posts.map((post) => {
          const urlData = post.sha256 ? presignedUrls.get(post.sha256) : null;
          return {
            ...post,
            id: post.id || "",
            title: post.title || "",
            sourceUrl: post.sourceUrl || "",
            imageUrl: post.imageUrl || "",
            publishDate: post.publishDate,
            mediaType: (post.mediaType as any) || "IMAGE",
            platform: (post.platform as any) || "REDDIT",
            handle: {
              ...post.handle,
              name: post.handle.name || "",
              handle: post.handle.handle || "",
            },
            presignedUrl: urlData?.url || null,
            urlExpiresAt: urlData?.expiresAt?.toISOString() || null,
          };
        });

        return {
          edges: postsWithUrls.map((post) => ({
            node: post as any,
            cursor: post.publishDate,
          })),
          pageInfo: {
            hasNextPage: feedResult.nextCursor !== null,
            endCursor: feedResult.nextCursor,
          },
        };
      } catch (error: any) {
        logger.error("Feed resolver error", error);
        return {
          edges: [],
          pageInfo: {
            hasNextPage: false,
            endCursor: null,
          },
        };
      }
    },

    creators: async (_, { query, limit = 20 }) => {
      return (await getCreators(query || undefined, limit || 20)) as any;
    },

    creator: async (_, { slug }) => {
      return (await getCreatorBySlug(slug)) as any;
    },

    getFeedGroups: async (_, { userId }) => {
      return (await getFeedGroups(userId || undefined)) as any;
    },

    getSources: async (_, { groupId }) => {
      return (await getSources(groupId || undefined)) as any;
    },

    searchSubreddits: async (_, { query }) => {
      return (await searchSubreddits(query)) as any;
    },

    getUserSources: async (_, { filters }) => {
      return (await getUserSources(filters || undefined)) as any;
    },

    getSourceById: async (_, { id }) => {
      return (await getSourceById(id)) as any;
    },

    parseOPML: async (_, { content }) => {
      return parseOPMLContent(content) as any;
    },

    discoverFeeds: async (_, { url }) => {
      return (await discoverFeeds(url)) as any;
    },

    checkDuplicate: async (_, { image }) => {
      const { ImageIngestionService } = await import(
        "../services/imageIngestion.js"
      );
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

      const result = await ingestionService.ingestImage(imageBuffer);

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

    similarImages: async (_, { mediaId, limit = 10 }) => {
      const similar = await getSimilarImages(mediaId, limit || 10);
      return similar.map((s) => ({
        media: {
          id: s.media.id,
          sha256: s.media.sha256,
          phash: s.media.phash,
          dhash: s.media.dhash,
          width: s.media.width,
          height: s.media.height,
          url: s.media.url,
          storagePath: s.media.storagePath,
        },
        similarityScore: s.similarity,
        method: s.method,
        hammingDistance: null,
      })) as any;
    },

    imageCluster: async (_, { clusterId }) => {
      const cluster = await getClusterById(clusterId);
      if (!cluster) {
        return null;
      }

      return withSession(async (session) => {
        const query = `
          MATCH (c:ImageCluster {id: $clusterId})
          OPTIONAL MATCH (c)-[:CANONICAL]->(canonical:Media)
          OPTIONAL MATCH (c)<-[:BELONGS_TO]-(m:Media)
          RETURN canonical.id AS canonicalId, collect(DISTINCT m.id) AS memberIds
        `;
        const result = await session.run(query, { clusterId });
        const record = result.records[0];
        const canonicalId = record.get("canonicalId");
        const memberIds = record.get("memberIds") || [];

        const canonicalMedia = canonicalId
          ? await getMediaById(canonicalId)
          : null;
        const allMemberIds = [
          ...new Set([...memberIds, canonicalId].filter(Boolean)),
        ];
        const members = await Promise.all(
          allMemberIds
            .filter((id: string) => id !== canonicalId)
            .map((id: string) => getMediaById(id)),
        );

        return {
          id: cluster.id,
          canonicalSha256: cluster.canonicalSha256,
          canonicalMedia: canonicalMedia
            ? {
                id: canonicalMedia.id,
                sha256: canonicalMedia.sha256,
                url: canonicalMedia.url,
                width: canonicalMedia.width,
                height: canonicalMedia.height,
              }
            : null,
          repostCount: cluster.repostCount,
          firstSeen: cluster.firstSeen,
          lastSeen: cluster.lastSeen,
          memberImages: members
            .filter((m) => m !== null)
            .map((m) => ({
              id: m!.id,
              sha256: m!.sha256,
              url: m!.url,
              width: m!.width,
              height: m!.height,
            })),
        } as any;
      });
    },

    imageLineage: async (_, { mediaId }) => {
      const lineage = await getImageLineage(mediaId);
      const media = await getMediaById(mediaId);
      const clusterId = media?.clusterId;

      return {
        mediaId,
        clusterId: clusterId || "",
        original: lineage.original
          ? {
              id: lineage.original.id,
              sha256: lineage.original.sha256,
              url: lineage.original.url,
              width: lineage.original.width,
              height: lineage.original.height,
            }
          : null,
        reposts: lineage.reposts.map((r) => ({
          media: {
            id: r.media.id,
            sha256: r.media.sha256,
            url: r.media.url,
            width: r.media.width,
            height: r.media.height,
          },
          postId: r.postId,
          createdAt: r.createdAt,
          confidence: r.confidence,
        })),
      } as any;
    },
  },
};
