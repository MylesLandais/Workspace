/**
 * Bunny GUI: Unified Mock Data Factory
 * 
 * This factory abstracts server interface and provides mock data for:
 * - Bunny Visual Feed (Media items, galleries, marketplace)
 * - Reader Reader (Long-form articles, AI summaries, insights)
 * - Unified Schema V2 entities (Persons, Sources, Boards)
 * 
 * Designed for Client-First development - no backend required.
 */

import type { 
  FeedItem, 
  MediaType, 
  IdentityProfile, 
  SavedBoard, 
  Comment, 
  RelatedThread, 
  PlatformType 
} from '../bunny/types';

// Import MediaType enum as a value for comparisons
import { MediaType as MediaTypeEnum } from '../bunny/types';

// ============================================================================
// SCHEMA V2: UNIFIED CLIENT INTERFACES
// ============================================================================

export type ViewMode = 'visual' | 'reader' | 'inbox' | 'archive';

export interface Article {
  id: string;
  sourceId: string;
  title: string;
  author: string;
  content: string; // HTML or Text content
  summary?: string; // AI Generated summary
  keyTakeaways?: string[]; // AI Generated
  publishedAt: string;
  read: boolean;
  saved: boolean;
  archived: boolean;
  tags: string[];
  type: PlatformType;
  url: string;
  imageUrl?: string;
  imageWidth?: number;
  imageHeight?: number;
  sauce?: SauceResult;
}

export interface SauceResult {
  similarity: number;
  sourceUrl: string;
  artistName: string;
  extUrl?: string;
}

export interface UnifiedContent {
  id: string;
  // Common fields
  title: string;
  author: { name: string; handle: string };
  source: string;
  platform: PlatformType;
  timestamp: string;
  tags: string[];
  
  // Visual Feed fields (Bunny)
  mediaUrl?: string;
  thumbnailUrl?: string;
  galleryUrls?: string[];
  type?: MediaType;
  aspectRatio?: string;
  width?: number;
  height?: number;
  likes?: number;
  
  // Reader fields (Reader)
  content?: string;
  summary?: string;
  keyTakeaways?: string[];
  read?: boolean;
  saved?: boolean;
  archived?: boolean;
  
  // Marketplace fields
  price?: number;
  currency?: string;
  condition?: string;
  isSold?: boolean;
  
  // Metadata
  permalink?: string;
  comments?: Comment[];
  relatedThreads?: RelatedThread[];
}

export interface Board {
  id: string;
  name: string;
  description?: string;
  articleIds: string[];
  viewMode: ViewMode;
  filters: {
    persons: string[];
    sources: string[];
    tags: string[];
    searchQuery: string;
  };
  createdAt: string;
}

// ============================================================================
// MOCK DATA GENERATORS
// ============================================================================

class MockDataFactory {
  private static instance: MockDataFactory;
  private contentCache: Map<string, UnifiedContent[]> = new Map();
  private boardCache: Map<string, Board> = new Map();
  private identityCache: Map<string, IdentityProfile> = new Map();

  private constructor() {
    this.initializeDemoData();
  }

  static getInstance(): MockDataFactory {
    if (!MockDataFactory.instance) {
      MockDataFactory.instance = new MockDataFactory();
    }
    return MockDataFactory.instance;
  }

  private initializeDemoData() {
    // Initialize demo identities
    this.identities = this.getDemoIdentities();
    
    // Initialize demo boards
    this.boards = this.getDemoBoards();
    
    // Initialize demo content
    this.contentCache.set('all', this.generateDemoContent());
  }

  // ============================================================================
  // CONTENT GENERATION
  // ============================================================================

  /**
   * Generate demo content for visual feed and reader
   */
  private generateDemoContent(count: number = 50): UnifiedContent[] {
    const content: UnifiedContent[] = [];
    const templates = this.getContentTemplates();

    for (let i = 0; i < count; i++) {
      const template = templates[i % templates.length];
      const item = this.createContentItem(i, template);
      content.push(item);
    }

    return content.sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }

