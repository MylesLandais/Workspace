export interface OPMLFeed {
  title: string;
  xmlUrl: string;
  htmlUrl?: string;
  category?: string;
  description?: string;
}

export interface OPMLParseResult {
  feeds: OPMLFeed[];
  feedCount: number;
  categories: string[];
  errors: string[];
}

interface FeedMetadata {
  title: string;
  description?: string;
  iconUrl?: string;
  siteUrl?: string;
}

/**
 * Parse OPML content and extract RSS feed information
 */
export function parseOPMLContent(xml: string): OPMLParseResult {
  const feeds: OPMLFeed[] = [];
  const categories = new Set<string>();
  const errors: string[] = [];

  try {
    // Extract all outline elements with xmlUrl (these are the actual feeds)
    const outlineRegex = /<outline[^>]*>/gi;
    const matches = xml.match(outlineRegex) || [];

    let currentCategory = "";

    for (const match of matches) {
      const xmlUrl = extractAttribute(match, "xmlUrl");

      if (xmlUrl) {
        // This is a feed
        const title =
          extractAttribute(match, "text") ||
          extractAttribute(match, "title") ||
          "Untitled Feed";
        const htmlUrl = extractAttribute(match, "htmlUrl");
        const description = extractAttribute(match, "description");

        feeds.push({
          title: decodeXMLEntities(title),
          xmlUrl: decodeXMLEntities(xmlUrl),
          htmlUrl: htmlUrl ? decodeXMLEntities(htmlUrl) : undefined,
          category: currentCategory || undefined,
          description: description ? decodeXMLEntities(description) : undefined,
        });
      } else {
        // This might be a category folder
        const text = extractAttribute(match, "text");
        if (text && !extractAttribute(match, "type")) {
          currentCategory = decodeXMLEntities(text);
          categories.add(currentCategory);
        }
      }
    }

    // Reset category tracking for nested structures
    // Re-parse with proper nesting awareness
    const properlyParsedFeeds = parseWithCategories(xml);
    if (properlyParsedFeeds.length > 0) {
      feeds.length = 0;
      feeds.push(...properlyParsedFeeds);
      properlyParsedFeeds.forEach((f) => {
        if (f.category) categories.add(f.category);
      });
    }
  } catch (error) {
    errors.push(`Failed to parse OPML: ${(error as Error).message}`);
  }

  return {
    feeds,
    feedCount: feeds.length,
    categories: Array.from(categories),
    errors,
  };
}

/**
 * Parse OPML with proper category nesting
 */
function parseWithCategories(xml: string): OPMLFeed[] {
  const feeds: OPMLFeed[] = [];

  // Find the body content
  const bodyMatch = xml.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  if (!bodyMatch) return feeds;

  const bodyContent = bodyMatch[1];

  // Parse nested outlines
  parseOutlineLevel(bodyContent, "", feeds);

  return feeds;
}

function parseOutlineLevel(
  content: string,
  parentCategory: string,
  feeds: OPMLFeed[]
): void {
  // Match outline tags at current level
  const outlineStartRegex = /<outline\s+([^>]*)(?:\/>|>)/gi;
  let match: RegExpExecArray | null;
  let lastIndex = 0;

  while ((match = outlineStartRegex.exec(content)) !== null) {
    const attributes = match[1];
    const isSelfClosing = match[0].endsWith("/>");
    const xmlUrl = extractAttribute(match[0], "xmlUrl");

    if (xmlUrl) {
      // This is a feed
      const title =
        extractAttribute(match[0], "text") ||
        extractAttribute(match[0], "title") ||
        "Untitled Feed";
      const htmlUrl = extractAttribute(match[0], "htmlUrl");
      const description = extractAttribute(match[0], "description");

      feeds.push({
        title: decodeXMLEntities(title),
        xmlUrl: decodeXMLEntities(xmlUrl),
        htmlUrl: htmlUrl ? decodeXMLEntities(htmlUrl) : undefined,
        category: parentCategory || undefined,
        description: description ? decodeXMLEntities(description) : undefined,
      });
    } else if (!isSelfClosing) {
      // This is a category folder, find its closing tag and children
      const text = extractAttribute(match[0], "text");
      const category = text ? decodeXMLEntities(text) : parentCategory;

      // Find the matching closing tag
      const startPos = match.index + match[0].length;
      const closingPos = findMatchingClosingTag(content, startPos);

      if (closingPos > startPos) {
        const innerContent = content.substring(startPos, closingPos);
        parseOutlineLevel(innerContent, category, feeds);
      }
    }

    lastIndex = outlineStartRegex.lastIndex;
  }
}

