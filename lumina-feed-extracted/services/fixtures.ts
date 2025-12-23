import { IdentityProfile, SavedBoard, FeedItem, MediaType } from '../types';

// --- 1. Test Entities (The "Golden" Dataset) ---

export const DEMO_IDENTITIES: Record<string, IdentityProfile> = {
  'taylor-swift': {
    id: 'taylor-swift',
    name: 'Taylor Swift',
    bio: 'The music industry.',
    avatarUrl: "https://images.unsplash.com/photo-1514525253440-b393452e3383?auto=format&fit=crop&w=400&q=80",
    aliases: ['taylor swift', 'taylor', 'tswift', 'blondie'],
    sources: [
      { platform: 'reddit', id: 'TaylorSwift', label: 'Main', hidden: false },
      { platform: 'instagram', id: 'taylorswift', label: 'Official', hidden: false },
      { platform: 'twitter', id: 'taylorswift13', label: 'News', hidden: false }
    ],
    contextKeywords: ['Eras Tour', 'Acoustic', 'Red Lip', '1989'],
    imagePool: [
       "https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?auto=format&fit=crop&w=800&q=80",
       "https://images.unsplash.com/photo-1604537466158-719b1972feb8?auto=format&fit=crop&w=800&q=80"
    ],
    relationships: [{ targetId: 'selena-gomez', type: 'Best Friend' }]
  },
  'selena-gomez': {
    id: 'selena-gomez',
    name: 'Selena Gomez',
    bio: 'Mogul. Rare Beauty.',
    avatarUrl: "https://images.unsplash.com/photo-1616683693504-3ea7e9ad6fec?auto=format&fit=crop&w=400&q=80",
    aliases: ['selena', 'selena gomez'],
    sources: [
      { platform: 'instagram', id: 'selenagomez', label: 'Official', hidden: false },
      { platform: 'tiktok', id: 'selenagomez', label: 'Personal', hidden: false }
    ],
    contextKeywords: ['Rare Beauty', 'Cooking', 'OOTD'],
    imagePool: [
      "https://images.unsplash.com/photo-1512310604669-443f26c35f52?auto=format&fit=crop&w=800&q=80",
      "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=800&q=80"
    ],
    relationships: [{ targetId: 'taylor-swift', type: 'Best Friend' }]
  }
};

// --- 2. Test Boards (Use Case Scenarios) ---

export const DEMO_BOARDS: SavedBoard[] = [
  {
    id: 'demo-board-linux',
    name: 'Linux Rice 🐧',
    filters: {
      persons: [],
      sources: ['r/unixporn', 'r/hyprland', 'r/kde', 'r/gnome', 'r/UsabilityPorn', 'r/battlestations'],
      searchQuery: ''
    },
    createdAt: 1715000000000
  },
  {
    id: 'demo-board-pop',
    name: 'Queens of Pop ✨',
    filters: {
      persons: ['Taylor Swift', 'Selena Gomez'],
      sources: [],
      searchQuery: ''
    },
    createdAt: 1715000005000
  }
];

// --- 3. Mock Feed Items (Offline/Demo Content) ---