  private createContentItem(id: number, template: Partial<UnifiedContent>): UnifiedContent {
    const isVisual = Math.random() > 0.3; // 70% visual, 30% long-form
    
    return {
      id: `content-${id}`,
      title: template.title || `Sample Content ${id}`,
      author: template.author || { name: 'Demo User', handle: '@demo' },
      source: template.source || 'r/demo',
      platform: template.platform || 'reddit',
      timestamp: new Date(Date.now() - id * 3600000).toISOString(),
      tags: template.tags || [],
      
      // Visual fields
      mediaUrl: isVisual ? template.mediaUrl : undefined,
      thumbnailUrl: isVisual ? template.thumbnailUrl : undefined,
      galleryUrls: template.galleryUrls,
      type: template.type,
      aspectRatio: template.aspectRatio,
      width: template.width,
      height: template.height,
      likes: template.likes || Math.floor(Math.random() * 10000),
      
      // Reader fields
      content: !isVisual ? this.generateLongFormContent() : undefined,
      summary: !isVisual ? this.generateSummary() : undefined,
      keyTakeaways: !isVisual ? this.generateKeyTakeaways() : undefined,
      read: false,
      saved: false,
      archived: false,
      
      // Marketplace fields (randomly assigned)
      price: Math.random() > 0.8 ? Math.floor(Math.random() * 500) + 10 : undefined,
      currency: '$',
      condition: Math.random() > 0.8 ? 'New' : undefined,
      isSold: Math.random() > 0.9,
      
      // Metadata
      permalink: `https://example.com/content/${id}`,
      comments: this.generateComments(),
      relatedThreads: this.generateRelatedThreads(),
    };
  }

  private generateLongFormContent(): string {
    const paragraphs = [
      'This is a comprehensive article about the topic at hand. We explore various aspects and provide detailed analysis.',
      'The research shows significant trends in this area. Many experts have weighed in on the subject.',
      'Looking at the data from multiple perspectives, we can see clear patterns emerging.',
      'In conclusion, this topic requires further study and ongoing attention from the community.'
    ];
    return paragraphs.join('\n\n');
  }

  private generateSummary(): string {
    const summaries = [
      'A comprehensive overview of the topic with key insights and data analysis.',
      'This article explores emerging trends and provides actionable recommendations.',
      'An in-depth look at the subject matter with expert commentary and research.',
      'A detailed examination of the topic with practical takeaways for readers.'
    ];
    return summaries[Math.floor(Math.random() * summaries.length)];
  }

  private generateKeyTakeaways(): string[] {
    const takeaways = [
      'Key finding: The data shows a 25% increase in engagement',
      'Important: Experts recommend a phased approach to implementation',
      'Critical: Security considerations should be prioritized',
      'Notable: User feedback has been overwhelmingly positive',
      'Trend: This pattern is expected to continue through Q4'
    ];
    return takeaways.slice(0, Math.floor(Math.random() * 3) + 2);
  }

  private generateComments(): Comment[] {
    const count = Math.floor(Math.random() * 10) + 1;
    const comments: Comment[] = [];
    
    for (let i = 0; i < count; i++) {
      comments.push({
        id: `comment-${i}`,
        author: `user_${Math.floor(Math.random() * 1000)}`,
        body: `This is a comment with some thoughts on the content. ${i}`,
        score: Math.floor(Math.random() * 100),
        timestamp: new Date(Date.now() - i * 3600000).toISOString()
      });
    }
    
    return comments;
  }

  private generateRelatedThreads(): RelatedThread[] {
    const threads: RelatedThread[] = [];
    const count = Math.floor(Math.random() * 3);
    
    for (let i = 0; i < count; i++) {
      threads.push({
        id: `thread-${i}`,
        title: `Related discussion ${i + 1}`,
        subreddit: 'r/example',
        url: `https://reddit.com/r/example/thread${i}`,
        type: i % 2 === 0 ? 'crosspost' : 'mention'
      });
    }
    
    return threads;
  }

