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
  const title = decodeHtmlEntities(
    titleMatch ? titleMatch[1].trim() : "4chan Thread",
  );

  // Extract first post body (OP)
  // Look for the first blockquote with postMessage class
  const opMatch = html.match(
    /<blockquote class="postMessage"[^>]*>([^<]*(?:<(?!\/blockquote)[^>]*>[^<]*)*)<\/blockquote>/,
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

  console.log(
    `loadImageboardThreads: Starting with ${threadIds.length} thread IDs`,
  );

  for (const threadId of threadIds) {
    try {
      console.log(`Processing thread ${threadId}...`);

      const baseUrl = process.env.VERCEL_URL
        ? `https://${process.env.VERCEL_URL}`
        : "http://localhost:3000";

      // Fetch both HTML and files data in parallel
      const [htmlResponse, filesResponse] = await Promise.all([
        fetch(`${baseUrl}/imageboard/html/b_${threadId}.html`),
        fetch(`${baseUrl}/api/imageboard-files?thread=${threadId}`),
      ]);

      if (!htmlResponse.ok) {
        console.warn(
          `HTML not OK for thread ${threadId}: ${htmlResponse.status}`,
        );
        continue;
      }

      const html = await htmlResponse.text();
      const { title, opBody } = parseHtmlForThreadData(html);

      // Get image paths from files API
      let imagePaths: string[] = [];
      if (filesResponse.ok) {
        const filesData = await filesResponse.json();
        imagePaths = filesData.files || [];
      }

      // If no images from API, generate placeholders
      if (imagePaths.length === 0) {
        const estimatedCount = (parseInt(threadId) % 200) + 50;
        imagePaths = Array.from(
          { length: estimatedCount },
          (_, i) =>
            `/imageboard/b/${threadId}/image_${String(i + 1).padStart(4, "0")}.jpg`,
        );
      }

      const threadData: ImageboardThread = {
        threadId,
        title,
        opBody,
        board: "b",
        imageCount: imagePaths.length,
        replyCount: Math.floor(Math.random() * 400) + 50,
        imagePaths,
        createdAt: new Date().toISOString(),
      };

      threads.push(threadData);
      console.log(
        `[SUCCESS] Thread ${threadId}: "${title}" (${imagePaths.length} images)`,
      );
    } catch (error) {
      console.error(`[ERROR] Error with thread ${threadId}:`, error);
      // Continue processing other threads even if one fails
    }
  }

  console.log(`loadImageboardThreads: Returning ${threads.length} threads`);
  return threads;
}

// Cache for loaded threads
let cachedThreads: ImageboardThread[] | null = null;

// Export loadImageboardThreads for testing
export { loadImageboardThreads };

// Clear cache for development
export function clearImageboardCache() {
  console.log("clearImageboardCache: Clearing cache");
  cachedThreads = null;
}

export interface ImageboardGallery {
  id: string;
  threadId: string;
  title: string;
  images: string[];
  thumbnail: string;
}

export function transformThreadToFeedItem(
  thread: ImageboardThread,
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
  console.log("generateImageboardFeed() called");

  // IMPROVED: Only cache if we have valid data
  if (cachedThreads && cachedThreads.length > 0) {
    console.log(`Returning ${cachedThreads.length} cached imageboard threads`);
    return cachedThreads.map((thread) => transformThreadToFeedItem(thread));
  }

  try {
    console.log("Loading imageboard threads...");
    const threads = await loadImageboardThreads();

    if (threads.length === 0) {
      console.warn("No threads loaded, returning empty array");
      return [];
    }

    console.log(`Loaded ${threads.length} imageboard threads`);
    cachedThreads = threads;

    const feedItems = threads
      .map((thread) => {
        try {
          return transformThreadToFeedItem(thread);
        } catch (transformError) {
          console.error(
            `Error transforming thread ${thread.threadId}:`,
            transformError,
          );
          return null;
        }
      })
      .filter(
        (item): item is FeedItem & { galleryUrls: string[] } =>
          item !== null && typeof item.galleryUrls === "string",
      ) as FeedItem[];

    console.log(`Transformed ${feedItems.length} threads to feed items`);
    return feedItems;
  } catch (error) {
    console.error("Failed to generate imageboard feed:", error);
    const errorStack = error instanceof Error ? error.stack : undefined;
    console.error("Error stack:", errorStack);
    return [];
  }
}

export async function getImageboardGallery(
  threadId: string,
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
