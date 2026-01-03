import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";
import * as authSchema from "./schema/auth";

let dbInstance: ReturnType<typeof drizzle> | null = null;

export function getDb() {
  if (!dbInstance) {
    const start = Date.now();
    const client = createClient({
      url: "file:/app/.local/db/bunny-auth.db",
    });
    dbInstance = drizzle(client, {
      schema: {
        ...authSchema,
      },
    });
    console.log(`[DB] New connection created in ${Date.now() - start}ms`);
  }
  return dbInstance;
}

export const db = getDb();

export type DatabaseType = typeof db;