export const DEMO_FEED_ITEMS: FeedItem[] = [
  // Scenario: Linux Rice / Unixporn
  {
    id: 'mock-linux-1',
    type: MediaType.IMAGE,
    caption: '[Hyprland] My first rice! Catppuccin theme + Waybar',
    author: { name: 'linux_wizard', handle: 'u/linux_wizard' },
    source: 'r/unixporn',
    timestamp: new Date().toISOString(),
    aspectRatio: 'aspect-video',
    width: 1920,
    height: 1080,
    likes: 4520,
    mediaUrl: 'https://images.unsplash.com/photo-1550439062-609e1531270e?auto=format&fit=crop&w=1200&q=80' // Matrix/Code aesthetic
  },
  {
    id: 'mock-linux-2',
    type: MediaType.IMAGE,
    caption: 'KDE Plasma 6 is looking buttery smooth on Arch',
    author: { name: 'arch_user_btw', handle: 'u/arch_user_btw' },
    source: 'r/kde',
    timestamp: new Date().toISOString(),
    aspectRatio: 'aspect-video',
    width: 1920,
    height: 1080,
    likes: 1200,
    mediaUrl: 'https://images.unsplash.com/photo-1629654297299-c8506221ca97?auto=format&fit=crop&w=1200&q=80' // Clean dark desktop setup
  },
  {
    id: 'mock-linux-3',
    type: MediaType.IMAGE,
    caption: 'Minimalist Battlestation - Night Mode',
    author: { name: 'desk_setup', handle: 'u/desk_setup' },
    source: 'r/battlestations',
    timestamp: new Date().toISOString(),
    aspectRatio: 'aspect-[3/4]',
    width: 1000,
    height: 1333,
    likes: 8900,
    mediaUrl: 'https://images.unsplash.com/photo-1593640408182-31c70c8268f5?auto=format&fit=crop&w=800&q=80' // RGB PC Setup
  },
  
  // Scenario: Taylor Swift
  {
    id: 'mock-ts-1',
    type: MediaType.IMAGE,
    caption: 'Surprise song from last night in Tokyo! 🎸',
    author: { name: 'TaylorSwift', handle: 'u/TaylorSwift' },
    source: 'r/TaylorSwift',
    timestamp: new Date().toISOString(),
    aspectRatio: 'aspect-[3/4]',
    width: 800,
    height: 1200,
    likes: 15000,
    mediaUrl: 'https://images.unsplash.com/photo-1493225255756-d9584f8606e9?auto=format&fit=crop&w=800&q=80' // Concert vibe
  },
  {
    id: 'mock-ts-2',
    type: MediaType.SHORT,
    caption: 'Backstage clips #ErasTour',
    author: { name: 'taylorswift', handle: '@taylorswift' },
    source: 'Instagram',
    timestamp: new Date().toISOString(),
    aspectRatio: 'aspect-[3/4]',
    width: 1080,
    height: 1920,
    likes: 250000,
    mediaUrl: 'https://images.unsplash.com/photo-1516280440614-6697288d5d38?auto=format&fit=crop&w=800&q=80' // Sparkly outfit
  },

  // Scenario: Selena Gomez
  {
    id: 'mock-sg-1',
    type: MediaType.IMAGE,
    caption: 'New Rare Beauty blush launch event 🌸',
    author: { name: 'selenagomez', handle: '@selenagomez' },
    source: 'Instagram',
    timestamp: new Date().toISOString(),
    aspectRatio: 'aspect-square',
    width: 1080,
    height: 1080,
    likes: 980000,
    mediaUrl: 'https://images.unsplash.com/photo-1512310604669-443f26c35f52?auto=format&fit=crop&w=800&q=80' // Makeup/Fashion
  }
];

export const getDemoItemsForFilters = (
  searchQuery: string,
  persons: string[],
  sources: string[]
): FeedItem[] => {
  const queryLower = searchQuery.toLowerCase();
  
  return DEMO_FEED_ITEMS.filter(item => {
    // 1. Check Source match
    const sourceMatch = sources.length === 0 || sources.some(s => {
      // Very loose matching for demo purposes
      return item.source.toLowerCase().includes(s.toLowerCase().replace('r/', ''));
    });
    
    // 2. Check Person match (via author or caption)
    const personMatch = persons.length === 0 || persons.some(p => {
      return item.author.name.toLowerCase().includes(p.toLowerCase().replace(' ', '')) || 
             item.caption.toLowerCase().includes(p.toLowerCase());
    });

    // 3. Check Search query
    const searchMatch = queryLower === '' || 
                        item.caption.toLowerCase().includes(queryLower) ||
                        item.source.toLowerCase().includes(queryLower);

    return sourceMatch && personMatch && searchMatch;
  });
};