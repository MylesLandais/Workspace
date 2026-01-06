import { NextResponse } from "next/server";
import { db } from "@/lib/db/mysql";
import { waitlist, user } from "@/lib/db/schema/mysql-auth";
import { count } from "drizzle-orm";

export async function GET() {
  try {
    const startTime = Date.now();

    let stats = {
      waitlistCount: 0,
      userCount: 0,
      waitlistByStatus: {
        pending: 0,
        invited: 0,
        joined: 0,
      },
    };

    try {
      const [waitlistStats] = await db
        .select({ count: count() })
        .from(waitlist);
      stats.waitlistCount = waitlistStats.count;

      const [userStats] = await db.select({ count: count() }).from(user);
      stats.userCount = userStats.count;
    } catch (error) {
      console.error("Metrics collection error:", error);
      return NextResponse.json(
        {
          status: "error",
          message: "Failed to collect metrics",
        },
        { status: 500 }
      );
    }

    const responseTime = Date.now() - startTime;

    return NextResponse.json({
      status: "success",
      timestamp: new Date().toISOString(),
      stats,
      responseTime,
    });
  } catch (error) {
    console.error("Metrics endpoint error:", error);
    return NextResponse.json(
      {
        status: "error",
        message: "Internal server error",
      },
      { status: 500 }
    );
  }
}
