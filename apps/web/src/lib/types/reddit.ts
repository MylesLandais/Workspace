/**
 * Reddit Data API Types
 * Source of truth for Reddit data schema
 * API Base: http://localhost:8001
 */

export interface RedditPost {
  id: string;
  title: string;
  created_utc: string; // ISO 8601 format
  score: number;
  num_comments: number;
  upvote_ratio: number;
  over_18: boolean;
  url: string;
  selftext: string;
  permalink: string;
  subreddit: string;
  author: string | null;
  is_image: boolean;
  image_url: string | null;
}

export interface RedditComment {
  id: string;
  body: string;
  author: string | null;
  score: number;
  depth: number;
  is_submitter: boolean;
  created_utc: string;
  link_id: string;
}

export interface RedditImage {
  url: string;
  image_path: string | null; // Local cache path if downloaded
}

export interface RedditPostDetails {
  post: RedditPost;
  comments: RedditComment[];
  images: RedditImage[];
}

export interface RedditSubreddit {
  name: string;
  post_count: number;
}

export interface RedditStats {
  total_posts: number;
  total_comments: number;
  total_images: number;
  cached_images: number;
  total_subreddits: number;
}

// API Response types
export interface PostsQueryParams {
  subreddit?: string;
  min_score?: number;
  is_image?: boolean;
  limit?: number;
  offset?: number;
}