  private getContentTemplates(): Partial<UnifiedContent>[] {
    return [
      // Linux Rice Templates
      {
        title: '[Hyprland] My first rice! Catppuccin theme + Waybar',
        author: { name: 'linux_wizard', handle: 'u/linux_wizard' },
        source: 'r/unixporn',
        platform: 'reddit',
        tags: ['linux', 'hyprland', 'rice', 'catppuccin'],
        mediaUrl: 'https://images.unsplash.com/photo-1550439062-609e1531270e?auto=format&fit=crop&w=1200&q=80',
        thumbnailUrl: 'https://images.unsplash.com/photo-1550439062-609e1531270e?auto=format&fit=crop&w=400&q=80',
        type: MediaTypeEnum.IMAGE,
        aspectRatio: 'aspect-video',
        width: 1920,
        height: 1080,
        likes: 4520
      },
      {
        title: 'KDE Plasma 6 is looking buttery smooth on Arch',
        author: { name: 'arch_user_btw', handle: 'u/arch_user_btw' },
        source: 'r/kde',
        platform: 'reddit',
        tags: ['kde', 'plasma', 'arch', 'linux'],
        mediaUrl: 'https://images.unsplash.com/photo-1629654297299-c8506221ca97?auto=format&fit=crop&w=1200&q=80',
        thumbnailUrl: 'https://images.unsplash.com/photo-1629654297299-c8506221ca97?auto=format&fit=crop&w=400&q=80',
        type: MediaTypeEnum.IMAGE,
        aspectRatio: 'aspect-video',
        width: 1920,
        height: 1080,
        likes: 1200
      },
      
      // Taylor Swift Templates
      {
        title: 'Surprise song from last night in Tokyo! 🎸',
        author: { name: 'TaylorSwift', handle: '@taylorswift' },
        source: 'Instagram',
        platform: 'instagram',
        tags: ['taylor swift', 'concert', 'eras tour', 'tokyo'],
        mediaUrl: 'https://images.unsplash.com/photo-1493225255756-d9584f8606e9?auto=format&fit=crop&w=800&q=80',
        thumbnailUrl: 'https://images.unsplash.com/photo-1493225255756-d9584f8606e9?auto=format&fit=crop&w=400&q=80',
        type: MediaTypeEnum.IMAGE,
        aspectRatio: 'aspect-[3/4]',
        width: 800,
        height: 1200,
        likes: 15000
      },
      {
        title: 'Backstage clips #ErasTour',
        author: { name: 'taylorswift', handle: '@taylorswift' },
        source: 'Instagram',
        platform: 'instagram',
        tags: ['taylor swift', 'backstage', 'eras tour', 'video'],
        mediaUrl: 'https://images.unsplash.com/photo-1516280440614-6697288d5d38?auto=format&fit=crop&w=800&q=80',
        thumbnailUrl: 'https://images.unsplash.com/photo-1516280440614-6697288d5d38?auto=format&fit=crop&w=400&q=80',
        type: MediaTypeEnum.SHORT,
        aspectRatio: 'aspect-[9/16]',
        width: 1080,
        height: 1920,
        likes: 250000
      },
      
      // Selena Gomez Templates
      {
        title: 'New Rare Beauty blush launch event 🌸',
        author: { name: 'selenagomez', handle: '@selenagomez' },
        source: 'Instagram',
        platform: 'instagram',
        tags: ['selena gomez', 'rare beauty', 'makeup', 'launch'],
        mediaUrl: 'https://images.unsplash.com/photo-1512310604669-443f26c35f52?auto=format&fit=crop&w=800&q=80',
        thumbnailUrl: 'https://images.unsplash.com/photo-1512310604669-443f26c35f52?auto=format&fit=crop&w=400&q=80',
        type: MediaTypeEnum.IMAGE,
        aspectRatio: 'aspect-square',
        width: 1080,
        height: 1080,
        likes: 980000
      },
      
      // Marketplace Templates
      {
        title: 'Vintage mechanical keyboard - restored',
        author: { name: 'keyboard_enthusiast', handle: '@keyboard_enthusiast' },
        source: 'r/mechmarket',
        platform: 'reddit',
        tags: ['keyboard', 'vintage', 'mechanical', 'for sale'],
        mediaUrl: 'https://images.unsplash.com/photo-1595225476474-87563907a212?auto=format&fit=crop&w=800&q=80',
        thumbnailUrl: 'https://images.unsplash.com/photo-1595225476474-87563907a212?auto=format&fit=crop&w=400&q=80',
        type: MediaTypeEnum.IMAGE,
        aspectRatio: 'aspect-square',
        width: 800,
        height: 800,
        likes: 245,
        price: 150,
        currency: '$',
        condition: 'Used - Like New',
        isSold: false
      },
      {
        title: 'SOLD: Custom keycap set - GMK',
        author: { name: 'keycap_artist', handle: '@keycap_artist' },
        source: 'r/mechmarket',
        platform: 'reddit',
        tags: ['keycaps', 'gmk', 'custom', 'sold'],
        mediaUrl: 'https://images.unsplash.com/photo-1587829741301-dc798b91a603?auto=format&fit=crop&w=800&q=80',
        thumbnailUrl: 'https://images.unsplash.com/photo-1587829741301-dc798b91a603?auto=format&fit=crop&w=400&q=80',
        type: MediaTypeEnum.IMAGE,
        aspectRatio: 'aspect-square',
        width: 800,
        height: 800,
        likes: 512,
        price: 120,
        currency: '$',
        condition: 'New',
        isSold: true
      },
      
      // Long-form Article Templates
      {
        title: 'The Future of Desktop Linux: A Deep Dive',
        author: { name: 'linux_analyst', handle: '@linux_analyst' },
        source: 'r/linux',
        platform: 'reddit',
        tags: ['linux', 'analysis', 'desktop', 'future'],
        type: MediaTypeEnum.TEXT,
        likes: 3420
      },
      {
        title: 'Understanding Music Industry Trends in 2025',
        author: { name: 'music_insider', handle: '@music_insider' },
        source: 'Newsletter',
        platform: 'web',
        tags: ['music', 'industry', 'trends', '2025'],
        type: MediaTypeEnum.TEXT,
        likes: 1200
      }
    ];
  }

