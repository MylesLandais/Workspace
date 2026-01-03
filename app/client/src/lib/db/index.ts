import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";
import * as authSchema from "./schema/auth";

/**
 * Global database state used to maintain a single connection across 
 * Hot Module Replacement (HMR) in development mode.
 */
const globalForDb = globalThis as unknown as {
  __BUNNY_DB_CLIENT__: ReturnType<typeof createClient> | undefined;
  __BUNNY_DB_DRIZZLE__: ReturnType<typeof drizzle> | undefined;
};

/**
 * Initialize the LibSQL client with WAL mode optimization.
 */
if (!globalForDb.__BUNNY_DB_CLIENT__) {
  globalForDb.__BUNNY_DB_CLIENT__ = createClient({
    url: "file:/app/.local/db/bunny-auth.db",
  });
  
  // Enable WAL mode for performance in Docker environments
  try {
     globalForDb.__BUNNY_DB_CLIENT__.execute("PRAGMA journal_mode = WAL;");
     globalForDb.__BUNNY_DB_CLIENT__.execute("PRAGMA synchronous = NORMAL;");
     console.log("Database initialized with WAL mode (Persistent)");
  } catch (e) {
     console.error("Failed to set WAL mode:", e);
  }
}

/**
 * Initialize Drizzle ORM.
 */
if (!globalForDb.__BUNNY_DB_DRIZZLE__) {
  globalForDb.__BUNNY_DB_DRIZZLE__ = drizzle(globalForDb.__BUNNY_DB_CLIENT__, {
    schema: {
      ...authSchema,
    },
  });
}

/**
 * Shared database instance used throughout the app server-side.
 */
export const db = globalForDb.__BUNNY_DB_DRIZZLE__!;

/**
 * Helper function to retrieve the database instance.
 */
export function getDb() {
  return db;
}

export type DatabaseType = typeof db;
