import "dotenv/config";
import { readFileSync, existsSync } from "fs";
import { withSession } from "../lib/session.js";
import { createIndexes } from "../neo4j/driver.js";
import neo4j from "neo4j-driver";

interface UnixpornPostJson {
  id: string;
  title: string;
  subreddit: string;
  url: string;
  permalink: string;
  score: number;
  num_comments: number;
  created_utc: string;
  selftext?: string;
  local_media_path?: string | null;
  media_url?: string | null;
}

/**
 * Syncs unixporn posts from JSON file to Neo4j
 * Handles media_url from MinIO and updates Post nodes accordingly
 */
async function syncPost(post: UnixpornPostJson) {
  return withSession(async (session) => {
    const createdUtc = neo4j.types.DateTime.fromStandardDate(
      new Date(post.created_utc),
    );

    // Extract file extension from media_url if available
    let mediaMimeType: string | null = null;
    if (post.media_url) {
      const ext = post.media_url.split(".").pop()?.toLowerCase();
      if (ext === "mp4" || ext === "webm") {
        mediaMimeType = `video/${ext === "webm" ? "webm" : "mp4"}`;
      } else if (ext === "jpg" || ext === "jpeg") {
        mediaMimeType = "image/jpeg";
      } else if (ext === "png") {
        mediaMimeType = "image/png";
      } else if (ext === "gif") {
        mediaMimeType = "image/gif";
      }
    }

    // Determine if post has media
    const hasMedia = !!post.media_url;

    const query = `
      MERGE (s:Subreddit {name: $subreddit})
      ON CREATE SET 
        s.displayName = $subreddit, 
        s.createdAt = datetime()

      MERGE (p:Post {id: $postId})
      ON CREATE SET
        p.title = $title,
        p.url = $url,
        p.permalink = $permalink,
        p.author = $author,
        p.created_utc = $createdUtc,
        p.score = $score,
        p.num_comments = $numComments,
        p.selftext = $selftext,
        p.over_18 = $over18,
        p.upvote_ratio = $upvoteRatio,
        p.is_image = $hasMedia,
        p.image_url = $imageUrl,
        p.media_url = $mediaUrl,
        p.media_mime_type = $mediaMimeType,
        p.synced_at = datetime()
      ON MATCH SET
        p.title = $title,
        p.score = $score,
        p.num_comments = $numComments,
        p.media_url = COALESCE($mediaUrl, p.media_url),
        p.media_mime_type = COALESCE($mediaMimeType, p.media_mime_type),
        p.is_image = $hasMedia,
        p.synced_at = datetime()

      MERGE (p)-[:POSTED_IN]->(s)
      RETURN p.id as id, p.media_url as mediaUrl
    `;

    const params = {
      postId: post.id,
      subreddit: post.subreddit || "r/unixporn",
      title: post.title,
      url: post.url,
      permalink: post.permalink,
      author: null, // Not in JSON, can be added later
      createdUtc,
      score: post.score || 0,
      numComments: post.num_comments || 0,
      selftext: post.selftext || null,
      over18: false,
      upvoteRatio: 0.95,
      hasMedia,
      imageUrl: post.media_url || post.url || null,
      mediaUrl: post.media_url || null,
      mediaMimeType,
    };

    try {
      const result = await session.run(query, params);
      const record = result.records[0];
      return {
        id: record.get("id"),
        mediaUrl: record.get("mediaUrl"),
      };
    } catch (error) {
      console.error(`Error syncing post ${post.id}:`, error);
      throw error;
    }
  });
}

async function main() {
  // Default to jupyter data directory
  const defaultPath =
    process.argv[2] ||
    "/home/warby/Workspace/jupyter/data/unixporn_latest.json";

  console.log(`Reading unixporn posts from: ${defaultPath}`);

  if (!existsSync(defaultPath)) {
    console.error(`File not found: ${defaultPath}`);
    console.error(
      "Usage: bun run syncUnixpornPosts.ts [path-to-unixporn_latest.json]",
    );
    process.exit(1);
  }

  let posts: UnixpornPostJson[];
  try {
    const content = readFileSync(defaultPath, "utf-8");
    posts = JSON.parse(content);
  } catch (error) {
    console.error("Failed to read or parse data file:", error);
    process.exit(1);
  }

  console.log(`Found ${posts.length} posts to sync`);

  // Create indexes first
  await createIndexes();

  // Sync posts
  let synced = 0;
  let withMedia = 0;
  let errors = 0;

  for (const post of posts) {
    try {
      const result = await syncPost(post);
      synced++;
      if (result.mediaUrl) {
        withMedia++;
      }
      if (synced % 10 === 0) {
        console.log(`Synced ${synced}/${posts.length} posts...`);
      }
    } catch (error) {
      errors++;
      console.error(`Failed to sync post ${post.id}:`, error);
    }
  }

  console.log("\n=== Sync Complete ===");
  console.log(`Total posts: ${posts.length}`);
  console.log(`Synced: ${synced}`);
  console.log(`With media: ${withMedia}`);
  console.log(`Errors: ${errors}`);

  // Verify
  await withSession(async (session) => {
    const result = await session.run(
      `MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $subreddit})
       RETURN count(p) as count, 
              count(CASE WHEN p.media_url IS NOT NULL THEN 1 END) as withMedia`,
      { subreddit: "r/unixporn" },
    );
    const record = result.records[0];
    console.log(`\nNeo4j stats for r/unixporn:`);
    console.log(`  Total posts: ${record.get("count").toNumber()}`);
    console.log(`  Posts with media: ${record.get("withMedia").toNumber()}`);
  });

  process.exit(0);
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
