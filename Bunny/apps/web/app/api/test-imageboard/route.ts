import { NextRequest, NextResponse } from "next/server";

export async function GET() {
  try {
    console.log("Test endpoint: Testing fresh imageboard import...");

    const freshModule = await import("@/lib/mock-data/imageboard-loader-fresh");
    console.log("Fresh module keys:", Object.keys(freshModule));

    const { generateImageboardFeedFresh } = freshModule;
    console.log("Function exists:", typeof generateImageboardFeedFresh);

    const feed = await generateImageboardFeedFresh();
    console.log(`Test endpoint: Generated ${feed.length} imageboard items`);

    return NextResponse.json({
      total: feed.length,
      feed,
    });
  } catch (error) {
    console.error("Test endpoint error:", error);
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";
    const errorStack = error instanceof Error ? error.stack : undefined;
    return NextResponse.json(
      {
        error: "Failed to test fresh imageboard feed",
        details: errorMessage,
        stack: errorStack,
      },
      { status: 500 },
    );
  }
}