  // ============================================================================
  // IDENTITIES (Entities/Actors/Persons)
  // ============================================================================

  /**
   * Standardized entity registry for frontend validation at scale
   * All entities are keyed by slug for consistent lookup
   */
  private getDemoIdentities(): Record<string, IdentityProfile> {
    return {
      'taylor-swift': {
        id: 'taylor-swift',
        name: 'Taylor Swift',
        bio: 'The music industry.',
        avatarUrl: 'https://images.unsplash.com/photo-1514525253440-b393452e3383?auto=format&fit=crop&w=400&q=80',
        aliases: ['taylor swift', 'taylor', 'tswift', 'blondie'],
        sources: [
          { platform: 'reddit', id: 'TaylorSwift', label: 'Main', hidden: false },
          { platform: 'instagram', id: 'taylorswift', label: 'Official', hidden: false },
          { platform: 'twitter', id: 'taylorswift13', label: 'News', hidden: false }
        ],
        contextKeywords: ['Eras Tour', 'Acoustic', 'Red Lip', '1989'],
        imagePool: [
          'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?auto=format&fit=crop&w=800&q=80',
          'https://images.unsplash.com/photo-1604537466158-719b1972feb8?auto=format&fit=crop&w=800&q=80'
        ],
        relationships: [{ targetId: 'selena-gomez', type: 'Best Friend' }]
      },
      'selena-gomez': {
        id: 'selena-gomez',
        name: 'Selena Gomez',
        bio: 'Mogul. Rare Beauty.',
        avatarUrl: 'https://images.unsplash.com/photo-1616683693504-3ea7e9ad6fec?auto=format&fit=crop&w=400&q=80',
        aliases: ['selena', 'selena gomez'],
        sources: [
          { platform: 'reddit', id: 'SelenaGomez', label: 'Main', hidden: false },
          { platform: 'instagram', id: 'selenagomez', label: 'Official', hidden: false },
          { platform: 'tiktok', id: 'selenagomez', label: 'Personal', hidden: false }
        ],
        contextKeywords: ['Rare Beauty', 'Cooking', 'OOTD'],
        imagePool: [
          'https://images.unsplash.com/photo-1512310604669-443f26c35f52?auto=format&fit=crop&w=800&q=80',
          'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=800&q=80'
        ],
        relationships: [{ targetId: 'taylor-swift', type: 'Best Friend' }]
      },
      'brooke-monk': {
        id: 'brooke-monk',
        name: 'Brooke Monk',
        bio: 'Content creator and social media personality.',
        avatarUrl: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=400&q=80',
        aliases: ['brooke', 'brooke monk'],
        sources: [
          { platform: 'tiktok', id: 'brookemonk', label: 'Main', hidden: false },
          { platform: 'instagram', id: 'brookemonk', label: 'Official', hidden: false },
          { platform: 'youtube', id: 'BrookeMonk', label: 'YouTube', hidden: false }
        ],
        contextKeywords: ['dance', 'trends', 'viral', 'content'],
        imagePool: [
          'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=800&q=80',
          'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=800&q=80'
        ],
        relationships: []
      },
      'miss-katie': {
        id: 'miss-katie',
        name: 'Miss Katie',
        bio: 'Lifestyle and fashion content creator.',
        avatarUrl: 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=400&q=80',
        aliases: ['katie', 'miss katie'],
        sources: [
          { platform: 'instagram', id: 'misskatie', label: 'Main', hidden: false },
          { platform: 'tiktok', id: 'misskatie', label: 'TikTok', hidden: false },
          { platform: 'youtube', id: 'MissKatie', label: 'YouTube', hidden: false }
        ],
        contextKeywords: ['fashion', 'lifestyle', 'ootd', 'beauty'],
        imagePool: [
          'https://images.unsplash.com/photo-1469334031218-e382a71b716b?auto=format&fit=crop&w=800&q=80',
          'https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=800&q=80'
        ],
        relationships: []
      },
      'fasffy': {
        id: 'fasffy',
        name: 'Fasffy',
        bio: 'Digital content creator and influencer.',
        avatarUrl: 'https://images.unsplash.com/photo-1514315384763-ba401779410f?auto=format&fit=crop&w=400&q=80',
        aliases: ['fasffy', 'fas'],
        sources: [
          { platform: 'tiktok', id: 'fasffy', label: 'Main', hidden: false },
          { platform: 'instagram', id: 'fasffy', label: 'Official', hidden: false },
          { platform: 'twitter', id: 'fasffy', label: 'Twitter', hidden: false }
        ],
        contextKeywords: ['digital', 'creator', 'influencer', 'content'],
        imagePool: [
          'https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?auto=format&fit=crop&w=800&q=80',
          'https://images.unsplash.com/photo-1499951360442-b19be8fe80f5?auto=format&fit=crop&w=800&q=80'
        ],
        relationships: []
      },
      'sjokz': {
        id: 'sjokz',
        name: 'Sjokz',
        bio: 'Esports host and content creator.',
        avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80',
        aliases: ['sjokz', 'esports', 'host'],
        sources: [
          { platform: 'youtube', id: 'Sjokz', label: 'Main', hidden: false },
          { platform: 'web', id: 'sjokz', label: 'Twitch', hidden: false },
          { platform: 'twitter', id: 'Sjokz', label: 'Twitter', hidden: false }
        ],
        contextKeywords: ['esports', 'hosting', 'gaming', 'interviews'],
        imagePool: [
          'https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=800&q=80',
          'https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=800&q=80'
        ],
        relationships: []
      }
    };
  }

