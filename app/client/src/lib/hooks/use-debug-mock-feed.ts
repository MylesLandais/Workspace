"use client";

import { FeedItem, MediaType } from "../types/feed";

const ASPECT_RATIOS = [
  { ratio: "aspect-[3/4]", width: 600, height: 800 },
  { ratio: "aspect-[4/3]", width: 800, height: 600 },
  { ratio: "aspect-[16/9]", width: 800, height: 450 },
  { ratio: "aspect-[1/1]", width: 600, height: 600 },
  { ratio: "aspect-[9/16]", width: 450, height: 800 },
];

const SOURCES = ["Reddit", "Pinterest", "Twitter", "Instagram", "TikTok"];

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
];

const AUTHORS = [
  { name: "Alex Chen", handle: "@alexc" },
  { name: "Jordan Smith", handle: "@jsmith" },
  { name: "Sam Rivera", handle: "@samr" },
  { name: "Taylor Kim", handle: "@tkim" },
  { name: "Morgan Lee", handle: "@mlee" },
];

function seededRandom(seed: number): () => number {
  return function () {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
}

function generateDebugItem(index: number): FeedItem {
  const random = seededRandom(index * 1337);
  const aspectData = ASPECT_RATIOS[Math.floor(random() * ASPECT_RATIOS.length)];
  const author = AUTHORS[Math.floor(random() * AUTHORS.length)];
  const source = SOURCES[Math.floor(random() * SOURCES.length)];
  const caption = CAPTIONS[Math.floor(random() * CAPTIONS.length)];

  const date = new Date();
  date.setHours(date.getHours() - Math.floor(random() * 168));

  const type = random() > 0.7 ? MediaType.VIDEO : MediaType.IMAGE;
  const mediaUrl = `https://picsum.photos/seed/${index}/${aspectData.width}/${aspectData.height}`;

  const redditData =
    source === "Reddit"
      ? {
          id: `reddit-${index}`,
          title: caption,
          created_utc: date.toISOString(),
          score: Math.floor(random() * 50000),
          num_comments: Math.floor(random() * 1000),
          upvote_ratio: 0.8 + random() * 0.2,
          over_18: random() > 0.9,
          url: mediaUrl,
          selftext:
            random() > 0.5 ? "This is a mock selftext for testing." : "",
          permalink: `/r/${source.toLowerCase()}/comments/${index}`,
          subreddit: "artwork",
          author: author.handle.replace("@", ""),
          is_image: type === MediaType.IMAGE,
          image_url: type === MediaType.IMAGE ? mediaUrl : null,
        }
      : undefined;

  return {
    id: `debug-item-${index}`,
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
    redditData,
  };
}

// Generate 20 debug items synchronously at module load time
const DEBUG_ITEMS: FeedItem[] = Array.from({ length: 20 }, (_, i) =>
  generateDebugItem(i),
);

export function useDebugMockFeed(): FeedItem[] {
  return DEBUG_ITEMS;
}
