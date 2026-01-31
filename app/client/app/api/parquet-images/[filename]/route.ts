import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ filename: string }> },
) {
  const { filename } = await context.params;

  if (!filename) {
    return NextResponse.json(
      { error: "Filename is required" },
      { status: 400 },
    );
  }

  // Redirect to static file in public directory
  const url = new URL(`/parquet-images/${filename}`, request.url);
  return NextResponse.redirect(url);
}
