/**
 * Data Factory for generating Article/FeedItem mock data
 * 
 * Provides deterministic factories for creating test data based on templates.
 * Uses real Reddit post data as templates, then generates variations.
 */

interface ArticleTemplate {
  id: string;
  title: string;
  caption?: string;
  imageUrl?: string;
  score?: number;
  author?: string;
  subreddit: string;
  timestamp: string;
}

interface ArticleFactoryOptions {
  id?: string;
  title?: string;
  imageUrl?: string;
  score?: number;
  author?: string;
  subreddit?: string;
  timestamp?: Date | string;
  isRead?: boolean;
}

/**
 * Create an article from a template with optional overrides
 */
export function createArticle(id: string | number, template: ArticleTemplate, overrides: ArticleFactoryOptions = {}) {
  const articleId = typeof id === 'number' ? `post_${id}` : id;
  
  return {
    id: overrides.id || articleId,
    title: overrides.title || template.title,
    caption: template.caption || template.title,
    imageUrl: overrides.imageUrl || template.imageUrl || `/temp/mock_data/${template.subreddit}/images/${template.id}.jpg`,
    sourceUrl: `https://reddit.com/r/${overrides.subreddit || template.subreddit}/comments/${articleId}`,
    publishDate: typeof overrides.timestamp === 'string' 
      ? new Date(overrides.timestamp).toISOString()
      : overrides.timestamp instanceof Date
      ? overrides.timestamp.toISOString()
      : template.timestamp,
    score: overrides.score ?? template.score ?? Math.floor(Math.random() * 1000),
    width: null,
    height: null,
    subreddit: {
      name: overrides.subreddit || template.subreddit,
    },
    author: {
      username: overrides.author || template.author || 'unknown',
    },
    platform: 'REDDIT' as const,
    handle: {
      name: `r/${overrides.subreddit || template.subreddit}`,
      handle: `r/${overrides.subreddit || template.subreddit}`,
    },
    mediaType: 'IMAGE' as const,
    viewCount: 0,
    isRead: overrides.isRead ?? Math.random() > 0.6, // 60% unread
  };
}

/**
 * Generate a feed of articles from templates
 * 
 * @param templates Array of template articles to clone/vary
 * @param count Number of articles to generate
 * @returns Array of generated articles
 */
export function createFeed(templates: ArticleTemplate[], count: number) {
  const articles = [];
  
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
 */
export const Scenarios = {
  /**
   * Empty feed scenario
   */
  emptyFeed: () => [],
  
  /**
   * Large feed scenario (5000 items)
   */
  largeFeed: (templates: ArticleTemplate[]) => createFeed(templates, 5000),
  
  /**
   * Single subscription feed
   */
  singleSubscription: (templates: ArticleTemplate[], subreddit: string) => {
    const filtered = templates.filter(t => t.subreddit === subreddit);
    return createFeed(filtered, 100);
  },
  
  /**
   * Mixed read/unread feed
   */
  mixedReadState: (templates: ArticleTemplate[], readRatio: number = 0.4) => {
    const articles = createFeed(templates, 100);
    articles.forEach((article, index) => {
      article.isRead = index % (1 / readRatio) === 0;
    });
    return articles;
  },
  
  /**
   * Recent articles only (last 24 hours)
   */
  recentArticles: (templates: ArticleTemplate[]) => {
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const recent = createFeed(templates, 50);
    return recent.filter(a => new Date(a.publishDate) > oneDayAgo);
  },
};




