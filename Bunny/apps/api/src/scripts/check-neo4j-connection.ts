import "dotenv/config";
import { verifyConnection, driver } from "../neo4j/driver.js";

async function main() {
  console.log("Attempting to connect to Neo4j...");
  try {
    await verifyConnection();
    console.log("✅ Neo4j connection successful!");
  } catch (error: any) {
    console.error("❌ Neo4j connection failed:");
    console.error(error.message);
    process.exit(1);
  } finally {
    // Close the driver gracefully
    await driver.close();
  }
}

main();
