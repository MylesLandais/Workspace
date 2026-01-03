import { betterAuth } from "better-auth";
import { betterSqlite3 } from "better-sqlite3";
import { drizzle } from "drizzle-orm";
import * as schema from "./db/schema/auth";

const sqlite = new betterSqlite3("/app/.local/db/bunny-auth.db");
const db = drizzle({
  client: sqlite,
  schema: {
    ...schema,
  },
});

export const auth = betterAuth({
  database: db,
  // For development, use explicit localhost to avoid origin issues
  baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3000",
  secret: process.env.BETTER_AUTH_SECRET || "a-very-long-secret-for-development-purposes-only-32-chars",
  emailAndPassword: {
    enabled: true,
    requireEmailVerification: false, // Disable for testing
  },
  socialProviders: {
    github: {
      clientId: process.env.GITHUB_CLIENT_ID || "",
      clientSecret: process.env.GITHUB_CLIENT_SECRET || "",
    },
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
    },
    discord: {
      clientId: process.env.DISCORD_CLIENT_ID || "",
      clientSecret: process.env.DISCORD_CLIENT_SECRET || "",
    },
  },
  session: {
    cookieCache: {
      enabled: false,
    },
    expiresIn: 60 * 60 * 24 * 7, // 7 days
  },
  rateLimit: {
    enabled: true,
    window: 15,
    max: 10,
  },
});
