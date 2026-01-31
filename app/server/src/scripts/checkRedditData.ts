import "dotenv/config";
import { getSession } from "../neo4j/driver.js";

async function main() {
  const session = getSession();

  try {
    // Check Post nodes
    const postCount = await session.run(
      "MATCH (p:Post) RETURN count(p) as count",
    );
    console.log("Post nodes:", postCount.records[0].get("count").toNumber());

    // Check Subreddit nodes
    const subredditCount = await session.run(
      "MATCH (s:Subreddit) RETURN count(s) as count",
    );
    console.log(
      "Subreddit nodes:",
      subredditCount.records[0].get("count").toNumber(),
    );

    // Check specific subreddits
    const subreddits = await session.run(
      "MATCH (s:Subreddit) RETURN s.name as name LIMIT 10",
    );
    console.log("\nSubreddits found:");
    subreddits.records.forEach((r) => console.log("  -", r.get("name")));

    // Check posts with subreddit relationship
    const postWithSub = await session.run(`
      MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
      RETURN s.name as subreddit, count(p) as count
      ORDER BY count DESC
      LIMIT 5
    `);
    console.log("\nPosts by subreddit:");
    postWithSub.records.forEach((r) =>
      console.log(`  - ${r.get("subreddit")}: ${r.get("count").toNumber()}`),
    );

    // Sample post
    const sample = await session.run(`
      MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
      RETURN p.title as title, s.name as subreddit, p.author as author
      LIMIT 3
    `);
    console.log("\nSample posts:");
    sample.records.forEach((r) =>
      console.log(
        `  - [r/${r.get("subreddit")}] ${r.get("title")} by ${r.get("author")}`,
      ),
    );
  } finally {
    await session.close();
    process.exit(0);
  }
}

main().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
