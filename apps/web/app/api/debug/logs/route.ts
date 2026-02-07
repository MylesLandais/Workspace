import { NextRequest, NextResponse } from "next/server";
import { createLogger } from "@/lib/debug/logger";

const log = createLogger("api:debug:logs");

const recentLogs: Array<{
  timestamp: string;
  level: string;
  namespace: string;
  message: string;
  context?: unknown;
}> = [];

export async function GET(request: NextRequest) {
  log.info("Logs debug endpoint accessed");

  const { searchParams } = new URL(request.url);
  const level = searchParams.get("level");
  const namespace = searchParams.get("namespace");
  const limit = parseInt(searchParams.get("limit") || "50", 10);

  let filteredLogs = [...recentLogs];

  if (level) {
    filteredLogs = filteredLogs.filter(
      (log) => log.level.toLowerCase() === level.toLowerCase(),
    );
  }

  if (namespace) {
    filteredLogs = filteredLogs.filter((log) =>
      log.namespace.startsWith(namespace),
    );
  }

  const limitedLogs = filteredLogs.slice(-limit);

  return NextResponse.json({
    logs: limitedLogs,
    total: filteredLogs.length,
    returned: limitedLogs.length,
    filters: {
      level: level || "all",
      namespace: namespace || "all",
      limit,
    },
  });
}
