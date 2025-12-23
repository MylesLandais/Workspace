import { getFeed } from '../neo4j/queries/feed.js';
import { getCreators, getCreatorBySlug } from '../neo4j/queries/creators.js';
import { getSources, getFeedGroups, searchSubreddits } from '../neo4j/queries/sources.js';
import {
  getClusterById,
  getMediaById,
  getImageLineage,
  getSimilarImages,
} from '../neo4j/queries/images.js';
import { ImageIngestionService } from '../services/imageIngestion.js';

export const queryResolvers = {
  Query: {
    feed: async (_: any, { cursor, limit = 20 }: { cursor?: string | null; limit?: number }) => {
      const { posts, nextCursor } = await getFeed(cursor, limit);
      
      return {
        edges: posts.map((post) => ({
          node: post,
          cursor: post.publishDate,
        })),
        pageInfo: {
          hasNextPage: nextCursor !== null,
          endCursor: nextCursor,
        },
      };
    },

    creators: async (_: any, { query, limit = 20 }: { query?: string; limit?: number }) => {
      return await getCreators(query, limit);
    },

    creator: async (_: any, { slug }: { slug: string }) => {
      return await getCreatorBySlug(slug);
    },

    getFeedGroups: async () => {
      return await getFeedGroups();
    },

    getSources: async (_: any, { groupId }: { groupId?: string }) => {
      return await getSources(groupId);
    },

    searchSubreddits: async (_: any, { query }: { query: string }) => {
      return await searchSubreddits(query);
    },

    checkDuplicate: async (_: any, { image }: { image: Promise<any> }) => {
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

      const result = await ingestionService.ingestImage(imageBuffer);

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

    similarImages: async (_: any, { mediaId, limit = 10 }: { mediaId: string; limit?: number }) => {
      const similar = await getSimilarImages(mediaId, limit);
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
      }));
    },

    imageCluster: async (_: any, { clusterId }: { clusterId: string }) => {
      const cluster = await getClusterById(clusterId);
      if (!cluster) {
        return null;
      }

      const { getSession } = await import('../neo4j/driver.js');
      const session = getSession();
      
      try {
        const query = `
          MATCH (c:ImageCluster {id: $clusterId})
          OPTIONAL MATCH (c)-[:CANONICAL]->(canonical:Media)
          OPTIONAL MATCH (c)<-[:BELONGS_TO]-(m:Media)
          RETURN canonical.id AS canonicalId, collect(DISTINCT m.id) AS memberIds
        `;
        const result = await session.run(query, { clusterId });
        const record = result.records[0];
        const canonicalId = record.get('canonicalId');
        const memberIds = record.get('memberIds') || [];
        
        const canonicalMedia = canonicalId ? await getMediaById(canonicalId) : null;
        const allMemberIds = [...new Set([...memberIds, canonicalId].filter(Boolean))];
        const members = await Promise.all(
          allMemberIds
            .filter((id: string) => id !== canonicalId)
            .map((id: string) => getMediaById(id))
        );

        return {
          id: cluster.id,
          canonicalSha256: cluster.canonicalSha256,
          canonicalMedia: canonicalMedia ? {
            id: canonicalMedia.id,
            sha256: canonicalMedia.sha256,
            url: canonicalMedia.url,
            width: canonicalMedia.width,
            height: canonicalMedia.height,
          } : null,
          repostCount: cluster.repostCount,
          firstSeen: cluster.firstSeen,
          lastSeen: cluster.lastSeen,
          memberImages: members.filter((m) => m !== null).map((m) => ({
            id: m!.id,
            sha256: m!.sha256,
            url: m!.url,
            width: m!.width,
            height: m!.height,
          })),
        };
      } finally {
        await session.close();
      }
    },

    imageLineage: async (_: any, { mediaId }: { mediaId: string }) => {
      const lineage = await getImageLineage(mediaId);
      const media = await getMediaById(mediaId);
      const clusterId = media?.clusterId;

      return {
        mediaId,
        clusterId: clusterId || '',
        original: lineage.original ? {
          id: lineage.original.id,
          sha256: lineage.original.sha256,
          url: lineage.original.url,
          width: lineage.original.width,
          height: lineage.original.height,
        } : null,
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
      };
    },
  },
};


