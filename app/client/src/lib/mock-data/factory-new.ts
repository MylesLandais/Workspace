import { FeedItem, FeedPage, MediaType } from "../types/feed";

export async function generateFeedPage(
  cursor: string | null,
  pageSize: number = 20
): Promise<FeedPage> {
  const startIndex = cursor ? parseInt(cursor, 10) : 0;
  const items: FeedItem[] = [];

  console.log('NEW FACTORY: Creating items...');

  for (let i = 0; i < pageSize; i++) {
    const item: FeedItem = {
      id: `item-${startIndex + i}`,
      type: MediaType.IMAGE,
      caption: `Test Item ${startIndex + i}`,
      author: {
        name: "Test User",
        handle: `@testuser${startIndex + i}`,
      },
      source: "NewFactory",
      timestamp: new Date().toISOString(),
      aspectRatio: "aspect-[4/3]",
      width: 800,
      height: 600,
      likes: 100,
      mediaUrl: 'https://picsum.photos/seed/test/800/600',
      tags: ["test"],
    };
    
    items.push(item);
    console.log(`NEW FACTORY: Created item ${startIndex + i}: ${item.caption}`);
  }

  console.log(`NEW FACTORY: Generated ${items.length} items`);

  const nextCursor = startIndex + pageSize;
  const hasNextPage = true;

  return {
    items,
    hasNextPage,
    endCursor: nextCursor.toString(),
  };
}

export async function generateInitialFeed(pageSize: number = 20): Promise<FeedPage> {
  return generateFeedPage(null, pageSize);
}