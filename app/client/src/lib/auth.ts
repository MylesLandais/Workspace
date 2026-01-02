import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "./db";
import * as schema from "./db/schema/auth";

/**
 * Better Auth server-side configuration.
 * 
 * This module initializes the authentication server with:
 * - LibSQL/SQLite database adapter via Drizzle.
 * - Email & Password authentication.
 * - Social providers (GitHub, Google, Discord).
 * - Session cookie caching for performance.
 * 
 * @see https://www.better-auth.com/docs/concepts/config
 */
export const auth = betterAuth({
    database: drizzleAdapter(db, {
        provider: "sqlite",
        schema: {
            ...schema,
        },
    }),
    // In development, allow Better Auth to infer the URL from headers
    // this prevents issues when accessing via IP vs localhost
    baseURL: process.env.NODE_ENV === "production" ? process.env.BETTER_AUTH_URL : undefined,
    emailAndPassword: {
        enabled: true,
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
            enabled: true,
            maxAge: 5 * 60, // 5 minutes cache
        },
    },
});
