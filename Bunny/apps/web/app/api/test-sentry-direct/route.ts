/**
 * Direct test endpoint to verify Sentry is working
 * This sends a test error immediately and flushes it
 * GET /api/test-sentry-direct
 */

import { NextResponse } from "next/server";
import * as Sentry from "@sentry/nextjs";

export async function GET() {
  try {
    console.log("[Test Sentry] Starting test error capture...");

    // Test error capture
    const testError = new Error(
      "Direct test error from /api/test-sentry-direct endpoint",
    );

    const eventId = Sentry.captureException(testError, {
      tags: {
        test_endpoint: "test-sentry-direct",
        timestamp: new Date().toISOString(),
      },
      extra: {
        endpoint: "/api/test-sentry-direct",
        method: "GET",
        test: true,
      },
    });

    console.log("[Test Sentry] Event ID:", eventId);

    // Flush immediately
    const flushed = await Sentry.flush(2000);
    console.log("[Test Sentry] Flushed:", flushed);

    return NextResponse.json({
      success: true,
      message: "Test error sent to Sentry",
      eventId: eventId,
      flushed: flushed,
      error: testError.message,
      timestamp: new Date().toISOString(),
      sentryClient: Sentry.getClient() ? "Connected" : "Not connected",
    });
  } catch (error) {
    console.error("[Test Sentry] Error:", error);
    return NextResponse.json(
      {
        success: false,
        message: "Failed to send test error",
        error: error instanceof Error ? error.message : "Unknown error",
        sentryClient: Sentry.getClient() ? "Connected" : "Not connected",
      },
      { status: 500 },
    );
  }
}