  // ============================================================================
  // BOARDS
  // ============================================================================

  private getDemoBoards(): Board[] {
    return [
      {
        id: 'board-pop-queenz',
        name: 'Pop Queenz ✨',
        description: 'Taylor Swift and Selena Gomez content',
        viewMode: 'visual',
        articleIds: [],
        filters: {
          persons: ['Taylor Swift', 'Selena Gomez'],
          sources: [],
          tags: [],
          searchQuery: ''
        },
        createdAt: new Date('2024-01-01').toISOString()
      },
      {
        id: 'board-linux-threads',
        name: 'Linux Threads 🐧',
        description: 'Linux rice and desktop customization',
        viewMode: 'visual',
        articleIds: [],
        filters: {
          persons: [],
          sources: ['r/unixporn', 'r/kde', 'r/battlestations'],
          tags: ['linux', 'rice', 'desktop'],
          searchQuery: ''
        },
        createdAt: new Date('2024-01-01').toISOString()
      },
      {
        id: 'board-reader-inbox',
        name: 'Reader Inbox 📚',
        description: 'Long-form articles and analysis',
        viewMode: 'reader',
        articleIds: [],
        filters: {
          persons: [],
          sources: ['r/linux', 'Newsletter', 'Blog'],
          tags: ['analysis', 'deep-dive', 'tutorial'],
          searchQuery: ''
        },
        createdAt: new Date('2024-01-01').toISOString()
      },
      {
        id: 'board-marketplace',
        name: 'Marketplace 💰',
        description: 'Items for sale and trade',
        viewMode: 'visual',
        articleIds: [],
        filters: {
          persons: [],
          sources: ['r/mechmarket', 'eBay', 'Grailed'],
          tags: ['for sale', 'trade', 'marketplace'],
          searchQuery: ''
        },
        createdAt: new Date('2024-01-01').toISOString()
      }
    ];
  }

