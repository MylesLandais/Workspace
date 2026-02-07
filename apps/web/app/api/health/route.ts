import { NextResponse } from "next/server";
import { checkConnection } from "@/lib/db/mysql";

export async function GET() {
  try {
    const startTime = Date.now();
    const dbCheck = await checkConnection();

    const checks = {
      database: dbCheck.connected,
      databaseError: dbCheck.error,
      databaseLatencyMs: dbCheck.latencyMs,
      timestamp: new Date().toISOString(),
      responseTime: 0,
    };

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
      },
    );
  } catch (error) {
    console.error("Health check error:", error);
    return NextResponse.json(
      {
        status: "unhealthy",
        error: "Internal health check error",
      },
      { status: 500 },
    );
  }
}
