import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./src/lib/db/schema/auth.ts",
  out: "./drizzle",
  dialect: "sqlite",
  dbCredentials: {
    url: "file:/app/.local/db/bunny-auth.db",
  },
});