  // ============================================================================
  // PUBLIC API
  // ============================================================================

  get identities(): Record<string, IdentityProfile> {
    return Object.fromEntries(this.identityCache.entries());
  }

  /**
   * Get identity by slug (standardized lookup)
   */
  getIdentityBySlug(slug: string): IdentityProfile | null {
    return this.identityCache.get(slug) || null;
  }

  /**
   * Search identities by name or alias (fuzzy matching)
   */
  searchIdentities(query: string): IdentityProfile[] {
    const lowerQuery = query.toLowerCase();
    const results: IdentityProfile[] = [];
    
    this.identityCache.forEach((profile) => {
      const nameMatch = profile.name.toLowerCase().includes(lowerQuery);
      const aliasMatch = profile.aliases.some(alias =>
        alias.toLowerCase().includes(lowerQuery)
      );
      
      if (nameMatch || aliasMatch) {
        results.push(profile);
      }
    });
    
    return results;
  }

  /**
   * Validate identity slug (frontend validation at scale)
   */
  isValidIdentitySlug(slug: string): boolean {
    return this.identityCache.has(slug);
  }

  set identities(value: Record<string, IdentityProfile>) {
    Object.entries(value).forEach(([id, profile]) => {
      this.identityCache.set(id, profile);
    });
  }

  get boards(): Board[] {
    return Array.from(this.boardCache.values());
  }

  set boards(value: Board[]) {
    value.forEach(board => {
      this.boardCache.set(board.id, board);
    });
  }

  /**
   * Get all content
   */
  getAllContent(): UnifiedContent[] {
    return this.contentCache.get('all') || [];
  }

  /**
   * Get content filtered by board
   */
  getContentForBoard(boardId: string): UnifiedContent[] {
    const board = this.boardCache.get(boardId);
    if (!board) return [];

    const allContent = this.getAllContent();
    const { persons, sources, tags, searchQuery } = board.filters;

    return allContent.filter(item => {
      // Filter by persons
      if (persons.length > 0) {
        const personMatch = persons.some(p => 
          item.author.name.toLowerCase().includes(p.toLowerCase()) ||
          item.tags.some(t => t.toLowerCase().includes(p.toLowerCase()))
        );
        if (!personMatch) return false;
      }

      // Filter by sources
      if (sources.length > 0) {
        const sourceMatch = sources.some(s => 
          item.source.toLowerCase().includes(s.toLowerCase().replace('r/', ''))
        );
        if (!sourceMatch) return false;
      }

      // Filter by tags
      if (tags.length > 0) {
        const tagMatch = tags.some(t => 
          item.tags.some(itemTag => itemTag.toLowerCase().includes(t.toLowerCase()))
        );
        if (!tagMatch) return false;
      }

      // Filter by search query
      if (searchQuery) {
        const searchLower = searchQuery.toLowerCase();
        const searchMatch = 
          item.title.toLowerCase().includes(searchLower) ||
          item.tags.some(t => t.toLowerCase().includes(searchLower));
        if (!searchMatch) return false;
      }

      return true;
    });
  }

