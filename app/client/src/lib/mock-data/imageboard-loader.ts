import { FeedItem, MediaType } from "@/lib/types/feed";
import { decodeHtmlEntities } from "@/lib/utils";

interface ImageboardThread {
  threadId: string;
  title: string;
  opBody: string;
  board: string;
  imageCount: number;
  replyCount: number;
  imagePaths: string[];
  createdAt: string;
}

function parseHtmlForThreadData(html: string): {
  title: string;
  opBody: string;
} {
  // Extract thread title from page title
  // Format: "/b/ - Title - Random - 4chan"
  const titleMatch = html.match(/<title>\/[a-z]\/ - ([^-]+) -/);
  const title = decodeHtmlEntities(titleMatch ? titleMatch[1].trim() : "4chan Thread");

  // Extract first post body (OP)
  // Look for the first blockquote with postMessage class
  const opMatch = html.match(
    /<blockquote class="postMessage"[^>]*>([^<]*(?:<(?!\/blockquote)[^>]*>[^<]*)*)<\/blockquote>/
  );
  let opBody = opMatch ? opMatch[1].trim() : "";

  // Clean up HTML entities and tags
  opBody = decodeHtmlEntities(opBody)
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .substring(0, 200);

  return { title, opBody };
}

// Thread metadata with known image paths from cache
const THREAD_METADATA: Record<string, { imageFiles: string[] }> = {};

async function loadImageboardThreads(): Promise<ImageboardThread[]> {
  const threadIds = [
    "944334460",
    "944303266",
    "944330306",
    "944342413",
    "944340175",
  ];
  const threads: ImageboardThread[] = [];

  for (const threadId of threadIds) {
    try {
      const response = await fetch(`/imageboard/html/b_${threadId}.html`);
      if (!response.ok) continue;

      const html = await response.text();
      const { title, opBody } = parseHtmlForThreadData(html);

      // Fetch the JSON manifest of images for this thread
      let imagePaths: string[] = [];
      try {
        console.log(`Fetching images for thread ${threadId}...`);
        const filesResponse = await fetch(
          `/api/imageboard-files?thread=${threadId}`
        );
        if (filesResponse.ok) {
          const data = await filesResponse.json();
          imagePaths = data.files || [];
          console.log(
            `✓ Loaded ${imagePaths.length} images from API for thread ${threadId}`
          );
        } else {
          console.warn(
            `API returned ${filesResponse.status} for thread ${threadId}`
          );
        }
      } catch (error) {
        console.warn(
          `Failed to fetch from API for thread ${threadId}:`,
          error
        );
      }

      // If we couldn't load real images, generate placeholder paths
      if (imagePaths.length === 0) {
        // Generate predictable placeholder paths based on thread
        const estimatedCount = parseInt(threadId) % 300 || 100;
        imagePaths = Array.from({ length: estimatedCount }, (_, i) =>
          `/imageboard/b/${threadId}/image_${String(i + 1).padStart(4, "0")}.jpg`
        );
      }

      threads.push({
        threadId,
        title,
        opBody,
        board: "b",
        imageCount: imagePaths.length,
        replyCount: Math.floor(Math.random() * 500) + 100,
        imagePaths,
        createdAt: new Date().toISOString(),
      });

      console.log(
        `Loaded thread ${threadId}: ${imagePaths.length} images, title: "${title}"`
      );
    } catch (error) {
      console.warn(`Failed to load thread ${threadId}:`, error);
    }
  }

  return threads;
}

// Cache for loaded threads
let cachedThreads: ImageboardThread[] | null = null;

export interface ImageboardGallery {
  id: string;
  threadId: string;
  title: string;
  images: string[];
  thumbnail: string;
}

export function transformThreadToFeedItem(
  thread: ImageboardThread
): FeedItem & { galleryUrls: string[] } {
  // Use first actual image if available, otherwise placeholder
  const thumbnailUrl =
    thread.imagePaths.length > 0
      ? thread.imagePaths[0]
      : `https://picsum.photos/seed/imageboard-${thread.threadId}/800/600`;

  return {
    id: `imageboard-${thread.threadId}`,
    type: MediaType.IMAGE,
    caption: thread.title,
    author: {
      name: "Anonymous",
      handle: `@anon_${thread.threadId}`,
    },
    source: "Imageboard",
    timestamp: thread.createdAt,
    aspectRatio: "aspect-[4/3]",
    width: 800,
    height: 600,
    likes: Math.floor(Math.random() * 5000) + 500,
    mediaUrl: thumbnailUrl,
    tags: [thread.board, `${thread.imageCount} images`, "gallery"],
    galleryUrls: thread.imagePaths,
    replyCount: thread.replyCount,
    imageCount: thread.imageCount,
  };
}

export async function generateImageboardFeed(): Promise<FeedItem[]> {
  if (cachedThreads) {
    return cachedThreads.map((thread) => transformThreadToFeedItem(thread));
  }

  try {
    const threads = await loadImageboardThreads();
    cachedThreads = threads;
    return threads.map((thread) => transformThreadToFeedItem(thread));
  } catch (error) {
    console.error("Failed to generate imageboard feed:", error);
    return [];
  }
}

export async function getImageboardGallery(
  threadId: string
): Promise<ImageboardGallery | null> {
  const threads = cachedThreads || (await loadImageboardThreads());
  const thread = threads.find((t) => t.threadId === threadId);
  if (!thread) return null;

  return {
    id: `gallery-${threadId}`,
    threadId: thread.threadId,
    title: thread.title,
    images: thread.imagePaths,
    thumbnail: thread.imagePaths[0] || "",
  };
}
