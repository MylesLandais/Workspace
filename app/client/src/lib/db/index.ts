import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";
import * as authSchema from "./schema/auth";

/**
 * Global database state used to maintain a single connection across 
 * Hot Module Replacement (HMR) in development mode.
 */
const globalForDb = global as unknown as {
  client: ReturnType<typeof createClient> | undefined;
  db: ReturnType<typeof drizzle> | undefined;
};

/**
 * Initialize the LibSQL client.
 * We use @libsql/client because it is compatible with the Bun runtime 
 * and provides better stability for Next.js 15 route handlers than 
 * native C++ drivers in some environments.
 */
if (!globalForDb.client) {
  globalForDb.client = createClient({
    url: "file:/app/.local/db/bunny-auth.db",
  });
}

/**
 * Initialize Drizzle ORM.
 */
if (!globalForDb.db) {
  globalForDb.db = drizzle(globalForDb.client, {
    schema: {
      ...authSchema,
    },
  });
}

/**
 * Shared database instance used throughout the app server-side.
 */
export const db = globalForDb.db!;

/**
 * Helper function to retrieve the database instance.
 */
export function getDb() {
  return db;
}

export type DatabaseType = typeof db;
