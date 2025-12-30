import type { TransformedMedia } from '../mock-data/loader';

export interface Media {
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
  platform: 'reddit' | 'youtube' | 'twitter' | 'instagram' | 'tiktok' | 'vsco';
  handle: {
    name: string;
    handle: string;
    creatorName?: string;
  };
  mediaType: 'video' | 'image' | 'text';
  viewCount?: number;
}

/**
 * Extract a unique identifier from an image URL
 * Uses the filename (last path segment) to catch URL variations
 * Example: "https://i.redd.it/abc123.jpg" -> "abc123.jpg"
 */
export function extractImageIdentifier(imageUrl: string): string {
  try {
    const url = new URL(imageUrl);
    const pathParts = url.pathname.split('/').filter(Boolean);
    return pathParts[pathParts.length - 1] || imageUrl;
  } catch {
    // Fallback if URL parsing fails
    const parts = imageUrl.split('/').filter(Boolean);
    return parts[parts.length - 1] || imageUrl;
  }
}

/**
 * Deduplicate media array by image identifier
 * Keeps the first occurrence of each unique image
 */
export function deduplicateMedia(media: Media[]): Media[] {
  const seenIdentifiers = new Map<string, Media>();
  const unique: Media[] = [];

  for (const item of media) {
    if (!item.imageUrl) {
      continue; // Skip items without image URLs
    }

    const imageId = extractImageIdentifier(item.imageUrl);

    if (!seenIdentifiers.has(imageId)) {
      seenIdentifiers.set(imageId, item);
      unique.push(item);
    }
  }

  return unique;
}
