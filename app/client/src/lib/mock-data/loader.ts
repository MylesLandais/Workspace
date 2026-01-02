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

export const SUBREDDITS = [
    'AddisonRae', 'ArianaGrande', 'SelenaGomez', 'TaylorSwift', 'SydneySweeney',
    'MargotRobbie', 'kendalljenner', 'NinaDobrev', 'blakelively', 'MirandaKerr',
    'unixporn', 'hyprland', 'kde', 'gnome', 'UsabilityPorn', 'battlestations'
];

function extractImageIdentifierFromUrl(url: string): string {
    try {
        const urlObj = new URL(url);
        return (urlObj.pathname.split('/').pop() || '').toLowerCase();
    } catch {
        return url.split('?')[0].split('#')[0].toLowerCase();
    }
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
        aspectRatio: "aspect-auto", // Will be measured
        width: 800, // Default placeholders
        height: 600,
        likes: post.score,
        mediaUrl: post.image_url,
    };
}

export async function loadAllMedia(): Promise<FeedItem[]> {
    const allMedia: FeedItem[] = [];

    const promises = SUBREDDITS.map(async (subredditName) => {
        try {
            // Note: we use /temp/ prefix because it's mounted in public/temp
            const url = `/temp/mock_data/${subredditName}/json/${subredditName}_posts.json`;
            const response = await fetch(url);
            if (response.ok) {
                const data: RedditPostData = await response.json();
                return data.posts
                    .map(post => transformPost(post))
                    .filter((post): post is FeedItem => post !== null);
            }
        } catch { }
        return [];
    });

    const results = await Promise.all(promises);
    results.forEach(posts => allMedia.push(...posts));

    // Deduplication
    const seenIdentifiers = new Set<string>();
    const validMedia: FeedItem[] = [];

    allMedia.forEach((item) => {
        if (!item.mediaUrl) return;
        const imageId = extractImageIdentifierFromUrl(item.mediaUrl);
        if (!seenIdentifiers.has(imageId)) {
            seenIdentifiers.add(imageId);
            validMedia.push(item);
        }
    });

    return validMedia.sort((a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
}
