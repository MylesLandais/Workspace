/**
 * MySQL database connection for Better Auth.
 *
 * Uses mysql2/promise with connection pooling for performance.
 * Drizzle ORM provides type-safe queries.
 */
import { drizzle } from "drizzle-orm/mysql2";
import mysql from "mysql2/promise";
import * as authSchema from "./schema/mysql-auth";

const pool = mysql.createPool({
  host: process.env.MYSQL_HOST || "localhost",
  user: process.env.MYSQL_USER || "root",
  password: process.env.MYSQL_PASSWORD || "betterauth",
  database: process.env.MYSQL_DATABASE || "bunny_auth",
  waitForConnections: true,
  connectionLimit: 20,
  queueLimit: 0,
  enableKeepAlive: true,
  keepAliveInitialDelay: 0,
});

export const mysqlDb = drizzle(pool, {
  schema: authSchema,
  mode: "default",
});

export type MySQLDatabase = typeof mysqlDb;
export { pool };
