import { FeedItem, FeedPage, MediaType } from "../types/feed";
import { RedditPostDetails } from "../types/reddit";
import { generateImageboardFeed } from "./imageboard-loader";
import testFiles from "./test-files.json";

const ASPECT_RATIOS = [
  { ratio: "aspect-[3/4]", width: 600, height: 800 },
  { ratio: "aspect-[4/3]", width: 800, height: 600 },
  { ratio: "aspect-[16/9]", width: 800, height: 450 },
  { ratio: "aspect-[1/1]", width: 600, height: 600 },
  { ratio: "aspect-[9/16]", width: 450, height: 800 },
];

const SOURCES = ["Instagram", "Reddit", "Twitter", "TikTok", "Pinterest"];

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

const COMMENT_AUTHORS = [
  "tech_enthusiast", "art_lover", "coffee_addict", "nature_explorer",
  "design_nerd", "music_fan", "bookworm", "gym_rat", "foodie",
  "travel_bug", "gamer", "student", "parent", "entrepreneur"
];

const COMMENT_BODIES = [
  "This is absolutely amazing! Love the composition and colors.",
  "Great shot! The lighting is perfect here. How did you achieve this?",
  "I've been to this place, it's even more beautiful in person.",
  "The detail in this is incredible. Well done!",
  "This deserves way more upvotes. Stunning work.",
  "Thanks for sharing! This made my day.",
  "Saved this. Definitely using it as inspiration.",
  "The aesthetic here is chef's kiss. Perfect vibe.",
  "How long did this take to create/capture?",
  "Mind if I use this as a reference? Love the style.",
  "This is going straight to my collection. Amazing.",
  "The contrast and depth here are next level.",
];

function seededRandom(seed: number): () => number {
  return function () {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
}

function generateMockComments(postId: string, count: number = 8) {
  const random = seededRandom(parseInt(postId.replace(/\D/g, '')) || 0);
  const comments = [];
  const baseDate = new Date();

  for (let i = 0; i < count; i++) {
    const timeOffset = Math.floor(random() * 86400000); // Random time in last 24 hours
    comments.push({
      id: `comment-${postId}-${i}`,
      body: COMMENT_BODIES[Math.floor(random() * COMMENT_BODIES.length)],
      author: COMMENT_AUTHORS[Math.floor(random() * COMMENT_AUTHORS.length)],
      score: Math.floor(random() * 10000),
      depth: Math.floor(random() * 3), // 0-2 depth for nesting
      is_submitter: i === 0 && random() > 0.7,
      created_utc: new Date(baseDate.getTime() - timeOffset).toISOString(),
      link_id: `t3_${postId}`,
    });
  }

  return comments;
}

export function generateMockPostDetails(postId: string, redditPost: any): RedditPostDetails {
  return {
    post: redditPost,
    comments: generateMockComments(postId, 8),
    images: [],
  };
}

export function generateFeedItem(index: number): FeedItem {
  const random = seededRandom(index * 1337);
  const aspectData = ASPECT_RATIOS[Math.floor(random() * ASPECT_RATIOS.length)];
  const author = AUTHORS[Math.floor(random() * AUTHORS.length)];
  const source = SOURCES[Math.floor(random() * SOURCES.length)];
  const caption = CAPTIONS[Math.floor(random() * CAPTIONS.length)];

  const date = new Date();
  date.setHours(date.getHours() - Math.floor(random() * 168)); // Random time in last week

  // Use local test files if available, otherwise fallback to picsum
  let mediaUrl: string;
  let type: MediaType = MediaType.IMAGE;

  if (testFiles.length > 0) {
    const fileName = testFiles[index % testFiles.length];
    mediaUrl = `/test-media/${fileName}`;
    
    if (fileName.endsWith('.mp4') || fileName.endsWith('.webm')) {
      type = MediaType.VIDEO;
    } else if (fileName.endsWith('.gif')) {
      type = MediaType.GIF;
    }
  } else {
    mediaUrl = `https://picsum.photos/seed/${index}/${aspectData.width}/${aspectData.height}`;
  }

  const redditData = source === "Reddit" ? {
    id: `reddit-${index}`,
    title: caption,
    created_utc: date.toISOString(),
    score: Math.floor(random() * 50000),
    num_comments: Math.floor(random() * 1000),
    upvote_ratio: 0.8 + random() * 0.2,
    over_18: random() > 0.9,
    url: mediaUrl,
    selftext: random() > 0.5 ? "This is a mock selftext for testing the expanded view of Reddit posts." : "",
    permalink: `/r/${source.toLowerCase()}/comments/${index}`,
    subreddit: "artwork",
    author: author.handle.replace('@', ''),
    is_image: type === MediaType.IMAGE,
    image_url: type === MediaType.IMAGE ? mediaUrl : null,
  } : undefined;

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
    redditData,
  };
}

export async function generateFeedPage(
  cursor: string | null,
  pageSize: number = 20
): Promise<FeedPage> {
  const startIndex = cursor ? parseInt(cursor, 10) : 0;
  const items: FeedItem[] = [];

  // Mix imageboard threads with regular feed items
  const imageboardFeed = await generateImageboardFeed();
  const totalItems = 500 + imageboardFeed.length;

  for (let i = 0; i < pageSize; i++) {
    const currentIndex = startIndex + i;

    // Add imageboard threads at the beginning
    if (currentIndex < imageboardFeed.length) {
      items.push(imageboardFeed[currentIndex]);
    } else {
      items.push(generateFeedItem(currentIndex - imageboardFeed.length));
    }
  }

  const nextCursor = startIndex + pageSize;
  const hasNextPage = nextCursor < totalItems;

  return {
    items,
    hasNextPage,
    endCursor: hasNextPage ? nextCursor.toString() : null,
  };
}

export async function generateInitialFeed(pageSize: number = 20): Promise<FeedPage> {
  return generateFeedPage(null, pageSize);
}
