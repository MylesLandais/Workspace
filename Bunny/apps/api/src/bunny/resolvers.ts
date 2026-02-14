import { PresignedUrlService } from "../services/presignedUrl.js";
import { getFeed } from "../neo4j/queries/feed.js";
import {
  getSavedBoards,
  createSavedBoard,
  updateSavedBoard,
  deleteSavedBoard,
  getIdentityProfiles,
  getIdentityProfileById,
  getRelationships,
} from "./queries.js";
import {
  getCreators,
  getCreatorBySlug,
  getHandlesForCreator,
} from "../neo4j/queries/creators.js";
import { withSession } from "../lib/session.js";
import { Resolvers } from "../schema/generated/resolvers.js";

const presignedUrlService = new PresignedUrlService();

// Temporary resolver for the feed until we integrate GraphQL better
export const tempFeedResolver: Resolvers["Query"] = {
  feed: async (_, { cursor, limit, filters }, context) => {
    // 1. Fetch posts from Neo4j (now including sha256, mimeType, isRead)
    const { posts, nextCursor } = await getFeed(
      context.userId || null,
      cursor || null,
      limit || 20,
      filters,
    );

    // 2. Map posts to get presigned URLs for S3-archived media
    const mediaItems = posts
      .filter((p) => p.sha256 && p.mimeType)
      .map((p) => ({ sha256: p.sha256!, mimeType: p.mimeType! }));

    if (mediaItems.length > 0) {
      const urls = await presignedUrlService.batchGetPresignedUrls(mediaItems);
      const urlMap = new Map(urls.map((u) => [u.sha256, u.url]));

      // 3. Inject the presigned URL into the final object
      const mappedPosts = posts.map((post) => {
        if (post.sha256 && urlMap.has(post.sha256)) {
          post.imageUrl = urlMap.get(post.sha256)!;
        }
        return post;
      });

      return { posts: mappedPosts, nextCursor };
    }

    // No S3 media found, return posts as is (relying on old imageUrl/Media.url)
    return { posts, nextCursor };
  },
};

