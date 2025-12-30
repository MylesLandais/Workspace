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
  selftext?: string; // HTML content that may contain image tags
}

interface RedditPostData {
  subreddit: string;
  export_date: string;
  total_posts: number;
  images_downloaded: number;
  posts: RedditPost[];
}

export interface TransformedMedia {
  id: string;
  title: string;
  imageUrl: string;
  sourceUrl: string;
  publishDate: string;
  score: number;
  subreddit: {
    name: string;
  };
  author: {
    username: string;
  } | null;
  platform: 'reddit';
  handle: {
    name: string;
    handle: string;
    creatorName?: string;
  };
  mediaType: 'image' | 'text';
  // TODO: Add removed/deleted tracking metadata for mod tools evaluation
  // removed?: boolean;
  // removedBy?: 'moderator' | 'reddit' | 'user';
}

export interface SourcePreview {
  subredditName: string;
  totalPosts: number;
  imagesDownloaded: number;
  previewImage?: string;
  latestPosts: TransformedMedia[];
}

export const SUBREDDITS = ['Triangl', 'OvileeWorship', 'BrookeMonkTheSecond', 'Sjokz', 'BestOfBrookeMonk', 'BrookeMonkNSFWHub', 'howdyhowdyyallhot'];

/**
 * Extracts a unique image identifier from a URL
 * For Reddit images, extracts the base filename to catch URL variations
 */
function extractImageIdentifierFromUrl(url: string): string {
  try {
    const urlObj = new URL(url);
    const pathname = urlObj.pathname;
    const filename = pathname.split('/').pop() || '';
    return filename.toLowerCase();
  } catch (e) {
    // Fallback to normalized full URL if parsing fails
    return url.split('?')[0].split('#')[0].toLowerCase();
  }
}

/**
 * Extracts image URL from selftext HTML (for posts where is_image is false but selftext contains images)
 */
function extractImageUrlFromSelftext(selftext: string): string | null {
  if (!selftext) return null;
  
  // Try to find img tag with src attribute
  const imgTagMatch = /<img[^>]+src=["']([^"'>]+)["']/.exec(selftext);
  if (imgTagMatch && imgTagMatch[1]) {
    let url = imgTagMatch[1];
    // Decode HTML entities
    url = url.replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
    
    // Prefer direct i.redd.it URLs over preview URLs
    if (url.includes('preview.redd.it')) {
      // Try to extract the actual image URL from the link in selftext
      const linkMatch = /<a[^>]+href=["']([^"'>]+)["'][^>]*>/.exec(selftext);
      if (linkMatch && linkMatch[1].includes('i.redd.it')) {
        return linkMatch[1].replace(/&amp;/g, '&');
      }
      // Convert preview URL to direct URL if possible
      const previewMatch = /preview\.redd\.it\/([^?]+)/.exec(url);
      if (previewMatch) {
        return `https://i.redd.it/${previewMatch[1]}`;
      }
    }
    
    // For thumbs.redditmedia.com, try to find the gallery link
    if (url.includes('thumbs.redditmedia.com')) {
      const galleryMatch = /<a[^>]+href=["']([^"'>]*gallery[^"'>]+)["']/.exec(selftext);
      if (galleryMatch) {
        // Gallery posts need special handling, but for now return the thumb
        return url;
      }
    }
    
    return url;
  }
  
  return null;
}

/**
 * Maps subreddit names to their creator entity names
 * This establishes the ontology relationship between sources and entities
 */
function getCreatorNameForSubreddit(subredditName: string): string | undefined {
  const subredditToCreator: Record<string, string> = {
    'Sjokz': 'Sjokz',
    'BrookeMonkTheSecond': 'Brooke Monk',
    'BestOfBrookeMonk': 'Brooke Monk',
    'BrookeMonkNSFWHub': 'Brooke Monk',
    'OvileeWorship': 'Ovilee',
    'howdyhowdyyallhot': 'Howdy',
  };
  return subredditToCreator[subredditName];
}

