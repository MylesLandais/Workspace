import { mysqlDb as db } from "@/lib/db/mysql";
import { user } from "@/lib/db/schema/mysql-auth";
import { count } from "drizzle-orm";
import { NextResponse } from "next/server";

export async function GET() {
  const start = Date.now();
  try {
    // Perform a simple count query to test connectivity and speed
    const result = await db.select({ count: count() }).from(user);
    const duration = Date.now() - start;

    return NextResponse.json({
      status: "ok",
      duration: `${duration}ms`,
      userCount: result[0]?.count || 0,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    const duration = Date.now() - start;
    return NextResponse.json(
      {
        status: "error",
        duration: `${duration}ms`,
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
      },
      { status: 500 },
    );
  }
}
