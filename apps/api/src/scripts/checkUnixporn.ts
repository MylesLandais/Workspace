import "dotenv/config";
import { getSession } from "../neo4j/driver.js";

async function main() {
  const session = getSession();

  try {
    // First, check all subreddits to see what exists
    const allSubs = await session.run(`
      MATCH (s:Subreddit)
      RETURN s.name as name, count((s)<-[:POSTED_IN]-(:Post)) as postCount
      ORDER BY postCount DESC
      LIMIT 20
    `);

    console.log(`\n📋 All Subreddits in Neo4j:`);
    allSubs.records.forEach((r) => {
      console.log(
        `   - ${r.get("name")}: ${r.get("postCount").toNumber()} posts`,
      );
    });

    // Check for r/unixporn specifically
    const unixpornQuery = `
      MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
      WHERE s.name = 'r/unixporn' OR s.name = 'unixporn'
      RETURN count(p) as count
    `;

    const result = await session.run(unixpornQuery);
    const count = result.records[0]?.get("count")?.toNumber() || 0;

    console.log(`\n📊 Unixporn Posts in Neo4j:`);
    console.log(`   Total posts: ${count}`);

    // Check posts with media
    const mediaQuery = `
      MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
      WHERE (s.name = 'r/unixporn' OR s.name = 'unixporn')
      AND p.media_url IS NOT NULL
      RETURN count(p) as count
    `;

    const mediaResult = await session.run(mediaQuery);
    const mediaCount = mediaResult.records[0]?.get("count")?.toNumber() || 0;

    console.log(`   Posts with media_url: ${mediaCount}`);

    // Check subreddit name variations
    const subredditCheck = `
      MATCH (s:Subreddit)
      WHERE s.name CONTAINS 'unixporn'
      RETURN s.name as name, count((s)<-[:POSTED_IN]-(:Post)) as postCount
    `;

    const subResult = await session.run(subredditCheck);
    console.log(`\n📋 Subreddit variations found:`);
    subResult.records.forEach((r) => {
      console.log(
        `   - ${r.get("name")}: ${r.get("postCount").toNumber()} posts`,
      );
    });

    // Sample posts
    const sampleQuery = `
      MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
      WHERE s.name = 'r/unixporn' OR s.name = 'unixporn'
      RETURN p.id as id, p.title as title, p.media_url as mediaUrl
      ORDER BY p.created_utc DESC
      LIMIT 5
    `;

    const sampleResult = await session.run(sampleQuery);
    if (sampleResult.records.length > 0) {
      console.log(`\n📝 Sample posts:`);
      sampleResult.records.forEach((r, i) => {
        const title = r.get("title") || "No title";
        const mediaUrl = r.get("mediaUrl") ? "✓" : "✗";
        console.log(
          `   ${i + 1}. [${mediaUrl} media] ${title.substring(0, 60)}...`,
        );
      });
    }
  } finally {
    await session.close();
    process.exit(0);
  }
}

main().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