function findMatchingClosingTag(content: string, startPos: number): number {
  let depth = 1;
  let pos = startPos;

  while (depth > 0 && pos < content.length) {
    const openMatch = content.indexOf("<outline", pos);
    const closeMatch = content.indexOf("</outline>", pos);

    if (closeMatch === -1) break;

    if (openMatch !== -1 && openMatch < closeMatch) {
      // Check if it's self-closing
      const tagEnd = content.indexOf(">", openMatch);
      if (tagEnd !== -1 && content[tagEnd - 1] !== "/") {
        depth++;
      }
      pos = tagEnd + 1;
    } else {
      depth--;
      if (depth === 0) return closeMatch;
      pos = closeMatch + 10;
    }
  }

  return content.length;
}

/**
 * Extract attribute value from an XML tag string
 */
function extractAttribute(tag: string, name: string): string | null {
  // Handle both single and double quotes
  const doubleQuoteRegex = new RegExp(`${name}\\s*=\\s*"([^"]*)"`, "i");
  const singleQuoteRegex = new RegExp(`${name}\\s*=\\s*'([^']*)'`, "i");

  const doubleMatch = tag.match(doubleQuoteRegex);
  if (doubleMatch) return doubleMatch[1];

  const singleMatch = tag.match(singleQuoteRegex);
  if (singleMatch) return singleMatch[1];

  return null;
}

/**
 * Decode XML entities
 */
function decodeXMLEntities(text: string): string {
  return text
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(parseInt(code, 10)))
    .replace(/&#x([0-9a-fA-F]+);/g, (_, code) =>
      String.fromCharCode(parseInt(code, 16))
    );
}

/**
 * Validate an RSS feed URL by fetching it
 */
export async function validateRssUrl(url: string): Promise<boolean> {
  try {
    const response = await fetch(url, {
      method: "HEAD",
      headers: {
        "User-Agent": "Bunny RSS Reader/1.0",
      },
      signal: AbortSignal.timeout(10000),
    });

    if (!response.ok) return false;

    const contentType = response.headers.get("content-type") || "";
    return (
      contentType.includes("xml") ||
      contentType.includes("rss") ||
      contentType.includes("atom")
    );
  } catch {
    return false;
  }
}

/**
 * Fetch metadata from an RSS feed URL
 */
