import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./src/lib/db/schema/mysql-auth.ts",
  out: "./drizzle-mysql",
  dialect: "mysql",
  dbCredentials: {
    host: process.env.MYSQL_HOST || "localhost",
    user: process.env.MYSQL_USER || "root",
    password: process.env.MYSQL_PASSWORD || "betterauth",
    database: process.env.MYSQL_DATABASE || "bunny_auth",
  },
});
