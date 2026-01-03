import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "./db";
import * as schema from "./db/schema/auth";

export const auth = betterAuth({
    database: drizzleAdapter(db, {
        provider: "sqlite",
        schema: {
            ...schema,
        },
    }),
    // For development, use explicit localhost to avoid origin issues
    // Better-auth validates the origin header against this base URL
    baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3000",
    secret: process.env.BETTER_AUTH_SECRET || "a-very-long-secret-for-development-purposes-only-32-chars",
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
            enabled: false,
        },
    },
});
