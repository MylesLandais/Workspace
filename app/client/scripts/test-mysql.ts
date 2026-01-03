#!/usr/bin/env bun
/**
 * Test MySQL connection and query performance
 */

import mysql from "mysql2/promise";

const start = Date.now();

const pool = mysql.createPool({
  host: process.env.MYSQL_HOST || "localhost",
  user: process.env.MYSQL_USER || "root",
  password: process.env.MYSQL_PASSWORD || "betterauth",
  database: process.env.MYSQL_DATABASE || "bunny_auth",
  waitForConnections: true,
  connectionLimit: 10,
});

console.log(`[MySQL] Pool created in ${Date.now() - start}ms`);

// Test connection
try {
  const connStart = Date.now();
  const connection = await pool.getConnection();
  console.log(`[MySQL] Got connection in ${Date.now() - connStart}ms`);
  
  // Test query
  const queryStart = Date.now();
  const [rows] = await connection.execute("SELECT 1 as test");
  console.log(`[MySQL] Query executed in ${Date.now() - queryStart}ms`, rows);
  
  connection.release();
  pool.end();
  console.log(`[MySQL] Total time: ${Date.now() - start}ms`);
} catch (e) {
  console.error("[MySQL] Error:", e);
  pool.end();
  process.exit(1);
}