function transformPost(post: RedditPost, subredditName: string): TransformedMedia | null {
  try {
    let imageUrl = post.image_url;
    let isImage = post.is_image;
    let extractedFromSelftext = false;

    // If is_image is false but selftext contains an image, try to extract it
    if (!isImage && post.selftext) {
      const extractedUrl = extractImageUrlFromSelftext(post.selftext);
      if (extractedUrl) {
        imageUrl = extractedUrl;
        isImage = true; // Treat as image post if URL is found in selftext
        extractedFromSelftext = true;
      }
    }

    // Skip posts without image URLs
    if (!isImage || !imageUrl || imageUrl.trim() === '') {
      if (isImage && !imageUrl) {
        console.debug(`[loader] Skipping post ${post.id} (${subredditName}): is_image=true but no image_url`);
      }
      return null;
    }

  // Filter out moderator/Reddit-removed posts
  // Check title patterns for removed posts (important for mod tools + bot tracking)
  const titleLower = post.title.toLowerCase().trim();
  const removedPatterns = [
    '[removed by reddit]',
    '[removed by moderator]',
    'removed by reddit',
    'removed by moderator',
  ];
  
  // Check permalink for removal indicators
  const permalinkLower = post.permalink?.toLowerCase() || '';
  const isRemoved = removedPatterns.some(pattern => 
    titleLower.includes(pattern) || permalinkLower.includes('removed_by_reddit') || permalinkLower.includes('removed_by_moderator')
  );
  
  if (isRemoved) {
    // Log removed posts for mod tool evaluation (can be tracked separately later)
    console.debug(`[loader] Filtered removed post: ${post.id} - ${post.title}`);
    return null;
  }

  // Filter out low-quality/repost indicators:
  // - Negative scores (downvoted content)
  // - Score of 0 with upvote_ratio of 0.0 (likely spam/removed/reposted content)
  // BUT: Allow posts with extracted images from selftext (they may have score 0 but are valid image posts)
  // This catches obvious low-quality duplicates while allowing new posts with score 0
  if (!extractedFromSelftext && (post.score < 0 || (post.score === 0 && post.upvote_ratio !== undefined && post.upvote_ratio === 0.0))) {
    return null;
  }

  const author = post.author ? post.author.replace('/u/', '').replace('u/', '') : 'unknown';
  
  let sourceUrl = post.url;
  if (post.permalink) {
    if (post.permalink.startsWith('http')) {
      sourceUrl = post.permalink;
    } else if (post.permalink.startsWith('/')) {
      sourceUrl = `https://reddit.com${post.permalink}`;
    } else {
      sourceUrl = `https://reddit.com/${post.permalink}`;
    }
  }
  
  const transformed = {
    id: post.id,
    title: post.title,
    imageUrl: imageUrl, // Use extracted URL (may be from selftext)
    sourceUrl,
    publishDate: new Date(post.created_utc).toISOString(),
    score: post.score,
    subreddit: {
      name: subredditName,
    },
    author: {
      username: author,
    },
    platform: 'reddit' as const,
    handle: {
      name: subredditName,
      handle: `r/${subredditName}`,
      creatorName: getCreatorNameForSubreddit(subredditName),
    },
    mediaType: 'image' as const,
  };
  
  // Debug logging for howdyhowdyyallhot
  if (subredditName === 'howdyhowdyyallhot') {
    console.log(`[loader] Transformed howdyhowdyyallhot post:`, {
      id: transformed.id,
      title: transformed.title,
      subredditName: transformed.subreddit.name,
      handleName: transformed.handle.name,
    });
  }
  
  return transformed;
  } catch (error) {
    console.error(`[loader] Error transforming post ${post.id} from ${subredditName}:`, error, post);
    return null;
  }
}

export async function loadSubredditData(subredditName: string): Promise<SourcePreview | null> {
  try {
    const response = await fetch(`/temp/mock_data/${subredditName}/json/${subredditName}_posts.json`);
    if (!response.ok) {
      console.warn(`Failed to load data for ${subredditName}:`, response.statusText);
      return null;
    }

    const data: RedditPostData = await response.json();
    
    const imagePosts = data.posts
      .map(post => transformPost(post, data.subreddit))
      .filter((post): post is TransformedMedia => post !== null);

    const previewImage = imagePosts.length > 0 ? imagePosts[0].imageUrl : undefined;
    const latestPosts = imagePosts.slice(0, 5);

    return {
      subredditName: data.subreddit,
      totalPosts: data.total_posts,
      imagesDownloaded: data.images_downloaded,
      previewImage,
      latestPosts,
    };
  } catch (error) {
    console.error(`Error loading data for ${subredditName}:`, error);
    return null;
  }
}

