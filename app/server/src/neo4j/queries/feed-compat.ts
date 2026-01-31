/**
 * Compatibility Feed Query for Reddit Post Data
 *
 * This version queries Post nodes directly when Media nodes don't exist,
 * providing a bridge between the Reddit data pipeline and Bunny's expectations.
 */

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
}

export async function getFeedFromPosts(
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
  const cacheKey = `feed:posts:${cursor || "initial"}:${limit}:${JSON.stringify(filters || {})}`;
  const valkey = getValkeyClient();

  try {
    const cached = await valkey.get(cacheKey);
    if (cached) {
      logger.debug("Feed cache hit (Posts)", { cacheKey });
      return JSON.parse(cached);
    }
  } catch (err) {
    logger.warn("Feed cache read error", err);
  }

  return withSession(async (session) => {
    // Query Post nodes directly - this is the compatibility layer!
    let query = `
      MATCH (p:Post)
      WHERE p.image_url IS NOT NULL
      OPTIONAL MATCH (p)-[:POSTED_IN]->(s:Subreddit)
      OPTIONAL MATCH (p)<-[:POSTED]-(u:User)
    `;

    const params: any = {
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
      whereConditions.push(`p.created_utc < datetime($cursor)`);
    }

    // Filter by subreddit names
    if (filters?.sources && filters.sources.length > 0) {
      const normalizedSources = filters.sources.map((s) => {
        return s.toLowerCase().startsWith("r/")
          ? s.substring(2).toLowerCase()
          : s.toLowerCase();
      });

      whereConditions.push(
        `(s IS NOT NULL AND toLower(s.name) IN $normalizedSources)`,
      );
      params.normalizedSources = normalizedSources;
    }

    // Filter by search query
    if (filters?.searchQuery && filters.searchQuery.trim().length > 0) {
      whereConditions.push(
        `(p.title IS NOT NULL AND toLower(p.title) CONTAINS toLower($searchQuery))`,
      );
      params.searchQuery = filters.searchQuery;
    }

    if (whereConditions.length > 0) {
      query += ` WHERE ${whereConditions.join(" AND ")}`;
    }

    query += `
      RETURN p, s.name AS subreddit, u.username AS author
      ORDER BY p.created_utc DESC
      LIMIT toInteger($limit)
    `;

    let result;
    try {
      result = await session.run(query, params);
      logger.info("Feed query (Posts)", { recordCount: result.records.length });
    } catch (error: any) {
      logger.error("Cypher query error (Posts)", {
        message: error.message,
        query,
        params,
      });
      return { posts: [], nextCursor: null };
    }

    const posts: FeedPost[] = result.records.slice(0, limit).map((record) => {
      const post = record.get("p")?.properties || {};
      const subreddit = record.get("subreddit");
      const author = record.get("author");

      const title = post.title || "Untitled";

      // Convert Unix timestamp to ISO string
      let publishDateISO: string;
      if (post.created_utc) {
        const timestampMs = Number(post.created_utc) * 1000;
        publishDateISO = new Date(timestampMs).toISOString();
      } else {
        publishDateISO = new Date().toISOString();
      }

      const score = post.score || 0;
      const sourceUrl = post.url || "";
      const platform = "REDDIT";

      const handleStr = subreddit ? `r/${subreddit}` : "";

      // Determine media type from URL or explicit field
      let mediaType = "IMAGE";
      if (post.media_type) {
        mediaType = post.media_type.toUpperCase();
      } else if (
        post.is_video ||
        sourceUrl.includes("v.redd.it") ||
        sourceUrl.includes("youtube.com")
      ) {
        mediaType = "VIDEO";
      }

      return {
        id: post.id || "",
        title,
        imageUrl: post.image_url || post.thumbnail || "",
        sourceUrl,
        publishDate: publishDateISO,
        score,
        width: post.image_width || 600,
        height: post.image_height || 800,
        subreddit: subreddit ? { name: subreddit } : undefined,
        author: author ? { username: author } : null,
        platform,
        handle: {
          name: subreddit || "",
          handle: handleStr,
        },
        mediaType,
        viewCount: post.view_count,
      };
    });

    const hasMore = result.records.length > limit;
    const nextCursor =
      hasMore && posts.length > 0 ? posts[posts.length - 1].publishDate : null;

    const response = { posts, nextCursor };

    try {
      await valkey.setEx(cacheKey, 60, JSON.stringify(response));
      logger.debug("Feed cache set (Posts)", { cacheKey });
    } catch (err) {
      logger.warn("Feed cache write error", err);
    }

    return response;
  });
}

/**
 * Hybrid feed query - tries Media first, falls back to Posts
 */
export async function getFeedHybrid(
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
  return withSession(async (session) => {
    // Quick check: do we have Media nodes?
    const checkQuery = `MATCH (m:Media) RETURN count(m) as mediaCount LIMIT 1`;
    const checkResult = await session.run(checkQuery);
    const mediaCount =
      checkResult.records[0]?.get("mediaCount")?.toNumber() || 0;

    if (mediaCount === 0) {
      logger.info("No Media nodes found, using Post-based feed");
      return getFeedFromPosts(cursor, limit, filters);
    } else {
      logger.info("Media nodes found, using standard feed");
      // Use the existing getFeed function from feed.ts
      const { getFeed } = await import("./feed.js");
      return getFeed(cursor, limit, filters);
    }
  });
}
