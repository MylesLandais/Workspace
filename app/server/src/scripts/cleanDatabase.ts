import "dotenv/config";
import { getSession } from "../neo4j/driver.js";

async function main() {
  const session = getSession();

  try {
    console.log("Cleaning Neo4j database...");

    await session.run("MATCH (n) DETACH DELETE n");

    console.log("Neo4j cleaned");
    console.log("Database cleanup complete");
  } finally {
    await session.close();
    process.exit(0);
  }
}

main().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
