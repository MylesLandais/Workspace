/**
 * Test endpoint to verify Sentry is working
 * GET /api/test-sentry
 */

import { NextResponse } from "next/server";
import * as Sentry from "@sentry/nextjs";

export async function GET() {
  try {
    // Test error capture
    const testError = new Error("Test error from /api/test-sentry endpoint");

    Sentry.captureException(testError, {
      tags: {
        test_endpoint: "true",
        timestamp: new Date().toISOString(),
      },
      extra: {
        endpoint: "/api/test-sentry",
        method: "GET",
      },
    });

    return NextResponse.json({
      success: true,
      message: "Test error sent to Sentry",
      error: testError.message,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        message: "Failed to send test error",
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
}
