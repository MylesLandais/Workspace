import { NextRequest, NextResponse } from "next/server";

export async function GET() {
  try {
    console.log("Test endpoint: Exact loop replication...");

    // Replicate exact loadImageboardThreads logic
    const threadIds = [
      "944334460",
      "944303266",
      "944330306",
      "944342413",
      "944340175",
    ];

    const threads = [];

    console.log(`Starting loop with ${threadIds.length} thread IDs`);

    for (const threadId of threadIds) {
      console.log(`Processing thread ${threadId}...`);

      try {
        const response = await fetch(
          `http://localhost:3000/imageboard/html/b_${threadId}.html`,
        );
        console.log(`  HTML response status: ${response.status}`);

        if (!response.ok) {
          console.log(`  Continue - HTML not OK: ${response.status}`);
          continue;
        }

        const html = await response.text();
        console.log(`  Got HTML, length: ${html.length}`);

        const titleMatch = html.match(/<title>\/[a-z]\/ - ([^-]+) -/);
        const title = titleMatch ? titleMatch[1].trim() : "4chan Thread";
        console.log(`  Parsed title: "${title}"`);

        threads.push({
          threadId,
          title,
          opBody: "",
          board: "b",
          imageCount: 0,
          replyCount: 100,
          imagePaths: [],
          createdAt: new Date().toISOString(),
        });

        console.log(`  [SUCCESS] Added thread ${threadId}`);
      } catch (error) {
        console.error(`  [ERROR] Error with thread ${threadId}:`, error);
      }
    }

    console.log(`Final result: ${threads.length} threads`);

    return NextResponse.json({
      threadCount: threads.length,
      firstThread: threads[0] || null,
    });
  } catch (error) {
    console.error("Test endpoint error:", error);
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";
    const errorStack = error instanceof Error ? error.stack : undefined;
    return NextResponse.json(
      { error: "Failed loop test", details: errorMessage, stack: errorStack },
      { status: 500 },
    );
  }
}