export async function loadAllSubredditData(): Promise<Map<string, SourcePreview>> {
  const results = new Map<string, SourcePreview>();
  
  const promises = SUBREDDITS.map(async (subreddit) => {
    const data = await loadSubredditData(subreddit);
    if (data) {
      results.set(subreddit, data);
    }
  });

  await Promise.all(promises);
  return results;
}

export async function getMediaForSubreddit(subredditName: string): Promise<TransformedMedia[]> {
  const sourceData = await loadSubredditData(subredditName);
  return sourceData?.latestPosts || [];
}

export async function loadAllMedia(): Promise<TransformedMedia[]> {
  const allMedia: TransformedMedia[] = [];
  
  const promises = SUBREDDITS.map(async (subredditName) => {
    try {
      const url = `/temp/mock_data/${subredditName}/json/${subredditName}_posts.json`;
      console.log(`[loader] Fetching ${url}...`);
      const response = await fetch(url);
      if (response.ok) {
        const data: RedditPostData = await response.json();
        console.log(`[loader] ${subredditName}: Found ${data.posts.length} total posts`);
        const imagePostsCount = data.posts.filter(p => p.is_image && p.image_url).length;
        console.log(`[loader] ${subredditName}: ${imagePostsCount} posts with is_image=true and image_url`);
        const imagePosts = data.posts
          .map(post => transformPost(post, data.subreddit))
          .filter((post): post is TransformedMedia => post !== null);
        console.log(`[loader] ${subredditName}: ${imagePosts.length} image posts after filtering (filtered out ${imagePostsCount - imagePosts.length})`);
        if (imagePosts.length > 0) {
          console.log(`[loader] ${subredditName}: Sample post:`, imagePosts[0]);
          if (subredditName === 'howdyhowdyyallhot') {
            console.log(`[loader] howdyhowdyyallhot: First post subreddit.name = "${imagePosts[0].subreddit.name}", handle.name = "${imagePosts[0].handle.name}"`);
          }
        } else if (subredditName === 'howdyhowdyyallhot') {
          console.error(`[loader] howdyhowdyyallhot: NO POSTS RETURNED after transform! Had ${imagePostsCount} posts with is_image=true and image_url`);
          // Debug: check why posts are being filtered
          const samplePost = data.posts.find(p => p.is_image && p.image_url);
          if (samplePost) {
            console.log(`[loader] howdyhowdyyallhot: Sample raw post before transform:`, samplePost);
            const transformed = transformPost(samplePost, data.subreddit);
            console.log(`[loader] howdyhowdyyallhot: After transform:`, transformed);
          }
        }
        return imagePosts;
      } else {
        console.warn(`[loader] Failed to load ${subredditName}: HTTP ${response.status} ${response.statusText}`);
        console.warn(`[loader] URL was: ${url}`);
      }
    } catch (error) {
      console.error(`[loader] Error loading media for ${subredditName}:`, error);
      console.error(`[loader] URL was: /temp/mock_data/${subredditName}/json/${subredditName}_posts.json`);
    }
    return [];
  });

  const results = await Promise.all(promises);
  results.forEach((posts, index) => {
    allMedia.push(...posts);
    console.log(`Added ${posts.length} posts from ${SUBREDDITS[index]}`);
  });
  
  // Deduplicate by image identifier (extracts filename to catch URL variations)
  const seenIdentifiers = new Map<string, TransformedMedia>();
  const validMedia: TransformedMedia[] = [];
  
  allMedia.forEach((item) => {
    // Skip invalid entries
    if (!item.imageUrl || !item.id || !item.title) {
      console.warn(`[loader] Skipping invalid media item:`, item);
      return;
    }
    
    // Extract image identifier (filename) to catch variations like:
    // - https://i.redd.it/abc123.jpeg vs https://preview.redd.it/abc123.jpeg?width=640
    // - Same image with different query parameters
    const imageId = extractImageIdentifierFromUrl(item.imageUrl);
    
    if (!seenIdentifiers.has(imageId)) {
      seenIdentifiers.set(imageId, item);
      validMedia.push(item);
    } else {
      console.debug(`[loader] Skipping duplicate image: ${imageId} (${item.imageUrl})`);
    }
  });
  
  console.log(`Total media loaded: ${allMedia.length} posts, ${validMedia.length} after deduplication (removed ${allMedia.length - validMedia.length})`);
  
  return validMedia.sort((a, b) => {
    const dateA = new Date(a.publishDate).getTime();
    const dateB = new Date(b.publishDate).getTime();
    return dateB - dateA;
  });
}

