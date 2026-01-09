"use client";

import { useState, useEffect, useMemo } from "react";
import { FeedItem, MediaType } from "@/lib/types/feed";
import { MasonryGrid, MediaLightbox, FeedHeader, FeedLoading } from "@/components/feed";
import { useLightboxStore } from "@/lib/store/lightbox-store";
import { useSearchStore } from "@/lib/store/search-store";
import { useSession } from "@/lib/auth-client";
import { RedditPostDetails } from "@/lib/types/reddit";

const GET_FEED = `
  query Feed($limit: Int, $filters: FeedFilters) {
    feed(limit: $limit, filters: $filters) {
      edges {
        node {
          id
          title
          sourceUrl
          publishDate
          imageUrl
          mediaType
          platform
          score
          width
          height
          handle {
            name
            handle
          }
          subreddit {
            name
          }
          author {
            username
          }
        }
      }
    }
  }
`;

const ASPECT_RATIOS = [
  { ratio: "aspect-[3/4]", width: 600, height: 800 },
  { ratio: "aspect-[4/3]", width: 800, height: 600 },
  { ratio: "aspect-[16/9]", width: 800, height: 450 },
  { ratio: "aspect-[1/1]", width: 600, height: 600 },
  { ratio: "aspect-[9/16]", width: 450, height: 800 },
];

const SOURCES = ["Reddit", "Pinterest", "Twitter", "Instagram", "TikTok", "Imageboard"];
const CAPTIONS = ["Morning vibes in the city", "Found this gem while exploring", "Nature at its finest", "Throwback to better days", "Living my best life", "Sunset chaser", "Coffee and contemplation", "Weekend wanderings", "Art imitates life", "Quiet moments"];
const AUTHORS = [{ name: "Alex Chen", handle: "@alexc" }, { name: "Jordan Smith", handle: "@jsmith" }, { name: "Sam Rivera", handle: "@samr" }, { name: "Taylor Kim", handle: "@tkim" }, { name: "Morgan Lee", handle: "@mlee" }];

