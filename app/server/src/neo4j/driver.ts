import neo4j from 'neo4j-driver';
import dotenv from 'dotenv';

dotenv.config();

const uri = process.env.NEO4J_URI || '';
const username = process.env.NEO4J_USERNAME || 'neo4j';
const password = process.env.NEO4J_PASSWORD || '';
const database = process.env.NEO4J_DATABASE || 'neo4j';

if (!uri || !password) {
  throw new Error('Missing Neo4j connection credentials. Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD');
}

export const driver = neo4j.driver(uri, neo4j.auth.basic(username, password), {
  maxConnectionLifetime: 3 * 60 * 60 * 1000,
  maxConnectionPoolSize: 50,
  connectionAcquisitionTimeout: 2 * 60 * 1000,
});

export async function verifyConnection() {
  const session = driver.session({ database });
  try {
    await session.run('RETURN 1 as test');
    console.log('Neo4j connection verified');
    return true;
  } catch (error) {
    console.error('Failed to connect to Neo4j:', error);
    throw error;
  } finally {
    await session.close();
  }
}

export async function createIndexes() {
  const session = driver.session({ database });
  try {
    const indexes = [
      'CREATE INDEX post_created_utc IF NOT EXISTS FOR (p:Post) ON (p.created_utc)',
      'CREATE INDEX post_is_image IF NOT EXISTS FOR (p:Post) ON (p.is_image)',
      'CREATE CONSTRAINT post_id_unique IF NOT EXISTS FOR (p:Post) REQUIRE p.id IS UNIQUE',
      'CREATE CONSTRAINT subreddit_name_unique IF NOT EXISTS FOR (s:Subreddit) REQUIRE s.name IS UNIQUE',
      'CREATE CONSTRAINT source_id_unique IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE',
      'CREATE INDEX source_subreddit_name IF NOT EXISTS FOR (s:Source) ON (s.subreddit_name)',
      'CREATE CONSTRAINT feedgroup_id_unique IF NOT EXISTS FOR (fg:FeedGroup) REQUIRE fg.id IS UNIQUE',
      'CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE',
      'CREATE INDEX media_sha256 IF NOT EXISTS FOR (m:Media) ON (m.sha256)',
      'CREATE INDEX media_phash IF NOT EXISTS FOR (m:Media) ON (m.phash)',
      'CREATE INDEX cluster_canonical IF NOT EXISTS FOR (c:ImageCluster) ON (c.canonical_sha256)',
      'CREATE CONSTRAINT cluster_id_unique IF NOT EXISTS FOR (c:ImageCluster) REQUIRE c.id IS UNIQUE',
      // Bunny schema extensions
      'CREATE CONSTRAINT savedboard_id_unique IF NOT EXISTS FOR (sb:SavedBoard) REQUIRE sb.id IS UNIQUE',
      'CREATE INDEX savedboard_user_id IF NOT EXISTS FOR (sb:SavedBoard) ON (sb.userId)',
      'CREATE INDEX savedboard_created_at IF NOT EXISTS FOR (sb:SavedBoard) ON (sb.createdAt)',
      'CREATE INDEX entity_aliases IF NOT EXISTS FOR (e:Entity) ON (e.aliases)',
      'CREATE INDEX source_label IF NOT EXISTS FOR (s:Source) ON (s.label)',
      'CREATE INDEX source_hidden IF NOT EXISTS FOR (s:Source) ON (s.hidden)',
    ];

    for (const query of indexes) {
      try {
        await session.run(query);
      } catch (error: any) {
        if (!error.message.includes('already exists')) {
          console.warn(`Index creation warning: ${error.message}`);
        }
      }
    }
    console.log('Database indexes and constraints created');
  } catch (error) {
    console.error('Failed to create indexes:', error);
    throw error;
  } finally {
    await session.close();
  }
}

export function getSession() {
  return driver.session({ database });
}


