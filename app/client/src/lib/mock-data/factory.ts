import { FeedItem, FeedPage, MediaType } from "../types/feed";

const ASPECT_RATIOS = [
  { ratio: "aspect-[3/4]", width: 600, height: 800 },
  { ratio: "aspect-[4/3]", width: 800, height: 600 },
  { ratio: "aspect-[16/9]", width: 800, height: 450 },
  { ratio: "aspect-[1/1]", width: 600, height: 600 },
  { ratio: "aspect-[9/16]", width: 450, height: 800 },
];

const SOURCES = ["Instagram", "Reddit", "Twitter", "TikTok", "Pinterest"];

const DEMO_VIDEOS = ["/demo-video.mp4", "/demo-video-2.mp4"];

const MEDIA_TYPES = [
  MediaType.IMAGE,
  MediaType.IMAGE,
  MediaType.IMAGE,
  MediaType.IMAGE,
  MediaType.SHORT,
  MediaType.GIF,
  MediaType.VIDEO,
  MediaType.VIDEO,
];

const CAPTIONS = [
  "Morning vibes in the city",
  "Found this gem while exploring",
  "Nature at its finest",
  "Throwback to better days",
  "Living my best life",
  "Sunset chaser",
  "Coffee and contemplation",
  "Weekend wanderings",
  "Art imitates life",
  "Quiet moments",
  "Urban jungle adventures",
  "Chasing dreams",
  "Golden hour magic",
  "Simple pleasures",
  "Escape the ordinary",
];

const AUTHORS = [
  { name: "Alex Chen", handle: "@alexc" },
  { name: "Jordan Smith", handle: "@jsmith" },
  { name: "Sam Rivera", handle: "@samr" },
  { name: "Taylor Kim", handle: "@tkim" },
  { name: "Morgan Lee", handle: "@mlee" },
  { name: "Casey Brooks", handle: "@cbrooks" },
  { name: "Jamie Park", handle: "@jpark" },
  { name: "Riley Adams", handle: "@radams" },
];

function seededRandom(seed: number): () => number {
  return function () {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
}

export function generateFeedItem(index: number): FeedItem {
  const random = seededRandom(index * 1337);
  const aspectData = ASPECT_RATIOS[Math.floor(random() * ASPECT_RATIOS.length)];
  const author = AUTHORS[Math.floor(random() * AUTHORS.length)];
  const source = SOURCES[Math.floor(random() * SOURCES.length)];
  const type = MEDIA_TYPES[Math.floor(random() * MEDIA_TYPES.length)];
  const caption = CAPTIONS[Math.floor(random() * CAPTIONS.length)];

  const date = new Date();
  date.setHours(date.getHours() - Math.floor(random() * 168)); // Random time in last week

  // Use demo video for VIDEO and SHORT types, otherwise use Picsum
  const mediaUrl =
    type === MediaType.VIDEO || type === MediaType.SHORT
      ? DEMO_VIDEOS[index % DEMO_VIDEOS.length]
      : `https://picsum.photos/seed/${index}/${aspectData.width}/${aspectData.height}`;

  return {
    id: `item-${index}`,
    type,
    caption,
    author,
    source,
    timestamp: date.toISOString(),
    aspectRatio: aspectData.ratio,
    width: aspectData.width,
    height: aspectData.height,
    likes: Math.floor(random() * 50000),
    mediaUrl,
  };
}

export function generateFeedPage(
  cursor: string | null,
  pageSize: number = 20
): FeedPage {
  const startIndex = cursor ? parseInt(cursor, 10) : 0;
  const items: FeedItem[] = [];

  for (let i = 0; i < pageSize; i++) {
    items.push(generateFeedItem(startIndex + i));
  }

  const nextCursor = startIndex + pageSize;
  const hasNextPage = nextCursor < 500; // Limit to 500 items total

  return {
    items,
    hasNextPage,
    endCursor: hasNextPage ? nextCursor.toString() : null,
  };
}

export function generateInitialFeed(pageSize: number = 20): FeedPage {
  return generateFeedPage(null, pageSize);
}
