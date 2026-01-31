import "dotenv/config";
import { getSession } from "../neo4j/driver.js";

async function main() {
  const session = getSession();

  try {
    const result = await session.run(`
      MATCH (m:Media)
      RETURN m.sha256 as sha256, m.storage_path as storagePath, m.mime_type as mimeType
      LIMIT 10
    `);

    console.log("Media storage paths:");
    result.records.forEach((record) => {
      console.log("  SHA256:", record.get("sha256").substring(0, 16) + "...");
      console.log("  Storage Path:", record.get("storagePath"));
      console.log("  MIME Type:", record.get("mimeType"));
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
