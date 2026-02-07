import { NextRequest, NextResponse } from "next/server";
import { decodeHtmlEntities } from "@/lib/utils";

interface OPMLFeed {
  title: string;
  xmlUrl: string;
  htmlUrl?: string;
  category?: string;
  description?: string;
}

interface OPMLParseResult {
  feeds: OPMLFeed[];
  feedCount: number;
  categories: string[];
  errors: string[];
}

/**
 * POST /api/sources/import-opml
 * Accepts an OPML file upload and returns parsed feeds for preview
 */
export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    // Validate file type
    const fileName = file.name.toLowerCase();
    if (!fileName.endsWith(".opml") && !fileName.endsWith(".xml")) {
      return NextResponse.json(
        { error: "Invalid file type. Please upload an OPML or XML file." },
        { status: 400 },
      );
    }

    // Read file content
    const content = await file.text();

    if (!content.includes("<opml") && !content.includes("<outline")) {
      return NextResponse.json(
        { error: "Invalid OPML format" },
        { status: 400 },
      );
    }

    // Parse OPML content
    const result = parseOPMLContent(content);

    return NextResponse.json(result);
  } catch (error) {
    console.error("OPML import error:", error);
    return NextResponse.json(
      { error: "Failed to parse OPML file" },
      { status: 500 },
    );
  }
}

/**
 * Parse OPML content and extract RSS feed information
 */
function parseOPMLContent(xml: string): OPMLParseResult {
  const feeds: OPMLFeed[] = [];
  const categories = new Set<string>();
  const errors: string[] = [];

  try {
    // Parse with proper category nesting
    const bodyMatch = xml.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
    if (bodyMatch) {
      parseOutlineLevel(bodyMatch[1], "", feeds, categories);
    } else {
      // Fallback: extract all outline elements with xmlUrl
      const outlineRegex = /<outline[^>]*>/gi;
      const matches = xml.match(outlineRegex) || [];

      for (const match of matches) {
        const xmlUrl = extractAttribute(match, "xmlUrl");
        if (xmlUrl) {
          const title =
            extractAttribute(match, "text") ||
            extractAttribute(match, "title") ||
            "Untitled Feed";

          feeds.push({
            title: decodeHtmlEntities(title),
            xmlUrl: decodeHtmlEntities(xmlUrl),
            htmlUrl: extractAttribute(match, "htmlUrl") || undefined,
            description: extractAttribute(match, "description") || undefined,
          });
        }
      }
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

function parseOutlineLevel(
  content: string,
  parentCategory: string,
  feeds: OPMLFeed[],
  categories: Set<string>,
): void {
  const outlineRegex = /<outline\s+([^>]*)(?:\/>|>)/gi;
  let match: RegExpExecArray | null;

  while ((match = outlineRegex.exec(content)) !== null) {
    const tagStr = match[0];
    const isSelfClosing = tagStr.endsWith("/>");
    const xmlUrl = extractAttribute(tagStr, "xmlUrl");

    if (xmlUrl) {
      // This is a feed
      const title =
        extractAttribute(tagStr, "text") ||
        extractAttribute(tagStr, "title") ||
        "Untitled Feed";
      const htmlUrl = extractAttribute(tagStr, "htmlUrl");
      const description = extractAttribute(tagStr, "description");

      feeds.push({
        title: decodeHtmlEntities(title),
        xmlUrl: decodeHtmlEntities(xmlUrl),
        htmlUrl: htmlUrl ? decodeHtmlEntities(htmlUrl) : undefined,
        category: parentCategory || undefined,
        description: description ? decodeHtmlEntities(description) : undefined,
      });
    } else if (!isSelfClosing) {
      // This is a category folder
      const text = extractAttribute(tagStr, "text");
      const category = text ? decodeHtmlEntities(text) : parentCategory;

      if (category && category !== parentCategory) {
        categories.add(category);
      }

      // Find closing tag and process children
      const startPos = match.index + tagStr.length;
      const closingPos = findMatchingClosingTag(content, startPos);

      if (closingPos > startPos) {
        const innerContent = content.substring(startPos, closingPos);
        parseOutlineLevel(innerContent, category, feeds, categories);
      }
    }
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

function extractAttribute(tag: string, name: string): string | null {
  const doubleQuoteRegex = new RegExp(`${name}\\s*=\\s*"([^"]*)"`, "i");
  const singleQuoteRegex = new RegExp(`${name}\\s*=\\s*'([^']*)'`, "i");

  const doubleMatch = tag.match(doubleQuoteRegex);
  if (doubleMatch) return doubleMatch[1];

  const singleMatch = tag.match(singleQuoteRegex);
  if (singleMatch) return singleMatch[1];

  return null;
}
