import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: [
    "./src/lib/db/schema/mysql-auth.ts",
    "./src/lib/db/schema/subscriptions.ts",
  ],
  out: "./drizzle",
  dialect: "mysql",
  dbCredentials: {
    host: process.env.MYSQL_HOST || "127.0.0.1",
    port: parseInt(process.env.MYSQL_PORT || "3307", 10),
    user: process.env.MYSQL_USER || "root",
    password: process.env.MYSQL_PASSWORD || "secret",
    database: process.env.MYSQL_DATABASE || "bunny_auth",
  },
});
