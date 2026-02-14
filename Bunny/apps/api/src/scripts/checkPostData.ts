import "dotenv/config";
import { getSession } from "../neo4j/driver.js";

async function main() {
  const session = getSession();

  try {
    const mediaResult = await session.run(
      "MATCH (m:Media) RETURN count(m) as count",
    );
    console.log("Media nodes:", mediaResult.records[0].get("count").toNumber());

    const postResult = await session.run(
      "MATCH (p:Post) RETURN count(p) as count",
    );
    console.log("Post nodes:", postResult.records[0].get("count").toNumber());

    const subredditResult = await session.run(
      "MATCH (s:Subreddit) RETURN count(s) as count",
    );
    console.log(
      "Subreddit nodes:",
      subredditResult.records[0].get("count").toNumber(),
    );

    const clusterResult = await session.run(
      "MATCH (c:ImageCluster) RETURN count(c) as count",
    );
    console.log(
      "Image clusters:",
      clusterResult.records[0].get("count").toNumber(),
    );

    // Check specific subreddits
    const specificSubs = await session.run(`
      MATCH (s:Subreddit)
      WHERE s.name IN ['unixporn', 'mechanicalkeyboards']
      RETURN s.name as name, count((s)<-[:POSTED_IN]-(:Post)) as postCount
    `);
    console.log("\nSpecific subreddits:");
    specificSubs.records.forEach((r) =>
      console.log(
        `  - r/${r.get("name")}: ${r.get("postCount").toNumber()} posts`,
      ),
    );

    // Sample post structure
    const samplePost = await session.run(`
      MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
      RETURN p.title as title, s.name as subreddit, p.created_utc as created_utc
      LIMIT 3
    `);
    console.log("\nSample posts:");
    samplePost.records.forEach((r) =>
      console.log(
        `  - [r/${r.get("subreddit")}] ${r.get("title")} (created: ${r.get("created_utc")})`,
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
