import "dotenv/config";
import { readFileSync } from "fs";
import { getSession, createIndexes } from "../neo4j/driver.js";
import neo4j from "neo4j-driver";

interface RedditPostJson {
  id: string;
  title: string;
  created_utc: string;
  score: number;
  num_comments: number;
  author: string;
  is_image: boolean;
  url: string;
  image_url: string;
  permalink: string;
  over_18: boolean;
  upvote_ratio: number;
}

interface DataFile {
  subreddit: string;
  posts: RedditPostJson[];
}

async function ingestPost(post: RedditPostJson, subreddit: string) {
  const session = getSession();

  const createdUtc = neo4j.types.DateTime.fromStandardDate(
    new Date(post.created_utc),
  );

  const query = `
    MERGE (s:Subreddit {name: $subreddit})
    ON CREATE SET s.displayName = $subreddit, s.createdAt = datetime()

    MERGE (p:Post {id: $postId})
    ON CREATE SET
      p.title = $title,
      p.url = $permalink,
      p.author = $author,
      p.created_utc = $createdUtc,
      p.score = $score,
      p.num_comments = $numComments,
      p.is_image = $isImage,
      p.image_url = $imageUrl,
      p.over_18 = $over18,
      p.upvote_ratio = $upvoteRatio

    MERGE (p)-[:POSTED_IN]->(s)
    RETURN p.id
  `;

  const params = {
    postId: post.id,
    subreddit,
    title: post.title,
    permalink: post.permalink,
    author: post.author,
    createdUtc,
    score: post.score,
    numComments: post.num_comments,
    isImage: post.is_image,
    imageUrl: post.image_url || post.url,
    over18: post.over_18 || false,
    upvoteRatio: post.upvote_ratio || 0.95,
  };

  try {
    await session.run(query, params);
    console.log(`Ingested: ${post.id} - ${post.title.slice(0, 50)}...`);
  } catch (error) {
    console.error(`Error ingesting post ${post.id}:`, error);
  } finally {
    await session.close();
  }
}

async function main() {
  const filePath =
    process.argv[2] ||
    "../../../app/client/public/parquet-cache/unixporn_posts.json";

  console.log(`Reading data from ${filePath}...`);

  let data: DataFile;
  try {
    const content = readFileSync(filePath, "utf-8");
    data = JSON.parse(content);
  } catch (error) {
    console.error("Failed to read data file:", error);
    process.exit(1);
  }

  console.log(`Found ${data.posts.length} posts from r/${data.subreddit}`);

  // Create indexes first
  await createIndexes();

  // Ingest each post
  for (const post of data.posts) {
    await ingestPost(post, data.subreddit);
  }

  console.log("\nIngestion complete!");

  // Verify
  const session = getSession();
  const result = await session.run(
    "MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit) RETURN s.name as subreddit, count(p) as count",
  );
  console.log("\nPost counts by subreddit:");
  for (const record of result.records) {
    console.log(
      `  r/${record.get("subreddit")}: ${record.get("count").toNumber()} posts`,
    );
  }
  await session.close();

  process.exit(0);
}

main();
