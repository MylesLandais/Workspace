import { getSession } from '../driver.js';
import type { Session } from 'neo4j-driver';

export interface FeedPost {
  id: string;
  title: string;
  imageUrl: string;
  sourceUrl: string;
  publishDate: string;
  score?: number;
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
}

export async function getFeed(cursor: string | null, limit: number = 20): Promise<{ posts: FeedPost[]; nextCursor: string | null }> {
  const session = getSession();
  try {
    const query = `
      MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
      WHERE p.is_image = true
        AND ($cursor IS NULL OR p.created_utc < datetime($cursor))
      OPTIONAL MATCH (u:User)-[:POSTED]->(p)
      RETURN p, s.name AS subreddit, u.username AS author
      ORDER BY p.created_utc DESC
      LIMIT $limit
    `;

    const result = await session.run(query, {
      cursor: cursor ? cursor : null,
      limit: limit + 1,
    });

    const posts: FeedPost[] = result.records.slice(0, limit).map((record) => {
      const post = record.get('p').properties;
      const subreddit = record.get('subreddit');
      const author = record.get('author');

      return {
        id: post.id,
        title: post.title || '',
        imageUrl: post.image_url || '',
        sourceUrl: post.url || '',
        publishDate: post.created_utc ? new Date(post.created_utc.toString()).toISOString() : new Date().toISOString(),
        score: post.score || 0,
        subreddit: subreddit ? { name: subreddit } : undefined,
        author: author ? { username: author } : null,
        platform: 'reddit',
        handle: {
          name: subreddit || '',
          handle: subreddit ? `r/${subreddit}` : '',
        },
        mediaType: 'image',
      };
    });

    const hasMore = result.records.length > limit;
    const nextCursor = hasMore && posts.length > 0
      ? posts[posts.length - 1].publishDate
      : null;

    return { posts, nextCursor };
  } finally {
    await session.close();
  }
}