function seededRandom(seed: number): () => number {
  return function () {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
}

function generateFeedItem(index: number, sourceOverride?: string, mediaUrl?: string): FeedItem {
  const random = seededRandom(index * 1337);
  const aspectData = ASPECT_RATIOS[Math.floor(random() * ASPECT_RATIOS.length)];
  const author = AUTHORS[Math.floor(random() * AUTHORS.length)];
  const source = sourceOverride || SOURCES[Math.floor(random() * SOURCES.length)];
  const caption = CAPTIONS[Math.floor(random() * CAPTIONS.length)];
  const date = new Date();
  date.setHours(date.getHours() - Math.floor(random() * 168));
  const type = random() > 0.7 ? MediaType.VIDEO : MediaType.IMAGE;
  const finalMediaUrl = mediaUrl || `https://picsum.photos/seed/${index}/${aspectData.width}/${aspectData.height}`;

  const redditData = source === "Reddit" ? {
    id: `reddit-${index}`, title: caption, created_utc: date.toISOString(),
    score: Math.floor(random() * 50000), num_comments: Math.floor(random() * 1000),
    upvote_ratio: 0.8 + random() * 0.2, over_18: random() > 0.9, url: finalMediaUrl,
    selftext: random() > 0.5 ? "This is a mock selftext for testing." : "",
    permalink: `/r/${source.toLowerCase()}/comments/${index}`, subreddit: "artwork",
    author: author.handle.replace('@', ''), is_image: type === MediaType.IMAGE,
    image_url: type === MediaType.IMAGE ? finalMediaUrl : null,
  } : undefined;

  return {
    id: `${source.toLowerCase()}-${index}`,
    type,
    caption,
    author,
    source,
    timestamp: date.toISOString(),
    aspectRatio: aspectData.ratio,
    width: aspectData.width,
    height: aspectData.height,
    likes: Math.floor(random() * 50000),
    mediaUrl: finalMediaUrl,
    redditData,
  };
}

interface ImageboardThreadData {
  threadId: string;
  firstImage: string;
  imageCount: number;
  hashes: string[];
  title: string;
}

async function loadImageboardThreads(): Promise<ImageboardThreadData[]> {
  console.log('Feed page loadImageboardThreads: Fetching from parquet cache...');
  try {
    const response = await fetch('/parquet-cache/feed-data.json');
    if (!response.ok) {
      console.error('Failed to fetch parquet cache:', response.status);
      return [];
    }
    
    const data = await response.json();
    console.log(`Feed page loadImageboardThreads: Loaded ${data.threads.length} threads from cache`);
    
    const result = data.threads.map((thread: any) => {
      const images = data.threadImageMapping[thread.thread_id] || [];
      const hashes = images.map((img: any) => img.filename.replace(/\.(jpg|png|webp)$/, ''));
      
      return {
        threadId: thread.thread_id,
        firstImage: images.length > 0 ? `/imageboard/b/${thread.thread_id}/${images[0].filename}` : null,
        imageCount: images.length,
        hashes,
        title: thread.title || `Thread ${thread.thread_id}`
      };
    }).filter((t: ImageboardThreadData & { firstImage: string }) => t.firstImage !== null);
    
    console.log(`Feed page loadImageboardThreads: Returning ${result.length} threads with images`);
    return result;
  } catch (error) {
    console.error('Failed to load imageboard threads:', error);
    return [];
  }
}

function generateInitialItems(): FeedItem[] {
  return [];
}

export default function FeedPage() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { filters } = useSearchStore();
  const lightboxStore = useLightboxStore();
  const { data: session } = useSession();

  useEffect(() => {
    async function loadFeed() {
      setIsLoading(true);
      console.log('loadFeed: Starting...');
      
      try {
        if (session) {
          console.log('loadFeed: Fetching from GraphQL API...');
          const response = await fetch('http://localhost:4002/api/graphql', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              query: GET_FEED,
              variables: {
                limit: 20,
                filters: {
                  sources: [], // Fetch all sources
                  persons: [],
                  tags: [],
                  searchQuery: ""
                }
              }
            }),
          });

          const result = await response.json();
          
          if (result.data?.feed?.edges) {
            const apiItems = result.data.feed.edges.map((edge: any) => {
              const node = edge.node;
              return {
                id: node.id,
                type: node.mediaType === 'VIDEO' ? MediaType.VIDEO : MediaType.IMAGE,
                caption: node.title,
                author: { 
                  name: node.handle.name, 
                  handle: node.handle.handle 
                },
                source: node.platform === 'REDDIT' ? 'Reddit' : 
                        node.platform === 'IMAGEBOARD' ? 'Imageboard' : 
                        node.platform.charAt(0) + node.platform.slice(1).toLowerCase(),
                timestamp: node.publishDate,
                aspectRatio: node.width && node.height ? `aspect-[${node.width}/${node.height}]` : "aspect-[3/4]",
                width: node.width || 600,
                height: node.height || 800,
                likes: node.score || 0,
                mediaUrl: node.imageUrl,
                redditData: node.platform === 'REDDIT' ? {
                  id: node.id,
                  title: node.title,
                  author: node.author?.username || node.handle.handle,
                  subreddit: node.subreddit?.name || '',
                  score: node.score,
                  num_comments: 0, 
                  created_utc: node.publishDate,
                  url: node.sourceUrl,
                  is_image: node.mediaType === 'IMAGE',
                  image_url: node.imageUrl
                } : undefined
              };
            });
            
            console.log(`loadFeed: Loaded ${apiItems.length} items from API`);
            setItems(apiItems);
            setIsLoading(false);
            return;
          }
        }

        console.log('loadFeed: Fetching parquet cache...');
        const threadData = await loadImageboardThreads();
        console.log(`loadFeed: Got ${threadData.length} threads`);
        
        if (threadData.length === 0) {
          console.warn('loadFeed: No threads loaded, using fallback');
        }
        
        const feedItems: FeedItem[] = [];
        
        for (const thread of threadData) {
          const random = seededRandom(parseInt(thread.threadId) * 999);
          const aspectData = ASPECT_RATIOS[Math.floor(random() * ASPECT_RATIOS.length)];
          const date = new Date();
          date.setHours(date.getHours() - Math.floor(random() * 168));
          
          feedItems.push({
            id: `imageboard-${thread.threadId}`,
            type: MediaType.IMAGE,
            caption: thread.title,
            author: { name: "Anonymous", handle: `@anon_${thread.threadId.slice(-4)}` },
            source: "Imageboard",
            timestamp: date.toISOString(),
            aspectRatio: aspectData.ratio,
            width: aspectData.width,
            height: aspectData.height,
            likes: Math.floor(random() * 5000) + 500,
            mediaUrl: thread.firstImage,
            tags: ["b", "gallery", "thread"],
            galleryUrls: thread.hashes.map(h => `/imageboard/b/${thread.threadId}/${h}.jpg`),
            replyCount: Math.floor(random() * 400) + 50,
            imageCount: thread.imageCount,
          });
        }
        
        for (let i = 0; i < 15; i++) {
          feedItems.push(generateFeedItem(i + 100));
        }
        
        setItems(feedItems);
        setIsLoading(false);
      } catch (error) {
        console.error('loadFeed: Error:', error);
        setIsLoading(false);
      }
    }
    
    loadFeed();
  }, []);

  const handleItemClick = (item: FeedItem) => {
    const itemIndex = items.findIndex((i) => i.id === item.id);
    if (itemIndex >= 0) {
      let slideIndex = 0;
      for (let i = 0; i < itemIndex; i++) {
        const galleryUrls = items[i].galleryUrls;
        slideIndex += galleryUrls && galleryUrls.length > 1 ? galleryUrls.length : 1;
      }
      lightboxStore.openLightbox(items, slideIndex);
      if (item.redditData) {
        lightboxStore.setLoadingThread(item.redditData.id, true);
        setTimeout(() => {
          const details: RedditPostDetails = { post: item.redditData, comments: [], images: [] };
          lightboxStore.setRedditThreadData(item.redditData!.id, details);
          lightboxStore.setLoadingThread(item.redditData!.id, false);
        }, 500);
      }
    }
  };

  const sourceInfo = useMemo(() => {
    const sourceCounts = items.reduce((acc, item) => {
      acc[item.source] = (acc[item.source] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    return Object.entries(sourceCounts).map(([s, c]) => `${s}:${c}`).join(', ');
  }, [items]);

  return (
    <main className="min-h-screen bg-app-bg">
      <FeedHeader itemCount={items.length} />
      <div style={{ background: '#1a1a1a', color: '#666', padding: '4px 8px', fontSize: '11px', fontFamily: 'monospace', textAlign: 'center' }}>
        {sourceInfo}
      </div>
      <div className="max-w-[2400px] mx-auto">
        <MasonryGrid items={items} isLoading={isLoading} hasNextPage={false} onLoadMore={() => {}} onItemClick={handleItemClick} />
      </div>
      <MediaLightbox />
    </main>
  );
}