export async function fetchFeedMetadata(url: string): Promise<FeedMetadata> {
  try {
    const response = await fetch(url, {
      headers: {
        "User-Agent": "Bunny RSS Reader/1.0",
        Accept: "application/rss+xml, application/xml, text/xml, */*",
      },
      signal: AbortSignal.timeout(15000),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const xml = await response.text();

    // Extract title
    const titleMatch =
      xml.match(/<title[^>]*>(?:<!\[CDATA\[)?([^\]<]+)(?:\]\]>)?<\/title>/i) ||
      xml.match(/<title>([^<]+)<\/title>/i);
    const title = titleMatch ? decodeXMLEntities(titleMatch[1].trim()) : url;

    // Extract description
    const descMatch =
      xml.match(
        /<description[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/description>/i
      ) ||
      xml.match(/<subtitle[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/subtitle>/i);
    const description = descMatch
      ? decodeXMLEntities(descMatch[1].trim()).substring(0, 500)
      : undefined;

    // Extract icon/image URL
    const iconMatch =
      xml.match(/<image[^>]*>[\s\S]*?<url>([^<]+)<\/url>/i) ||
      xml.match(/<icon>([^<]+)<\/icon>/i) ||
      xml.match(/<logo>([^<]+)<\/logo>/i);
    const iconUrl = iconMatch ? decodeXMLEntities(iconMatch[1].trim()) : undefined;

    // Extract site URL
    const linkMatch =
      xml.match(/<link[^>]*href="([^"]+)"[^>]*rel="alternate"/i) ||
      xml.match(/<link>([^<]+)<\/link>/i);
    const siteUrl = linkMatch ? decodeXMLEntities(linkMatch[1].trim()) : undefined;

    return {
      title,
      description,
      iconUrl,
      siteUrl,
    };
  } catch (error) {
    return {
      title: url,
      description: undefined,
      iconUrl: undefined,
    };
  }
}

/**
 * Discover RSS feeds from a website URL
 */
export async function discoverFeeds(websiteUrl: string): Promise<OPMLFeed[]> {
  const feeds: OPMLFeed[] = [];

  try {
    // Normalize URL
    let url = websiteUrl;
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      url = `https://${url}`;
    }

    const response = await fetch(url, {
      headers: {
        "User-Agent": "Bunny RSS Reader/1.0",
        Accept: "text/html,application/xhtml+xml",
      },
      signal: AbortSignal.timeout(15000),
    });

    if (!response.ok) return feeds;

    const html = await response.text();

    // Look for RSS/Atom link tags
    const linkRegex =
      /<link[^>]*type=["'](application\/rss\+xml|application\/atom\+xml)["'][^>]*>/gi;
    let match: RegExpExecArray | null;

    while ((match = linkRegex.exec(html)) !== null) {
      const href = extractAttribute(match[0], "href");
      const title =
        extractAttribute(match[0], "title") || "RSS Feed";

      if (href) {
        // Resolve relative URLs
        let feedUrl = href;
        if (href.startsWith("/")) {
          const urlObj = new URL(url);
          feedUrl = `${urlObj.origin}${href}`;
        } else if (!href.startsWith("http")) {
          feedUrl = new URL(href, url).toString();
        }

        feeds.push({
          title: decodeXMLEntities(title),
          xmlUrl: feedUrl,
          htmlUrl: url,
        });
      }
    }

    // Also check common feed paths if no links found
    if (feeds.length === 0) {
      const commonPaths = [
        "/feed",
        "/rss",
        "/rss.xml",
        "/feed.xml",
        "/atom.xml",
        "/feeds/posts/default",
      ];

      const urlObj = new URL(url);
      for (const path of commonPaths) {
        try {
          const feedUrl = `${urlObj.origin}${path}`;
          const isValid = await validateRssUrl(feedUrl);
          if (isValid) {
            const metadata = await fetchFeedMetadata(feedUrl);
            feeds.push({
              title: metadata.title,
              xmlUrl: feedUrl,
              htmlUrl: url,
              description: metadata.description,
            });
            break; // Found a valid feed, stop searching
          }
        } catch {
          continue;
        }
      }
    }
  } catch (error) {
    // Return empty array on error
  }

  return feeds;
}

/**
 * Detect source type from URL
 */
export function detectSourceType(
  url: string
): "RSS" | "REDDIT" | "YOUTUBE" | "TWITTER" | "INSTAGRAM" | "TIKTOK" | null {
  const lowercaseUrl = url.toLowerCase();

  if (lowercaseUrl.includes("reddit.com") || lowercaseUrl.startsWith("r/")) {
    return "REDDIT";
  }
  if (
    lowercaseUrl.includes("youtube.com") ||
    lowercaseUrl.includes("youtu.be")
  ) {
    return "YOUTUBE";
  }
  if (lowercaseUrl.includes("twitter.com") || lowercaseUrl.includes("x.com")) {
    return "TWITTER";
  }
  if (lowercaseUrl.includes("instagram.com")) {
    return "INSTAGRAM";
  }
  if (lowercaseUrl.includes("tiktok.com")) {
    return "TIKTOK";
  }

  // Check if it's an RSS/XML URL
  if (
    lowercaseUrl.endsWith(".xml") ||
    lowercaseUrl.endsWith(".rss") ||
    lowercaseUrl.includes("/feed") ||
    lowercaseUrl.includes("/rss")
  ) {
    return "RSS";
  }

  return null;
}

/**
 * Extract handle/identifier from platform URL
 */
export function extractHandleFromUrl(url: string): string | null {
  try {
    const urlObj = new URL(url.startsWith("http") ? url : `https://${url}`);
    const pathname = urlObj.pathname;

    // Reddit: /r/subreddit or /user/username
    if (
      urlObj.hostname.includes("reddit.com") ||
      url.toLowerCase().startsWith("r/")
    ) {
      const match = pathname.match(/\/r\/([^\/]+)/);
      if (match) return match[1];
      // Handle r/subreddit format without URL
      const shortMatch = url.match(/^r\/([^\/\s]+)/i);
      if (shortMatch) return shortMatch[1];
    }

    // YouTube: /channel/id or /@handle or /c/customurl
    if (
      urlObj.hostname.includes("youtube.com") ||
      urlObj.hostname.includes("youtu.be")
    ) {
      const handleMatch = pathname.match(/\/@([^\/]+)/);
      if (handleMatch) return handleMatch[1];
      const channelMatch = pathname.match(/\/channel\/([^\/]+)/);
      if (channelMatch) return channelMatch[1];
      const customMatch = pathname.match(/\/c\/([^\/]+)/);
      if (customMatch) return customMatch[1];
    }

    // Twitter/X: /username
    if (
      urlObj.hostname.includes("twitter.com") ||
      urlObj.hostname.includes("x.com")
    ) {
      const match = pathname.match(/\/([^\/]+)/);
      if (match && !["home", "explore", "notifications", "messages"].includes(match[1])) {
        return match[1];
      }
    }

    // Instagram: /username
    if (urlObj.hostname.includes("instagram.com")) {
      const match = pathname.match(/\/([^\/]+)/);
      if (match && !["explore", "reels", "stories", "p", "reel"].includes(match[1])) {
        return match[1];
      }
    }

    // TikTok: /@username
    if (urlObj.hostname.includes("tiktok.com")) {
      const match = pathname.match(/\/@([^\/]+)/);
      if (match) return match[1];
    }

    return null;
  } catch {
    return null;
  }
}
