import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { mysql2 } from "drizzle-orm/mysql2";
import mysql from "mysql2/promise";
import { createClient as createRedisClient } from "ioredis";
import * as schema from "./db/schema/auth";

// MySQL connection pool with optimizations
const pool = mysql.createPool({
  host: process.env.MYSQL_HOST || "localhost",
  user: process.env.MYSQL_USER || "root",
  password: process.env.MYSQL_PASSWORD || "betterauth",
  database: process.env.MYSQL_DATABASE || "bunny_auth",
  waitForConnections: true,
  connectionLimit: 20, // Increase connection pool
  queueLimit: 0,
  enableKeepAlive: true,
  keepAliveInitialDelay: 0,
});

// Redis client for session caching
let redisClient: ReturnType<typeof createRedisClient> | null = null;

function getRedisClient() {
  if (!redisClient && process.env.REDIS_URL) {
    redisClient = createRedisClient(process.env.REDIS_URL, {
      maxRetriesPerRequest: 3,
      retryStrategy(times) {
        const delay = Math.min(times * 50, 2000);
        return delay;
      },
    });
  }
  return redisClient;
}

// Drizzle instance
export const db = drizzle(pool, {
  schema: {
    ...schema,
  },
});

// Better Auth with MySQL + Redis + Performance optimizations
export const auth = betterAuth({
  database: drizzleAdapter(db, {
    provider: "mysql",
    schema: {
      ...schema,
    },
  }),
  baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3000",
  secret: process.env.BETTER_AUTH_SECRET || "your-production-secret-min-32-chars-please-change",
  emailAndPassword: {
    enabled: true,
  },
  session: {
    cookieCache: {
      enabled: process.env.REDIS_URL ? true : false,
      maxAge: 15 * 60, // 15 minutes cache (longer for better UX)
      redis: getRedisClient() || undefined,
    },
    expiresIn: 60 * 60 * 24 * 7, // 7 days
  },
  rateLimit: {
    enabled: true,
    window: 15, // 15 seconds
    max: 10, // 10 requests per window
  },
});
