/**
 * Data Factory for generating Article/FeedItem mock data
 * 
 * Provides deterministic factories for creating test data based on templates.
 * Uses real Reddit post data as templates, then generates variations.
 * 
 * Matches GraphQL schema format from pre-transformed-loader.ts
 */

import type { GraphQLFeedNode } from '../graphql/mocks/pre-transformed-loader';

export interface ArticleTemplate extends GraphQLFeedNode {
  // Template extends GraphQLFeedNode for consistency
}

export interface ArticleFactoryOptions {
  id?: string;
  title?: string;
  imageUrl?: string | null;
  score?: number;
  author?: { username: string };
  subreddit?: { name: string };
  timestamp?: Date | string;
  isRead?: boolean;
}

/**
 * Create an article from a template with optional overrides
 * Returns GraphQLFeedNode format matching our schema
 */
export function createArticle(id: string | number, template: ArticleTemplate, overrides: ArticleFactoryOptions = {}): GraphQLFeedNode {
  const articleId = typeof id === 'number' ? `post_${id}` : id;
  const subredditName = overrides.subreddit?.name || template.subreddit.name;
  
  return {
    id: overrides.id || articleId,
    title: overrides.title || template.title,
    imageUrl: overrides.imageUrl !== undefined ? overrides.imageUrl : (template.imageUrl || `/temp/mock_data/${subredditName}/images/${template.id}.jpg`),
    sourceUrl: template.sourceUrl || `https://reddit.com/r/${subredditName}/comments/${articleId}`,
    publishDate: typeof overrides.timestamp === 'string' 
      ? new Date(overrides.timestamp).toISOString()
      : overrides.timestamp instanceof Date
      ? overrides.timestamp.toISOString()
      : template.publishDate,
    score: overrides.score ?? template.score ?? Math.floor(Math.random() * 1000),
    width: template.width ?? null,
    height: template.height ?? null,
    subreddit: overrides.subreddit || template.subreddit,
    author: overrides.author || template.author,
    platform: template.platform || 'REDDIT',
    handle: template.handle || {
      name: `r/${subredditName}`,
      handle: `r/${subredditName}`,
    },
    mediaType: template.mediaType || 'IMAGE',
    viewCount: template.viewCount ?? 0,
  };
}

/**
 * Generate a feed of articles from templates
 * 
 * @param templates Array of template articles to clone/vary
 * @param count Number of articles to generate
 * @returns Array of generated articles in GraphQLFeedNode format
 */
export function createFeed(templates: ArticleTemplate[], count: number): GraphQLFeedNode[] {
  const articles: GraphQLFeedNode[] = [];
  
  if (templates.length === 0) {
    return articles;
  }
  
  for (let i = 0; i < count; i++) {
    const template = templates[i % templates.length];
    const variationIndex = Math.floor(i / templates.length);
    
    articles.push(createArticle(i, template, {
      title: variationIndex > 0 ? `${template.title} (${variationIndex + 1})` : template.title,
      timestamp: new Date(Date.now() - i * 3600000), // Stagger by 1 hour
      score: template.score ? template.score + variationIndex * 10 : Math.floor(Math.random() * 1000),
    }));
  }
  
  return articles;
}

/**
 * Create articles for a specific scenario
 * All scenarios return GraphQLFeedNode[] format
 */
export const Scenarios = {
  /**
   * Empty feed scenario
   */
  emptyFeed: (): GraphQLFeedNode[] => [],
  
  /**
   * Large feed scenario (5000 items)
   */
  largeFeed: (templates: ArticleTemplate[]): GraphQLFeedNode[] => {
    if (templates.length === 0) return [];
    return createFeed(templates, 5000);
  },
  
  /**
   * Single subscription feed (filtered by subreddit)
   */
  singleSubscription: (templates: ArticleTemplate[], subreddit: string): GraphQLFeedNode[] => {
    const filtered = templates.filter(t => t.subreddit.name === subreddit || t.subreddit.name.toLowerCase() === subreddit.toLowerCase());
    if (filtered.length === 0) return [];
    return createFeed(filtered, 100);
  },
  
  /**
   * Recent articles only (last 24 hours)
   */
  recentArticles: (templates: ArticleTemplate[]): GraphQLFeedNode[] => {
    if (templates.length === 0) return [];
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const recent = createFeed(templates, Math.min(100, templates.length * 2));
    return recent.filter(a => new Date(a.publishDate) > oneDayAgo);
  },
  
  /**
   * High-score articles only (top scoring)
   */
  topScoring: (templates: ArticleTemplate[], minScore: number = 100): GraphQLFeedNode[] => {
    if (templates.length === 0) return [];
    const highScoring = templates.filter(t => t.score >= minScore);
    if (highScoring.length === 0) return createFeed(templates, 50); // Fallback to regular feed
    return createFeed(highScoring, 100);
  },
};

