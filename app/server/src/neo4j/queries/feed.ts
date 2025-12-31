import { getSession } from '../driver.js';
import type { Session } from 'neo4j-driver';

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
}

export async function getFeed(
  cursor: string | null,
  limit: number = 20,
  filters?: { persons?: string[]; sources?: string[]; tags?: string[]; searchQuery?: string }
): Promise<{ posts: FeedPost[]; nextCursor: string | null }> {
  const session = getSession();
  try {
    // Simplified query - start with just getting Media with Posts
    // Build query incrementally to avoid syntax errors
    let query = `
      MATCH (m:Media)
      WHERE m.mime_type IS NOT NULL 
        AND (m.mime_type STARTS WITH 'image/' OR m.mime_type STARTS WITH 'video/')
      OPTIONAL MATCH (m)-[:APPEARED_IN]->(p:Post)
      OPTIONAL MATCH (p)-[:POSTED_IN]->(s:Subreddit)
      OPTIONAL MATCH (s)<-[:POSTED_IN]-(src:Source)
      OPTIONAL MATCH (src)<-[:HAS_SOURCE]-(e:Entity)
      OPTIONAL MATCH (u:User)-[:POSTED]->(p)
    `;
    
    const params: any = {
      limit: Math.floor(limit) + 1,
    };
    
    // Handle cursor - convert to datetime if provided
    if (cursor) {
      try {
        // Try to parse cursor as ISO string and convert to datetime
        params.cursor = cursor;
      } catch (e) {
        // If cursor is invalid, ignore it
        params.cursor = null;
      }
    } else {
      params.cursor = null;
    }
    
    // Build WHERE conditions after WITH
    const whereConditions: string[] = [];
    
    // Cursor filtering - simplified to avoid datetime() issues
    if (cursor) {
      whereConditions.push(`(
        (p IS NOT NULL AND p.created_utc IS NOT NULL AND p.created_utc < datetime($cursor)) OR
        (p IS NULL AND m.created_at IS NOT NULL AND m.created_at < datetime($cursor))
      )`);
    }
    
    // Filter by persons (entities) - if specified
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
    
    // Filter by sources/platforms - if specified
    if (filters?.sources && filters.sources.length > 0) {
      const normalizedSources = filters.sources.map(s => {
        return s.toLowerCase().startsWith('r/') ? s.substring(2).toLowerCase() : s.toLowerCase();
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
    
    // Filter by search query - if specified
    if (filters?.searchQuery && filters.searchQuery.trim().length > 0) {
      whereConditions.push(`(p IS NOT NULL AND p.title IS NOT NULL AND toLower(p.title) CONTAINS toLower($searchQuery))`);
      params.searchQuery = filters.searchQuery;
    }
    
    // Filter by tags - if specified
    if (filters?.tags && filters.tags.length > 0) {
      whereConditions.push(`(m.tags IS NOT NULL AND ANY(item.tags IN $tags))`);
      params.tags = filters.tags;
    }
    
    // Ensure sources are not hidden (unless filtering by persons)
    if (!filters?.persons || filters.persons.length === 0) {
      whereConditions.push(`(src IS NULL OR src.hidden IS NULL OR src.hidden = false)`);
    }
    
    // Add WITH and WHERE if we have conditions
    if (whereConditions.length > 0) {
      query += ` WITH m, p, s, src, e, u WHERE ${whereConditions.join(' AND ')}`;
    } else {
      query += ` WITH m, p, s, src, e, u`;
    }
    
    // Final query to return results
    query += `
      RETURN m, p, s.name AS subreddit, u.username AS author, src, e, m.width AS width, m.height AS height
      ORDER BY COALESCE(p.created_utc, m.created_at) DESC
      LIMIT toInteger($limit)
    `;

    let result;
    try {
      result = await session.run(query, params);
    } catch (error: any) {
      console.error('Cypher query error:', error.message);
      console.error('Query:', query);
      console.error('Params:', JSON.stringify(params, null, 2));
      // Return empty result instead of crashing the server
      return { posts: [], nextCursor: null };
    }

    const posts: FeedPost[] = result.records.slice(0, limit).map((record) => {
      const media = record.get('m')?.properties || {};
      const post = record.get('p')?.properties;
      const source = record.get('src')?.properties;
      const entity = record.get('e')?.properties;
      const subreddit = record.get('subreddit');
      const author = record.get('author');
      const width = record.get('width') || media.width;
      const height = record.get('height') || media.height;

      // Get data from Post if available, otherwise from Media
      const title = post?.title || '';

      // Handle publishDate - could be Unix timestamp (number) or Neo4j DateTime
      let publishDateISO: string;
      if (post?.created_utc) {
        // Unix timestamp in seconds
        const timestampMs = Number(post.created_utc) * 1000;
        publishDateISO = new Date(timestampMs).toISOString();
      } else if (media.created_at) {
        // Neo4j DateTime object - has toString() method
        publishDateISO = media.created_at.toString();
      } else {
        publishDateISO = new Date().toISOString();
      }

      const score = post?.score || 0;
      const sourceUrl = post?.url || media.url || '';

      // Determine platform from source type
      const platform = source?.source_type?.toUpperCase() || 'REDDIT';
      
      // Build handle string
      let handleStr = '';
      if (subreddit) {
        handleStr = `r/${subreddit}`;
      } else if (source) {
        if (source.source_type === 'reddit' && source.subreddit_name) {
          handleStr = `r/${source.subreddit_name}`;
        } else if (source.source_type === 'youtube' && source.youtube_channel_handle) {
          handleStr = source.youtube_channel_handle;
        } else {
          handleStr = source.name || '';
        }
      }

      // Determine media type from Media node or Post
      let mediaType = 'IMAGE';
      if (media.mime_type) {
        if (media.mime_type.startsWith('video/')) mediaType = 'VIDEO';
        else mediaType = 'IMAGE';
      } else if (post?.media_type) {
        mediaType = post.media_type.toUpperCase();
      }

      return {
        id: media.id || post?.id || '',
        title,
        imageUrl: media.url || post?.image_url || '',
        sourceUrl,
        publishDate: publishDateISO,
        score,
        width: width || post?.image_width || 600,
        height: height || post?.image_height || 800,
        subreddit: subreddit ? { name: subreddit } : undefined,
        author: author ? { username: author } : null,
        platform,
        handle: {
          name: entity?.name || entity?.display_name || subreddit || '',
          handle: handleStr,
          creatorName: entity?.name,
        },
        mediaType,
        viewCount: post?.view_count || media.view_count,
        sha256: media.sha256,
        mimeType: media.mime_type,
        storagePath: media.storage_path,
      };
    });

    const hasMore = result.records.length > limit;
    const nextCursor = hasMore && posts.length > 0
      ? posts[posts.length - 1].publishDate
      : null;

    return { posts, nextCursor };
  } catch (error: any) {
    // Top-level error handler - ensure server never crashes
    console.error('getFeed error:', error);
    console.error('Error stack:', error.stack);
    return { posts: [], nextCursor: null };
  } finally {
    await session.close();
  }
}


