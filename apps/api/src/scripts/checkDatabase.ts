import "dotenv/config";
import { getSession } from "../neo4j/driver.js";

async function main() {
  const session = getSession();

  try {
    const mediaResult = await session.run(
      "MATCH (m:Media) RETURN count(m) as count",
    );
    console.log("Media nodes:", mediaResult.records[0].get("count").toNumber());

    const clusterResult = await session.run(
      "MATCH (c:ImageCluster) RETURN count(c) as count",
    );
    console.log(
      "Image clusters:",
      clusterResult.records[0].get("count").toNumber(),
    );

    const postResult = await session.run(
      "MATCH (p:Post) RETURN count(p) as count",
    );
    console.log("Post nodes:", postResult.records[0].get("count").toNumber());

    const sampleMedia = await session.run(`
      MATCH (m:Media)
      RETURN m.id as id, m.url as url, m.sha256 as sha256
      LIMIT 3
    `);

    console.log("\nSample Media nodes:");
    sampleMedia.records.forEach((record) => {
      console.log(`  ID: ${record.get("id")}`);
      console.log(`  SHA256: ${record.get("sha256").substring(0, 16)}...`);
      console.log(`  URL: ${record.get("url").substring(0, 80)}...`);
      console.log("");
    });
  } finally {
    await session.close();
    process.exit(0);
  }
}

main().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
