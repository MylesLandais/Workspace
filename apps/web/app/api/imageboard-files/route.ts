import { readdirSync } from "fs";
import { join } from "path";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const thread = request.nextUrl.searchParams.get("thread");

  if (!thread) {
    return NextResponse.json(
      { error: "Missing thread parameter" },
      { status: 400 },
    );
  }

  // Prevent path traversal
  if (thread.includes("..") || thread.includes("/") || thread.includes("\\")) {
    return NextResponse.json(
      { error: "Invalid thread parameter" },
      { status: 400 },
    );
  }

  try {
    const imageDir = join(process.cwd(), "public", "imageboard", "b", thread);

    // Read actual files from the directory
    const files = readdirSync(imageDir)
      .filter((file) => /\.(jpg|jpeg|png|webm|gif)$/i.test(file))
      .sort()
      .map((file) => `/imageboard/b/${thread}/${file}`);

    return NextResponse.json({
      thread,
      count: files.length,
      files,
    });
  } catch (error) {
    console.error(
      `Failed to read imageboard directory for thread ${thread}:`,
      error,
    );
    return NextResponse.json(
      { error: "Failed to read thread images", thread },
      { status: 404 },
    );
  }
}
