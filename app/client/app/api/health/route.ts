import { NextResponse } from "next/server";
import { db } from "@/lib/db/mysql";
import { user } from "@/lib/db/schema/mysql-auth";

export async function GET() {
  try {
    const startTime = Date.now();
    const checks = {
      database: false,
      timestamp: new Date().toISOString(),
      responseTime: 0,
    };

    try {
      await db.select().from(user).limit(1);
      checks.database = true;
    } catch (error) {
      console.error("Database health check failed:", error);
    }

    checks.responseTime = Date.now() - startTime;

    const allHealthy = checks.database;

    return NextResponse.json(
      {
        status: allHealthy ? "healthy" : "degraded",
        checks,
        uptime: process.uptime(),
      },
      {
        status: allHealthy ? 200 : 503,
        headers: {
          "Cache-Control": "no-cache, no-store, must-revalidate",
        },
      }
    );
  } catch (error) {
    console.error("Health check error:", error);
    return NextResponse.json(
      {
        status: "unhealthy",
        error: "Internal health check error",
      },
      { status: 500 }
    );
  }
}
