/**
 * MySQL database connection for Better Auth.
 *
 * Uses mysql2/promise with connection pooling for performance.
 * Drizzle ORM provides type-safe queries.
 */
import { drizzle } from "drizzle-orm/mysql2";
import * as mysql from "mysql2/promise";
import type { PoolOptions, Pool } from "mysql2/promise";
import * as Sentry from "@sentry/nextjs";
import * as authSchema from "./schema/mysql-auth";

const isServer = typeof window === "undefined";

function log(
  level: "info" | "warn" | "error",
  message: string,
  meta?: Record<string, unknown>,
  error?: Error,
) {
  if (!isServer) return;
  const prefix = `[mysql] ${level.toUpperCase()}:`;
  const metaStr = meta ? ` ${JSON.stringify(meta)}` : "";
  if (level === "error") {
    console.error(`${prefix} ${message}${metaStr}`);
    // Report errors to Sentry with context
    if (error) {
      Sentry.captureException(error, {
        tags: { component: "mysql", operation: "connection" },
        extra: meta,
      });
    } else {
      Sentry.captureMessage(`MySQL: ${message}`, {
        level: "error",
        tags: { component: "mysql" },
        extra: meta,
      });
    }
  } else if (level === "warn") {
    console.warn(`${prefix} ${message}${metaStr}`);
  } else {
    console.log(`${prefix} ${message}${metaStr}`);
  }
}

const poolConfig: PoolOptions = {
  host: process.env.MYSQL_HOST,
  port: process.env.MYSQL_PORT ? parseInt(process.env.MYSQL_PORT, 10) : 3306,
  user: process.env.MYSQL_USER,
  password: process.env.MYSQL_PASSWORD,
  database: process.env.MYSQL_DATABASE,
  waitForConnections: true,
  connectionLimit: 20,
  queueLimit: 0,
  enableKeepAlive: true,
  keepAliveInitialDelay: 0,
};

// Prefer socket connection if available (common in Nix/devenv)
if (process.env.MYSQL_UNIX_PORT) {
  poolConfig.socketPath = process.env.MYSQL_UNIX_PORT;
}

// Log configuration on module load (server-side only, no password)
if (isServer) {
  const configSummary = {
    host: poolConfig.host || "(not set)",
    port: poolConfig.port,
    user: poolConfig.user || "(not set)",
    database: poolConfig.database || "(not set)",
    socketPath: poolConfig.socketPath,
  };

  if (!poolConfig.host && !poolConfig.socketPath) {
    log("error", "MYSQL_HOST not configured", configSummary);
  } else if (!poolConfig.user) {
    log("error", "MYSQL_USER not configured", configSummary);
  } else if (!poolConfig.database) {
    log("error", "MYSQL_DATABASE not configured", configSummary);
  } else {
    log("info", "Initializing connection pool", configSummary);
  }
}

const pool: Pool = mysql.createPool(poolConfig);

// Attach error listener to catch connection failures
pool.on("connection", () => {
  log("info", "New connection established");
});

/**
 * Test the database connection and return status.
 * Use this for health checks and startup validation.
 */
export async function checkConnection(): Promise<{
  connected: boolean;
  error?: string;
  latencyMs?: number;
}> {
  const start = Date.now();
  try {
    const conn = await pool.getConnection();
    await conn.query("SELECT 1");
    conn.release();
    const latencyMs = Date.now() - start;
    log("info", "Health check passed", { latencyMs });
    return { connected: true, latencyMs };
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err));
    log("error", "Health check failed", { error: error.message }, error);
    return { connected: false, error: error.message };
  }
}

/**
 * Wrapper for database operations with connection error handling.
 * Provides clear error messages when the database is unavailable.
 */
export async function withDbConnection<T>(
  operation: () => Promise<T>,
  context?: string,
): Promise<T> {
  try {
    return await operation();
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err));
    const isConnectionError =
      error.message.includes("ECONNREFUSED") ||
      error.message.includes("Access denied") ||
      error.message.includes("ER_ACCESS_DENIED_ERROR") ||
      error.message.includes("ETIMEDOUT") ||
      error.message.includes("ENOTFOUND");

    if (isConnectionError) {
      log(
        "error",
        "Database connection failed",
        {
          context,
          error: error.message,
          host: poolConfig.host,
          port: poolConfig.port,
          database: poolConfig.database,
        },
        error,
      );
      throw new Error(
        `Database connection failed: ${error.message}. ` +
          `Check MYSQL_HOST (${poolConfig.host}), MYSQL_PORT (${poolConfig.port}), ` +
          `MYSQL_USER, MYSQL_PASSWORD, and MYSQL_DATABASE (${poolConfig.database}) env vars.`,
      );
    }
    throw error;
  }
}

export const mysqlDb = drizzle(pool, {
  schema: authSchema,
  mode: "default",
});

export type MySQLDatabase = typeof mysqlDb;
export { pool };
