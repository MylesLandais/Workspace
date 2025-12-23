import { Article, FeedSource, Board } from '../types';

export const MOCK_FEEDS: FeedSource[] = [
  { id: '1', name: 'TechCrunch', type: 'rss', unreadCount: 2 },
  { id: '2', name: '@paulg', type: 'twitter', unreadCount: 1 },
  { id: '3', name: 'Stratechery', type: 'newsletter', unreadCount: 1 },
  { id: '4', name: 'Veritasium', type: 'youtube', unreadCount: 0 },
  { id: '5', name: 'r/LocalLLaMA', type: 'reddit', unreadCount: 3 },
  { id: '6', name: 'Danbooru: Top', type: 'booru', unreadCount: 12 },
  { id: '7', name: 'Kemono: ArtistX', type: 'monitor', unreadCount: 4 },
];

export const MOCK_BOARDS: Board[] = [
  { id: 'b1', name: 'UI Inspiration', articleIds: [] },
  { id: 'b2', name: 'Character Design', articleIds: [] },
];

export const MOCK_ARTICLES: Article[] = [
  {
    id: 'a1',
    sourceId: '1',
    type: 'rss',
    title: 'The Future of AI Agents in Production',
    author: 'Alex Wilhelm',
    publishedAt: '2024-05-20T10:30:00Z',
    url: '#',
    read: false,
    saved: false,
    archived: false,
    tags: ['AI', 'Startups', 'Infrastructure'],
    content: `<p>As large language models (LLMs) continue to evolve...</p>`
  },
  {
    id: 'a5',
    sourceId: '5',
    type: 'reddit',
    title: 'Llama-3 70B is essentially GPT-4 class for local inference',
    author: 'u/LocalLLM_Enjoyer',
    publishedAt: '2024-05-22T09:30:00Z',
    url: '#',
    read: false,
    saved: true,
    archived: false,
    tags: ['AI', 'Local', 'Open Source'],
    content: `<div class="reddit-post"><p>I've been running the quantized versions...</p></div>`
  },
  {
    id: 'a6',
    sourceId: '6',
    type: 'booru',
    title: 'Rem (Re:Zero) - Digital Art',
    author: 'wlop',
    publishedAt: '2024-05-23T14:20:00Z',
    url: '#',
    read: false,
    saved: false,
    archived: false,
    tags: ['rem_(re:zero)', 'width:1920', 'height:1080', 'blue_hair', 'maid'],
    imageUrl: 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800&q=80',
    imageWidth: 1920,
    imageHeight: 1080,
    content: `<img src="https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800&q=80" />`
  },
  {
    id: 'a7',
    sourceId: '6',
    type: 'booru',
    title: 'Cyberpunk Cityscape',
    author: 'unknown',
    publishedAt: '2024-05-23T12:00:00Z',
    url: '#',
    read: false,
    saved: false,
    archived: false,
    tags: ['scenery', 'cyberpunk', 'neon', 'width:1080', 'height:2400', 'mobile_wallpaper'],
    imageUrl: 'https://images.unsplash.com/photo-1515630278258-407f66498911?w=600&q=80',
    imageWidth: 1080,
    imageHeight: 2400,
    content: `<img src="https://images.unsplash.com/photo-1515630278258-407f66498911?w=600&q=80" />`
  },
  {
    id: 'a8',
    sourceId: '7',
    type: 'monitor',
    title: 'New Sketch Dump (May 2024)',
    author: 'ArtistX (Fanbox)',
    publishedAt: '2024-05-21T18:00:00Z',
    url: '#',
    read: false,
    saved: false,
    archived: false,
    tags: ['sketch', 'wip', 'character_study'],
    imageUrl: 'https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=600&q=80',
    imageWidth: 1200,
    imageHeight: 1600,
    content: `<p>Here are some sketches from this week!</p><img src="https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=600&q=80" />`
  }
];