  /**
   * Get content by view mode
   */
  getContentByViewMode(viewMode: ViewMode): UnifiedContent[] {
    const allContent = this.getAllContent();

    switch (viewMode) {
      case 'visual':
        return allContent.filter(item => item.mediaUrl && item.type !== MediaTypeEnum.TEXT);
      case 'reader':
      case 'inbox':
        return allContent.filter(item => item.content && !item.read);
      case 'archive':
        return allContent.filter(item => item.archived);
      default:
        return allContent;
    }
  }

  /**
   * Get article by ID (for reader view)
   */
  getArticleById(id: string): UnifiedContent | null {
    const allContent = this.getAllContent();
    return allContent.find(item => item.id === id) || null;
  }

  /**
   * Mark article as read
   */
  markAsRead(id: string): void {
    const allContent = this.getAllContent();
    const item = allContent.find(i => i.id === id);
    if (item) {
      item.read = true;
      this.contentCache.set('all', allContent);
    }
  }

  /**
   * Toggle save status
   */
  toggleSave(id: string): void {
    const allContent = this.getAllContent();
    const item = allContent.find(i => i.id === id);
    if (item) {
      item.saved = !item.saved;
      this.contentCache.set('all', allContent);
    }
  }

  /**
   * Create new board
   */
  createBoard(name: string, filters: Board['filters'], viewMode: ViewMode): Board {
    const board: Board = {
      id: `board-${Date.now()}`,
      name,
      filters,
      viewMode,
      articleIds: [],
      createdAt: new Date().toISOString()
    };
    this.boardCache.set(board.id, board);
    return board;
  }

  /**
   * Delete board
   */
  deleteBoard(boardId: string): void {
    this.boardCache.delete(boardId);
  }

  /**
   * Update board
   */
  updateBoard(boardId: string, updates: Partial<Board>): void {
    const board = this.boardCache.get(boardId);
    if (board) {
      const updated = { ...board, ...updates };
      this.boardCache.set(boardId, updated);
    }
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

export const mockDataFactory = MockDataFactory.getInstance();

// Convenience exports
export const getAllContent = () => mockDataFactory.getAllContent();
export const getContentForBoard = (boardId: string) => mockDataFactory.getContentForBoard(boardId);
export const getContentByViewMode = (viewMode: ViewMode) => mockDataFactory.getContentByViewMode(viewMode);
export const getArticleById = (id: string) => mockDataFactory.getArticleById(id);
export const markAsRead = (id: string) => mockDataFactory.markAsRead(id);
export const toggleSave = (id: string) => mockDataFactory.toggleSave(id);
export const getBoards = () => mockDataFactory.boards;
export const createBoard = (name: string, filters: Board['filters'], viewMode: ViewMode) => 
  mockDataFactory.createBoard(name, filters, viewMode);
export const deleteBoard = (boardId: string) => mockDataFactory.deleteBoard(boardId);
export const updateBoard = (boardId: string, updates: Partial<Board>) => 
  mockDataFactory.updateBoard(boardId, updates);
export const getIdentities = () => mockDataFactory.identities;
export const getIdentityBySlug = (slug: string) => mockDataFactory.getIdentityBySlug(slug);
export const searchIdentities = (query: string) => mockDataFactory.searchIdentities(query);
export const isValidIdentitySlug = (slug: string) => mockDataFactory.isValidIdentitySlug(slug);

// Types are already exported above (Article, Board, SauceResult, UnifiedContent, ViewMode)
// Re-export types from bunny/types for convenience
export type { PlatformType } from '../bunny/types';
