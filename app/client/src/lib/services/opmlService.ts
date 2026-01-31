/**
 * OPML Service
 *
 * Handles importing and exporting RSS feed lists via OPML format
 */

import { FeedNode } from "@/lib/types/dashboard";

export function parseOPML(opmlContent: string): FeedNode[] {
  try {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(opmlContent, "text/xml");

    const parseError = xmlDoc.querySelector("parsererror");
    if (parseError) {
      throw new Error("Invalid OPML format");
    }

    const outlines = xmlDoc.querySelectorAll("outline");
    const feeds: FeedNode[] = [];

    outlines.forEach((outline) => {
      const type = outline.getAttribute("type");
      const text =
        outline.getAttribute("text") ||
        outline.getAttribute("title") ||
        "Untitled";
      const xmlUrl = outline.getAttribute("xmlUrl");
      const htmlUrl = outline.getAttribute("htmlUrl");

      if (type === "rss" && xmlUrl) {
        feeds.push({
          id: `feed-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          title: text,
          type: "feed",
          url: xmlUrl,
        });
      } else if (!type && !xmlUrl) {
        // Folder
        const children: FeedNode[] = [];
        outline.querySelectorAll(":scope > outline").forEach((child) => {
          const childXmlUrl = child.getAttribute("xmlUrl");
          const childText =
            child.getAttribute("text") ||
            child.getAttribute("title") ||
            "Untitled";
          if (childXmlUrl) {
            children.push({
              id: `feed-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              title: childText,
              type: "feed",
              url: childXmlUrl,
            });
          }
        });

        if (children.length > 0) {
          feeds.push({
            id: `folder-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            title: text,
            type: "folder",
            isOpen: false,
            children,
          });
        }
      }
    });

    return feeds;
  } catch (error) {
    console.error("[OPML] Parse error:", error);
    throw error;
  }
}

export function exportOPML(
  feeds: FeedNode[],
  title: string = "Bunny Dashboard Feeds",
): string {
  const now = new Date().toUTCString();

  let opml = `<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>${escapeXml(title)}</title>
    <dateCreated>${now}</dateCreated>
    <dateModified>${now}</dateModified>
  </head>
  <body>
`;

  function buildOutlines(nodes: FeedNode[], indent: string = "    "): string {
    let result = "";

    for (const node of nodes) {
      if (node.type === "feed" && node.url) {
        result += `${indent}<outline type="rss" text="${escapeXml(node.title)}" xmlUrl="${escapeXml(node.url)}" />\n`;
      } else if (node.type === "folder" && node.children) {
        result += `${indent}<outline text="${escapeXml(node.title)}">\n`;
        result += buildOutlines(node.children, indent + "  ");
        result += `${indent}</outline>\n`;
      }
    }

    return result;
  }

  opml += buildOutlines(feeds);
  opml += `  </body>
</opml>`;

  return opml;
}

function escapeXml(unsafe: string): string {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export function downloadOPML(opml: string, filename: string = "feeds.opml") {
  const blob = new Blob([opml], { type: "application/xml" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function readOPMLFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      resolve(content);
    };
    reader.onerror = () => reject(new Error("Failed to read file"));
    reader.readAsText(file);
  });
}
