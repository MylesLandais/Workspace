import { FeedItem, MediaType } from "../types/feed";
import { decodeHtmlEntities } from "../utils";

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
  const titleMatch = html.match(/<title>\/[a-z]\/ - ([^-]+) -/);
  const title = decodeHtmlEntities(
    titleMatch ? titleMatch[1].trim() : "4chan Thread",
  );

  const opMatch = html.match(
    /<blockquote class="postMessage"[^>]*>([^<]*(?:<(?!\/blockquote)[^>]*>[^<]*)*)<\/blockquote>/,
  );
  let opBody = opMatch ? opMatch[1].trim() : "";

  opBody = decodeHtmlEntities(opBody)
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .substring(0, 200);

  return { title, opBody };
}

export function transformThreadToFeedItem(
  thread: ImageboardThread,
): FeedItem & { galleryUrls: string[] } {
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
      handle: `@anon_${thread.threadId.slice(-6)}`,
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

// NEW FRESH IMPLEMENTATION - SIMPLIFIED
export async function generateImageboardFeedFresh(): Promise<FeedItem[]> {
  console.log("generateImageboardFeedFresh() called");

  try {
    // Just return one hardcoded item for testing
    const item: FeedItem = {
      id: "imageboard-test-123",
      type: MediaType.IMAGE,
      caption: "Test Imageboard Thread",
      author: {
        name: "Anonymous",
        handle: "@anon_123456",
      },
      source: "Imageboard",
      timestamp: new Date().toISOString(),
      aspectRatio: "aspect-[4/3]",
      width: 800,
      height: 600,
      likes: 1000,
      mediaUrl: "https://picsum.photos/seed/test/800/600",
      tags: ["b", "test", "gallery"],
      galleryUrls: ["https://picsum.photos/seed/test/800/600"],
      replyCount: 50,
      imageCount: 1,
    };

    console.log("[SUCCESS] Created test item:", item);

    return [item];
  } catch (error) {
    console.error("[ERROR] Error in generateImageboardFeedFresh:", error);
    return [];
  }
}
