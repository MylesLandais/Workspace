import { withSession } from "../../lib/session.js";
import { getValkeyClient } from "../../valkey/client.js";
import logger from "../../lib/logger.js";

export interface FeedPost {
  id: string;
  title: string;
  imageUrl: string;
  sourceUrl: string;
  publishDate: string;
  score?: number;
  width?: number;
  height?: number;
  subreddit?: {
    name: string;
  };
  author?: {
    username: string;
  } | null;
  platform: string;
  handle: {
    name: string;
    handle: string;
    creatorName?: string;
  };
  mediaType: string;
  viewCount?: number;
  sha256?: string;
  mimeType?: string;
  storagePath?: string;
  isRead: boolean; // Add isRead status
}

export async function getFeed(
  userId: string | null,
  cursor: string | null,
  limit: number = 20,
  filters?: {
    persons?: string[];
    sources?: string[];
    tags?: string[];
    searchQuery?: string;
    categories?: string[];
  },
): Promise<{ posts: FeedPost[]; nextCursor: string | null }> {
  // Generate cache key
  const cacheKey = `feed:${cursor || "initial"}:${limit}:${JSON.stringify(filters || {})}`;
  const valkey = getValkeyClient();

  try {
    const cached = await valkey.get(cacheKey);
    if (cached) {
      logger.debug("Feed cache hit", { cacheKey });
      return JSON.parse(cached);
    }
  } catch (err) {
    logger.warn("Feed cache read error", err);
  }

  return withSession(async (session) => {
    let query = `
      MATCH (m:Media)
      WHERE m.mime_type IS NOT NULL 
        AND (m.mime_type STARTS WITH 'image/' OR m.mime_type STARTS WITH 'video/')
      OPTIONAL MATCH (m)-[:APPEARED_IN]->(p:Post)
      OPTIONAL MATCH (p)-[:POSTED_IN]->(s:Subreddit)
      OPTIONAL MATCH (s)<-[:POSTED_IN]-(src:Source)
      OPTIONAL MATCH (src)<-[:HAS_SOURCE]-(e:Entity)
      OPTIONAL MATCH (u:User)-[:POSTED]->(p)
      OPTIONAL MATCH (reader:User {id: $userId})-[reads:READS]->(p) // Check read status
    `;

    const params: any = {
      userId: userId, // Pass userId for the READS check
      limit: Math.floor(limit) + 1,
    };

    if (cursor) {
      try {
        params.cursor = cursor;
      } catch (e) {
        params.cursor = null;
      }
    } else {
      params.cursor = null;
    }

    const whereConditions: string[] = [];

    if (cursor) {
      whereConditions.push(`(
        (p IS NOT NULL AND p.created_utc IS NOT NULL AND p.created_utc < datetime($cursor)) OR
        (p IS NULL AND m.created_at IS NOT NULL AND m.created_at < datetime($cursor))
      )`);
    }

    if (filters?.persons && filters.persons.length > 0) {
      whereConditions.push(`(
        e IS NOT NULL AND (
          e.name IN $persons 
          OR e.display_name IN $persons 
          OR e.id IN $persons
        )
      )`);
      params.persons = filters.persons;
    }

    if (filters?.sources && filters.sources.length > 0) {
      const normalizedSources = filters.sources.map((s) => {
        return s.toLowerCase().startsWith("r/")
          ? s.substring(2).toLowerCase()
          : s.toLowerCase();
      });

      whereConditions.push(`(
        (s IS NOT NULL AND toLower(s.name) IN $normalizedSources)
        OR (src IS NOT NULL AND src.subreddit_name IS NOT NULL AND toLower(src.subreddit_name) IN $normalizedSources)
        OR (src IS NOT NULL AND toLower(src.name) IN $normalizedSources)
        OR (src IS NOT NULL AND toLower(src.source_type) IN $normalizedSources)
      )`);
      params.sources = filters.sources;
      params.normalizedSources = normalizedSources;
    }

    if (filters?.searchQuery && filters.searchQuery.trim().length > 0) {
      whereConditions.push(
        `(p IS NOT NULL AND p.title IS NOT NULL AND toLower(p.title) CONTAINS toLower($searchQuery))`,
      );
      params.searchQuery = filters.searchQuery;
    }

    if (filters?.tags && filters.tags.length > 0) {
      whereConditions.push(`(m.tags IS NOT NULL AND ANY(item.tags IN $tags))`);
      params.tags = filters.tags;
    }

    if (filters?.categories && filters.categories.length > 0) {
      const mediaTypeConditions: string[] = [];
      for (const cat of filters.categories) {
        const upperCat = cat.toUpperCase();
        if (upperCat === "IMAGE" || upperCat === "PHOTO") {
          mediaTypeConditions.push(`m.mime_type STARTS WITH 'image/'`);
        } else if (upperCat === "VIDEO") {
          mediaTypeConditions.push(`m.mime_type STARTS WITH 'video/'`);
        } else if (upperCat === "GIF") {
          mediaTypeConditions.push(
            `(m.mime_type = 'image/gif' OR m.mime_type = 'video/mp4')`,
          );
        }
      }

      if (mediaTypeConditions.length > 0) {
        whereConditions.push(`(${mediaTypeConditions.join(" OR ")})`);
      }
      params.categories = filters.categories;
    }

    if (!filters?.persons || filters.persons.length === 0) {
      whereConditions.push(
        `(src IS NULL OR src.hidden IS NULL OR src.hidden = false)`,
      );
    }

    if (whereConditions.length > 0) {
      query += ` WITH m, p, s, src, e, u WHERE ${whereConditions.join(" AND ")}`;
    } else {
      query += ` WITH m, p, s, src, e, u`;
    }

    query += `
      RETURN m, p, s.name AS subreddit, u.username AS author, src, e, m.width AS width, m.height AS height,
             p.sha256_hash AS sha256_hash, p.media_mime_type AS media_mime_type, reads IS NOT NULL AS isRead
      ORDER BY COALESCE(p.created_utc, m.created_at) DESC
      LIMIT toInteger($limit)
    `;

    let result;
    try {
      result = await session.run(query, params);
    } catch (error: any) {
      logger.error("Cypher query error", {
        message: error.message,
        query,
        params,
      });
      return { posts: [], nextCursor: null };
    }

    const posts: FeedPost[] = result.records.slice(0, limit).map((record) => {
      const media = record.get("m")?.properties || {};
      const post = record.get("p")?.properties;
      const source = record.get("src")?.properties;
      const entity = record.get("e")?.properties;
      const subreddit = record.get("subreddit");
      const author = record.get("author");
      const width = record.get("width") || media.width;
      const height = record.get("height") || media.height;
      const sha256_hash = record.get("sha256_hash") || media.sha256;
      const media_mime_type = record.get("media_mime_type") || media.mime_type;
      const isRead = record.get("isRead") || false; // Fetch isRead status

      const title = post?.title || "";

      let publishDateISO: string;
      if (post?.created_utc) {
        const timestampMs = Number(post.created_utc) * 1000;
        publishDateISO = new Date(timestampMs).toISOString();
      } else if (media.created_at) {
        publishDateISO = media.created_at.toString();
      } else {
        publishDateISO = new Date().toISOString();
      }

      const score = post?.score || 0;
      const sourceUrl = post?.url || media.url || "";
      const platform = source?.source_type?.toUpperCase() || "REDDIT";

      let handleStr = "";
      if (subreddit) {
        handleStr = `r/${subreddit}`;
      } else if (source) {
        if (source.source_type === "reddit" && source.subreddit_name) {
          handleStr = `r/${source.subreddit_name}`;
        } else if (
          source.source_type === "youtube" &&
          source.youtube_channel_handle
        ) {
          handleStr = source.youtube_channel_handle;
        } else {
          handleStr = source.name || "";
        }
      }

      let mediaType = "IMAGE";
      if (media_mime_type) {
        if (media_mime_type.startsWith("video/")) mediaType = "VIDEO";
        else mediaType = "IMAGE";
      } else if (post?.media_type) {
        mediaType = post.media_type.toUpperCase();
      }

      return {
        id: media.id || post?.id || "",
        title,
        imageUrl: media.url || post?.image_url || "",
        sourceUrl,
        publishDate: publishDateISO,
        score,
        width: width || post?.image_width || 600,
        height: height || post?.image_height || 800,
        subreddit: subreddit ? { name: subreddit } : undefined,
        author: author ? { username: author } : null,
        platform,
        handle: {
          name: entity?.name || entity?.display_name || subreddit || "",
          handle: handleStr,
          creatorName: entity?.name,
        },
        mediaType,
        viewCount: post?.view_count || media.view_count,
        sha256: sha256_hash,
        mimeType: media_mime_type,
        storagePath: media.storage_path,
        isRead, // Include isRead
      };
    });

    const hasMore = result.records.length > limit;
    const nextCursor =
      hasMore && posts.length > 0 ? posts[posts.length - 1].publishDate : null;

    const response = { posts, nextCursor };

    try {
      await valkey.setEx(cacheKey, 60, JSON.stringify(response));
      logger.debug("Feed cache set", { cacheKey });
    } catch (err) {
      logger.warn("Feed cache write error", err);
    }

    return response;
  });
}
