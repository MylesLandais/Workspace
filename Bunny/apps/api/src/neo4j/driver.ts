import neo4j from "neo4j-driver";
import dotenv from "dotenv";
import path from "path";
import logger from "../lib/logger.js";

// Resolve path to project root .env file
const projectRoot = path.resolve(process.cwd(), "..", "..");
dotenv.config({ path: path.join(projectRoot, ".env") });

const uri = process.env.NEO4J_URI || "";
const username = process.env.NEO4J_USER || "neo4j";
const password = process.env.NEO4J_PASSWORD || "";
const database = process.env.NEO4J_DATABASE || "neo4j";

if (!uri || !password) {
  throw new Error(
    "Missing Neo4j connection credentials. Please set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD",
  );
}

export const driver = neo4j.driver(uri, neo4j.auth.basic(username, password), {
  maxConnectionLifetime: 3 * 60 * 60 * 1000,
  maxConnectionPoolSize: 50,
  connectionAcquisitionTimeout: 2 * 60 * 1000,
});

export async function verifyConnection() {
  const session = driver.session({ database });
  try {
    await session.run("RETURN 1 as test");
    logger.info("Neo4j connection verified");
    return true;
  } catch (error) {
    logger.error("Failed to connect to Neo4j", error);
    throw error;
  } finally {
    await session.close();
  }
}

export async function createIndexes() {
  const session = driver.session({ database });
  try {
    const indexes = [
      "CREATE INDEX post_created_utc IF NOT EXISTS FOR (p:Post) ON (p.created_utc)",
      "CREATE INDEX post_is_image IF NOT EXISTS FOR (p:Post) ON (p.is_image)",
      "CREATE CONSTRAINT post_id_unique IF NOT EXISTS FOR (p:Post) REQUIRE p.id IS UNIQUE",
      "CREATE CONSTRAINT subreddit_name_unique IF NOT EXISTS FOR (s:Subreddit) REQUIRE s.name IS UNIQUE",
      "CREATE CONSTRAINT source_id_unique IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE",
      "CREATE INDEX source_subreddit_name IF NOT EXISTS FOR (s:Source) ON (s.subreddit_name)",
      "CREATE CONSTRAINT feedgroup_id_unique IF NOT EXISTS FOR (fg:FeedGroup) REQUIRE fg.id IS UNIQUE",
      "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
      "CREATE INDEX media_sha256 IF NOT EXISTS FOR (m:Media) ON (m.sha256)",
      "CREATE INDEX media_phash IF NOT EXISTS FOR (m:Media) ON (m.phash)",
      "CREATE INDEX cluster_canonical IF NOT EXISTS FOR (c:ImageCluster) ON (c.canonical_sha256)",
      "CREATE CONSTRAINT cluster_id_unique IF NOT EXISTS FOR (c:ImageCluster) REQUIRE c.id IS UNIQUE",
      "CREATE CONSTRAINT identity_provider_unique IF NOT EXISTS FOR (i:Identity) REQUIRE (i.provider, i.provider_uid) IS UNIQUE",
      "CREATE INDEX identity_user_id IF NOT EXISTS FOR (i:Identity) ON (i.userId)",
      "CREATE INDEX identity_provider IF NOT EXISTS FOR (i:Identity) ON (i.provider)",
      "CREATE INDEX identity_provider_uid IF NOT EXISTS FOR (i:Identity) ON (i.provider_uid)",
      "CREATE CONSTRAINT session_id_unique IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE",
      "CREATE INDEX session_token IF NOT EXISTS FOR (s:Session) ON (s.token)",
      "CREATE INDEX session_user_id IF NOT EXISTS FOR (s:Session) ON (s.userId)",
      "CREATE INDEX session_expires_at IF NOT EXISTS FOR (s:Session) ON (s.expiresAt)",
      "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
      "CREATE INDEX user_email IF NOT EXISTS FOR (u:User) ON (u.email)",
      "CREATE INDEX user_handle IF NOT EXISTS FOR (u:User) ON (u.handle)",
      // Bunny schema extensions
      "CREATE CONSTRAINT savedboard_id_unique IF NOT EXISTS FOR (sb:SavedBoard) REQUIRE sb.id IS UNIQUE",
      "CREATE INDEX savedboard_user_id IF NOT EXISTS FOR (sb:SavedBoard) ON (sb.userId)",
      "CREATE INDEX savedboard_created_at IF NOT EXISTS FOR (sb:SavedBoard) ON (sb.createdAt)",
      "CREATE INDEX entity_aliases IF NOT EXISTS FOR (e:Entity) ON (e.aliases)",
      "CREATE INDEX source_label IF NOT EXISTS FOR (s:Source) ON (s.label)",
      "CREATE INDEX source_hidden IF NOT EXISTS FOR (s:Source) ON (s.hidden)",
      // Tag index for Source nodes
      "CREATE INDEX source_tags IF NOT EXISTS FOR (s:Source) ON (s.tags)",
      // Subscription system indexes
      "CREATE INDEX source_type_subreddit IF NOT EXISTS FOR (s:Source) ON (s.source_type, s.subreddit_name)",
      "CREATE INDEX source_type_youtube IF NOT EXISTS FOR (s:Source) ON (s.source_type, s.youtube_channel_handle)",
      "CREATE INDEX source_sync_status IF NOT EXISTS FOR (s:Source) ON (s.source_type, s.last_synced)",
      "CREATE INDEX subscribes_to_added IF NOT EXISTS FOR ()-[r:SUBSCRIBES_TO]->() ON (r.added_at)",
    ];

    for (const query of indexes) {
      try {
        await session.run(query);
      } catch (error: any) {
        if (!error.message.includes("already exists")) {
          logger.warn("Index creation warning", { message: error.message });
        }
      }
    }
    logger.info("Database indexes and constraints created");
  } catch (error) {
    logger.error("Failed to create indexes", error);
    throw error;
  } finally {
    await session.close();
  }
}

export function getSession() {
  return driver.session({ database });
}
