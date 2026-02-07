import { FeedItem, MediaType } from "../types/feed";
import { decodeHtmlEntities } from "../utils";

interface RedditPost {
  id: string;
  title: string;
  created_utc: string;
  score: number;
  num_comments: number;
  author: string | null;
  image_url: string | null;
  is_image: boolean;
  url: string;
  permalink: string;
  subreddit: string;
  local_image_path?: string;
  upvote_ratio?: number;
  selftext?: string;
}

interface RedditPostData {
  subreddit: string;
  export_date: string;
  total_posts: number;
  images_downloaded: number;
  posts: RedditPost[];
}

export const REDDIT_SUBREDDITS = [
  "unixporn",
  "hyprland",
  "kde",
  "gnome",
  "UsabilityPorn",
  "battlestations",
];

let cachedData: RedditPostData[] | null = null;

async function loadRedditData(
  subredditName: string,
): Promise<RedditPostData | null> {
  const urls = [
    `/temp/mock_data/${subredditName}/json/${subredditName}_posts.json`,
    `/parquet-cache/${subredditName}_posts.json`,
  ];

  for (const url of urls) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        const data: RedditPostData = await response.json();
        console.log(`Loaded ${subredditName}: ${data.posts.length} posts`);
        return data;
      }
    } catch {}
  }
  return null;
}

async function loadAllRedditData(): Promise<RedditPostData[]> {
  if (cachedData) return cachedData;

  const allData: RedditPostData[] = [];

  for (const subredditName of REDDIT_SUBREDDITS) {
    const data = await loadRedditData(subredditName);
    if (data) {
      allData.push(data);
    }
  }

  cachedData = allData;
  console.log(`Loaded Reddit data from ${allData.length} subreddits`);
  return allData;
}

function transformPost(post: RedditPost): FeedItem | null {
  if (!post.is_image || !post.image_url) return null;

  return {
    id: post.id,
    type: MediaType.IMAGE,
    caption: decodeHtmlEntities(post.title),
    author: {
      name: decodeHtmlEntities(post.author || "Unknown"),
      handle: decodeHtmlEntities(post.author || "unknown"),
    },
    source: post.subreddit,
    timestamp: new Date(post.created_utc).toISOString(),
    aspectRatio: "aspect-[4/3]",
    width: 800,
    height: 600,
    likes: post.score,
    mediaUrl: post.image_url,
  };
}

export async function generateRedditFeed(): Promise<FeedItem[]> {
  console.log("generateRedditFeed() called");

  const allData = await loadAllRedditData();
  const allPosts = allData.flatMap((data) => data.posts);

  const feedItems = allPosts
    .map((post) => transformPost(post))
    .filter((post): post is FeedItem => post !== null);

  const sortedItems = feedItems.sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
  );

  console.log(`Generated ${sortedItems.length} Reddit feed items`);
  return sortedItems;
}
