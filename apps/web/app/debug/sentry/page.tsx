/**
 * Sentry Debug Page
 *
 * Test Sentry error capture from the client side
 */

"use client";

import { useState } from "react";
import * as Sentry from "@sentry/nextjs";
import { logError } from "@/lib/errorLogger";

export default function SentryDebugPage() {
  const [result, setResult] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const testDirectSentry = async () => {
    setLoading(true);
    setResult("Testing direct Sentry.captureException...\n");

    try {
      const testError = new Error("Test error from Sentry debug page");
      const eventId = Sentry.captureException(testError, {
        tags: {
          source: "debug-page",
          test: "true",
        },
        extra: {
          timestamp: new Date().toISOString(),
        },
      });

      setResult((prev) => prev + `Event ID: ${eventId}\n`);

      // Flush immediately
      const flushed = await Sentry.flush(2000);
      setResult((prev) => prev + `Flushed: ${flushed}\n`);
      setResult(
        (prev) =>
          prev +
          `Sentry Client: ${Sentry.getClient() ? "Connected" : "Not connected"}\n`,
      );
    } catch (error) {
      setResult((prev) => prev + `Error: ${error}\n`);
    } finally {
      setLoading(false);
    }
  };

  const testLogError = async () => {
    setLoading(true);
    setResult("Testing logError wrapper...\n");

    try {
      // Check Sentry initialization first
      const sentryClient = Sentry.getClient();
      setResult(
        (prev) =>
          prev +
          `Sentry Client: ${sentryClient ? "Connected" : "Not connected"}\n`,
      );

      if (!sentryClient) {
        setResult((prev) => prev + "⚠️ WARNING: Sentry not initialized!\n");
      }

      // Capture what happens in console
      const originalLog = console.log;
      const originalError = console.error;
      const logs: string[] = [];

      console.log = (...args: unknown[]) => {
        logs.push(`[LOG] ${args.map((a) => String(a)).join(" ")}`);
        originalLog(...args);
      };

      console.error = (...args: unknown[]) => {
        logs.push(`[ERROR] ${args.map((a) => String(a)).join(" ")}`);
        originalError(...args);
      };

      logError(new Error("Test error from logError wrapper"), {
        tags: {
          source: "debug-page",
          test: "true",
        },
        extra: {
          timestamp: new Date().toISOString(),
        },
      });

      // Wait a bit for async operations
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Restore console
      console.log = originalLog;
      console.error = originalError;

      setResult((prev) => prev + "logError called\n");
      setResult((prev) => prev + `\nConsole Output:\n${logs.join("\n")}\n`);

      // Check if event was captured
      const eventIdMatch = logs.find((log) =>
        log.includes("Event captured with ID"),
      );
      const eventId = eventIdMatch
        ? eventIdMatch.match(/ID: ([a-f0-9]+)/)?.[1]
        : null;

      setResult((prev) => {
        const hasEventId = !!eventId;
        let result =
          prev + `\nEvent Captured: ${hasEventId ? "✅ Yes" : "❌ No"}\n`;
        if (eventId) {
          result += `Event ID: ${eventId}\n`;
          result += `\n⚠️ IMPORTANT: Check your Sentry dashboard for this Event ID!\n`;
          result += `If you don't see it, check:\n`;
          result += `1. Sentry Settings → Inbound Filters (may filter localhost/dev)\n`;
          result += `2. Network tab → Filter by "sentry" → Look for POST to *.ingest.sentry.io\n`;
          result += `3. Check if requests return 200 status\n`;
        }
        return result;
      });
    } catch (error) {
      setResult((prev) => prev + `❌ Error in testLogError: ${error}\n`);
      if (error instanceof Error) {
        setResult((prev) => prev + `Stack: ${error.stack}\n`);
      }
    } finally {
      setLoading(false);
    }
  };

  const testApiEndpoint = async () => {
    setLoading(true);
    setResult("Testing API endpoint...\n");

    try {
      const response = await fetch("/api/test-sentry-direct");
      const data = await response.json();
      setResult(
        (prev) => prev + `Response: ${JSON.stringify(data, null, 2)}\n`,
      );
    } catch (error) {
      setResult((prev) => prev + `Error: ${error}\n`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">Sentry Debug Page</h1>

      <div className="space-y-4 mb-6">
        <button
          onClick={testDirectSentry}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          Test Direct Sentry.captureException
        </button>

        <button
          onClick={testLogError}
          disabled={loading}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 ml-4"
        >
          Test logError Wrapper
        </button>

        <button
          onClick={testApiEndpoint}
          disabled={loading}
          className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50 ml-4"
        >
          Test API Endpoint
        </button>
      </div>

      <div className="bg-gray-100 p-4 rounded">
        <h2 className="font-bold mb-2">Results:</h2>
        <pre className="whitespace-pre-wrap font-mono text-sm">
          {result || "Click a button to test..."}
        </pre>
      </div>

      <div className="mt-6 bg-yellow-100 p-4 rounded">
        <h2 className="font-bold mb-2">Instructions:</h2>
        <ol className="list-decimal list-inside space-y-1">
          <li>Open browser DevTools Console (F12)</li>
          <li>Open Network tab and filter by &quot;sentry&quot;</li>
          <li>Click test buttons above</li>
          <li>Check console for Sentry logs</li>
          <li>Check Network tab for POST requests to *.sentry.io</li>
          <li>Verify requests return 200 status</li>
        </ol>
      </div>
    </div>
  );
}
