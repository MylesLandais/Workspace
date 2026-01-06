import { FeedItem, MediaType } from "../types/feed";
import { decodeHtmlEntities } from "@/lib/utils";

interface ParquetThread {
  board: string;
  thread_id: string;
  url: string;
  title: string;
  post_count: string;
  image_count: string;
  html_path: string;
  html_filename: string;
  file_size: string;
  file_modified: string;
  cached_at: string;
}

interface ParquetImage {
  sha256: string;
  local_path: string;
  relative_path: string;
  filename: string;
  file_size: string;
  file_modified: string;
  cached_at: string;
}

interface ParquetCache {
  metadata: {
    generatedAt: string;
    totalThreads: number;
    totalImages: number;
    source: string;
  };
  threads: ParquetThread[];
  images: ParquetImage[];
  threadImageMapping: Record<string, ParquetImage[]>;
}

let cachedData: ParquetCache | null = null;

// Load the JSON cache file
async function loadParquetCache(): Promise<ParquetCache | null> {
  if (cachedData) return cachedData;

  try {
    const baseUrl = process.env.VERCEL_URL 
      ? `https://${process.env.VERCEL_URL}` 
      : 'http://localhost:3000';
    const response = await fetch(`${baseUrl}/parquet-cache/feed-data.json`);
    if (!response.ok) {
      throw new Error(`Failed to load parquet cache: ${response.status}`);
    }
    
    cachedData = await response.json();
    console.log(`Loaded parquet cache: ${cachedData.metadata.totalThreads} threads, ${cachedData.metadata.totalImages} images`);
    return cachedData;
  } catch (error) {
    console.error('Error loading parquet cache:', error);
    return null;
  }
}

function decodeHtmlEntities(text: string): string {
  const entityMap: Record<string, string> = {
    '&amp;': '&',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"',
    '&#39;': "'",
    '&apos;': "'"
  };
  
  return text.replace(/&[a-zA-Z0-9#]+;/g, (match) => entityMap[match] || match);
}

export async function generateParquetFeed(): Promise<FeedItem[]> {
  console.log('generateParquetFeed() called');
  
  const cacheData = await loadParquetCache();
  
  if (!cacheData) {
    console.warn('No parquet cache data available');
    return [];
  }

  console.log(`Creating parquet feed from ${cacheData.threads.length} threads`);
  const feedItems: FeedItem[] = [];

  for (const thread of cacheData.threads.slice(0, 20)) { // Limit to 20 threads for performance
    const threadId = thread.thread_id;
    const images = cacheData.threadImageMapping[threadId] || [];
    
    // Use the first image as the thumbnail if available
    const firstImage = images.length > 0 ? images[0] : null;
    const thumbnailUrl = firstImage 
      ? `/imageboard/b/${threadId}/${firstImage.filename}` 
      : `https://picsum.photos/seed/parquet-${threadId}/800/600`;

    const title = decodeHtmlEntities(thread.title || "Untitled Thread");
    
    // Truncate long titles
    const truncatedTitle = title.length > 100 
      ? title.substring(0, 97) + '...' 
      : title;

    const feedItem: FeedItem = {
      id: `parquet-${threadId}`,
      type: MediaType.IMAGE,
      caption: truncatedTitle,
      author: {
        name: "Anonymous",
        handle: `@anon_${threadId.slice(-6)}`,
      },
      source: "Parquet Archive",
      timestamp: new Date(thread.cached_at).toISOString(),
      aspectRatio: "aspect-[4/3]",
      width: 800,
      height: 600,
      likes: Math.floor(Math.random() * 5000) + 500,
      mediaUrl: thumbnailUrl,
      tags: [thread.board, `${images.length} images`, "archived"],
      galleryUrls: images.map(img => `/imageboard/b/${threadId}/${img.filename}`),
      replyCount: Number(thread.post_count) - 1, // Subtract 1 for OP
      imageCount: images.length,
    };

    feedItems.push(feedItem);
  }

  const sortedItems = feedItems.sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
  
  console.log(`Generated ${sortedItems.length} parquet feed items`);
  return sortedItems;
}

export async function getParquetGallery(threadId: string): Promise<{
  id: string;
  threadId: string;
  title: string;
  images: string[];
  thumbnail: string;
} | null> {
  const cacheData = await loadParquetCache();
  
  if (!cacheData) return null;
  
  const thread = cacheData.threads.find(t => t.thread_id === threadId);
  
  if (!thread) return null;

  const images = cacheData.threadImageMapping[threadId] || [];
  const imageUrls = images.map(img => `/imageboard/b/${threadId}/${img.filename}`);

  return {
    id: `parquet-gallery-${threadId}`,
    threadId,
    title: decodeHtmlEntities(thread.title || "Untitled Thread"),
    images: imageUrls,
    thumbnail: imageUrls[0] || "",
  };
}