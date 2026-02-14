import { NextRequest, NextResponse } from "next/server";

const GRAPHQL_ENDPOINT =
  process.env.GRAPHQL_API_URL || "http://localhost:4002/api/graphql";

// Cache for gallery images to avoid repeated Reddit API calls
const galleryCache = new Map<string, string | null>();

/**
 * Extract gallery images from Reddit JSON API
 * Gallery posts have URLs like https://www.reddit.com/gallery/{id}
 */
async function fetchGalleryImage(
  postId: string,
  url: string,
): Promise<string | null> {
  // Only process gallery URLs
  if (!url.includes("/gallery/")) {
    galleryCache.set(postId, null);
    return null;
  }

  // Extract gallery ID from URL (may differ from post ID for cross-posts)
  const galleryMatch = url.match(/\/gallery\/([a-z0-9]+)/i);
  const galleryId = galleryMatch ? galleryMatch[1] : postId;

  // Check cache first (use gallery ID as key)
  const cacheKey = `gallery:${galleryId}`;
  if (galleryCache.has(cacheKey)) {
    return galleryCache.get(cacheKey) || null;
  }

  try {
    // Fetch post JSON from Reddit using gallery ID
    const redditUrl = `https://www.reddit.com/comments/${galleryId}.json`;
    const response = await fetch(redditUrl, {
      headers: {
        "User-Agent": "Bunny/1.0 (feed aggregator)",
      },
    });

    if (!response.ok) {
      galleryCache.set(cacheKey, null);
      return null;
    }

    const data = await response.json();
    const postData = data?.[0]?.data?.children?.[0]?.data;

    if (!postData?.media_metadata) {
      // Try preview images as fallback
      const previewUrl = postData?.preview?.images?.[0]?.source?.url?.replace(
        /&amp;/g,
        "&",
      );
      galleryCache.set(cacheKey, previewUrl || null);
      return previewUrl || null;
    }

    // Get first image from gallery
    const mediaIds =
      postData.gallery_data?.items?.map(
        (item: { media_id: string }) => item.media_id,
      ) || Object.keys(postData.media_metadata);
    const firstMediaId = mediaIds[0];

    if (firstMediaId && postData.media_metadata[firstMediaId]) {
      const media = postData.media_metadata[firstMediaId];
      // Get the highest resolution image (s = source/full resolution)
      const imageUrl =
        media.s?.u?.replace(/&amp;/g, "&") ||
        media.s?.gif?.replace(/&amp;/g, "&");
      galleryCache.set(cacheKey, imageUrl || null);
      return imageUrl || null;
    }

    galleryCache.set(cacheKey, null);
    return null;
  } catch (error) {
    console.error(`[Gallery] Failed to fetch gallery for ${galleryId}:`, error);
    galleryCache.set(cacheKey, null);
    return null;
  }
}

const REDDIT_POSTS_QUERY = `
  query RedditPosts($subreddit: String!, $limit: Int, $offset: Int) {
    redditPosts(subreddit: $subreddit, limit: $limit, offset: $offset) {
      id
      title
      url
      permalink
      author
      score
      numComments
      upvoteRatio
      over18
      selftext
      createdAt
      subreddit
      isImage
      imageUrl
      imageWidth
      imageHeight
      mediaUrl
      isRead
    }
  }
`;

export async function GET(request: NextRequest) {
  console.log("[Reddit Posts API] Starting request to:", GRAPHQL_ENDPOINT);

  try {
    const searchParams = request.nextUrl.searchParams;
    const subreddit = searchParams.get("subreddit") || "unixporn";
    const limit = parseInt(searchParams.get("limit") || "20");
    const offset = parseInt(searchParams.get("offset") || "0");

    const response = await fetch(GRAPHQL_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: REDDIT_POSTS_QUERY,
        variables: {
          subreddit,
          limit,
          offset,
        },
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(
        `[Reddit Posts API] GraphQL HTTP error: ${response.status} ${response.statusText}`,
      );
      console.error(`[Reddit Posts API] Response body: ${errorText}`);
      throw new Error(`GraphQL request failed: ${response.statusText}`);
    }

    const data = await response.json();

    if (data.errors) {
      console.error("[Reddit Posts API] GraphQL errors:", data.errors);
      return NextResponse.json(
        { error: "Failed to fetch reddit posts", details: data.errors },
        { status: 500 },
      );
    }

    if (!data.data || !data.data.redditPosts) {
      return NextResponse.json(
        { error: "Invalid response from GraphQL server" },
        { status: 500 },
      );
    }

    // Transform to match RedditPost client type (snake_case)
    // First pass: basic transformation
    const rawPosts = data.data.redditPosts.map(
      (post: {
        id: string;
        title: string;
        url: string;
        permalink: string;
        author: string | null;
        score: number;
        numComments: number;
        upvoteRatio: number;
        over18: boolean;
        selftext: string | null;
        createdAt: string;
        subreddit: string;
        isImage: boolean;
        imageUrl: string | null;
        imageWidth: number | null;
        imageHeight: number | null;
        mediaUrl: string | null;
        isRead: boolean | null;
      }) => ({
        id: post.id,
        title: post.title,
        url: post.url,
        permalink: post.permalink,
        author: post.author,
        score: post.score,
        num_comments: post.numComments,
        upvote_ratio: post.upvoteRatio,
        over_18: post.over18,
        selftext: post.selftext || "",
        created_utc: post.createdAt,
        subreddit: post.subreddit,
        is_image: post.isImage,
        image_url: post.mediaUrl || post.imageUrl, // Prefer mediaUrl from MinIO
        image_width: post.imageWidth,
        image_height: post.imageHeight,
        media_url: post.mediaUrl,
        is_read: post.isRead || false,
      }),
    );

    // Second pass: resolve gallery images for posts without images
    // Process in parallel with concurrency limit
    const CONCURRENCY = 5;
    const postsNeedingGallery = rawPosts.filter(
      (p: { image_url: string | null; url: string }) =>
        !p.image_url && p.url.includes("/gallery/"),
    );

    // Batch fetch gallery images
    for (let i = 0; i < postsNeedingGallery.length; i += CONCURRENCY) {
      const batch = postsNeedingGallery.slice(i, i + CONCURRENCY);
      await Promise.all(
        batch.map(
          async (post: {
            id: string;
            url: string;
            image_url: string | null;
            is_image: boolean;
          }) => {
            const galleryImage = await fetchGalleryImage(post.id, post.url);
            if (galleryImage) {
              post.image_url = galleryImage;
              post.is_image = true;
            }
          },
        ),
      );
    }

    return NextResponse.json({ posts: rawPosts });
  } catch (error) {
    console.error("[Reddit Posts API] Error:", error);
    return NextResponse.json(
      {
        error: "Internal server error",
        message: error instanceof Error ? error.message : String(error),
      },
      { status: 500 },
    );
  }
}