export const bunnyResolvers: Resolvers = {
  Query: {
    ...tempFeedResolver, // Merge in the feed resolver
    getSavedBoards: async (_, { userId }) => {
      return (await getSavedBoards(userId)) as any;
    },

    getIdentityProfiles: async (_, { query, limit }) => {
      const profiles = await getIdentityProfiles(
        query || undefined,
        limit || 20,
      );
      // For now, return basic data. Full IdentityProfile requires handles which we'll add later
      return profiles.map((profile) => ({
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
        const sources = sourcesResult.records.map((record) => {
          const source = record.get("s").properties;
          return {
            platform: (source.source_type || "REDDIT").toUpperCase() as any,
            id:
              source.subreddit_name ||
              source.youtube_channel_handle ||
              source.name,
            databaseId: source.id, // Include database ID for mutations
            label: source.label || undefined,
            hidden: source.hidden || false,
          };
        });

        const relationships = await getRelationships(id);

        return {
          ...profile,
          sources,
          relationships: relationships.map((r) => ({
            targetId: r.targetId,
            type: r.type,
          })),
        } as any;
      });
    },

    redditPosts: async (_, { subreddit, limit = 50, offset = 0 }) => {
      return withSession(async (session) => {
        // Handle both naming conventions: "unixporn" and "r/unixporn"
        const query = `
          MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
          WHERE s.name = $subreddit OR s.name = 'r/' + $subreddit
          OPTIONAL MATCH (m:Media)-[:APPEARED_IN]->(p)
          RETURN p, m
          ORDER BY p.created_utc DESC
          SKIP toInteger($offset)
          LIMIT toInteger($limit)
        `;
        const result = await session.run(query, { subreddit, limit, offset });
        return result.records.map((record) => {
          const p = record.get("p").properties;
          const m = record.get("m")?.properties || {};
          const createdUtc = p.created_utc;

          let createdAt = new Date().toISOString();
          if (createdUtc !== null && createdUtc !== undefined) {
            try {
              // Handle Neo4j DateTime object
              if (
                createdUtc.toString &&
                typeof createdUtc.toString === "function" &&
                createdUtc.year
              ) {
                createdAt = new Date(createdUtc.toString()).toISOString();
              } else if (typeof createdUtc.toNumber === "function") {
                createdAt = new Date(
                  createdUtc.toNumber() * 1000,
                ).toISOString();
              } else if (typeof createdUtc === "number") {
                createdAt = new Date(createdUtc * 1000).toISOString();
              } else if (typeof createdUtc === "string") {
                createdAt = new Date(createdUtc).toISOString();
              }
            } catch (e) {
              console.error("Date conversion error:", e, createdUtc);
              createdAt = new Date().toISOString();
            }
          }

          // Get image URL from Media node or Post node
          const imageUrl = m.url || m.imageUrl || p.image_url || p.url || null;

          // Determine if this is an image post
          const isImage =
            p.is_image === true ||
            (imageUrl && /\.(jpeg|jpg|png|gif|webp)$/i.test(imageUrl)) ||
            (m.mime_type && m.mime_type.startsWith("image/"));

          // Construct MinIO media URL if media_url exists or we can construct it
          let mediaUrl: string | null = null;
          const minioEndpoint =
            process.env.MINIO_ENDPOINT || "http://localhost:9000";

          if (p.media_url) {
            // Direct media_url from Post node (already includes full MinIO URL)
            mediaUrl = p.media_url;
          } else if (p.media_bucket && p.media_object) {
            // Construct from bucket and object
            mediaUrl = `${minioEndpoint}/${p.media_bucket}/${p.media_object}`;
          } else if (p.sha256_hash && subreddit === "unixporn") {
            // For unixporn, construct URL from SHA256 hash
            // Bucket: unixporn-media, prefix: unixporn/
            const ext = p.media_mime_type?.includes("video")
              ? ".mp4"
              : p.media_mime_type?.includes("image/png")
                ? ".png"
                : p.media_mime_type?.includes("image/jpeg")
                  ? ".jpg"
                  : ".jpg";
            mediaUrl = `${minioEndpoint}/unixporn-media/unixporn/${p.sha256_hash}${ext}`;
          }

          return {
            id: p.id,
            title: p.title || "",
            url: p.url || "",
            permalink:
              p.permalink || p.url || `/r/${subreddit}/comments/${p.id}`,
            author: p.author || null,
            score:
              typeof p.score === "number"
                ? p.score
                : p.score?.toNumber?.() || 0,
            numComments:
              typeof p.num_comments === "number"
                ? p.num_comments
                : p.num_comments?.toNumber?.() || 0,
            upvoteRatio: p.upvote_ratio || 0.95,
            over18: p.over_18 || false,
            selftext: p.selftext || null,
            createdAt,
            subreddit,
            isImage: isImage || false,
            imageUrl: isImage ? imageUrl : null,
            imageWidth:
              m.width?.toNumber?.() || m.width || p.image_width || null,
            imageHeight:
              m.height?.toNumber?.() || m.height || p.image_height || null,
            mediaUrl,
            isRead: false, // TODO: Implement read tracking
          };
        });
      });
    },

    debugStats: async () => {
      return withSession(async (session) => {
        const mediaCount = await session.run(
          "MATCH (m:Media) RETURN count(m) as count",
        );
        const postCount = await session.run(
          "MATCH (p:Post) RETURN count(p) as count",
        );
        const subredditCount = await session.run(
          "MATCH (s:Subreddit) RETURN count(s) as count",
        );

        return {
          mediaCount: mediaCount.records[0].get("count").toNumber(),
          postCount: postCount.records[0].get("count").toNumber(),
          subredditCount: subredditCount.records[0].get("count").toNumber(),
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
        const id = input.id || input.name.toLowerCase().replace(/\s+/g, "-");

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
          bio: input.bio || "",
          avatarUrl: input.avatarUrl || "",
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
                subreddit_name: ${platform === "REDDIT" ? "$username" : "null"},
                youtube_channel_handle: ${platform === "YOUTUBE" ? "$username" : "null"},
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
          contextKeywords: input.contextKeywords
            ? JSON.stringify(input.contextKeywords)
            : null,
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
        return result.records[0].get("deleted").toNumber() > 0;
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
        return (relationships.find((r) => r.targetId === input.targetId) || {
          targetId: input.targetId,
          type: input.type,
        }) as any;
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
        return result.records[0].get("deleted").toNumber() > 0;
      });
    },
  },
};
