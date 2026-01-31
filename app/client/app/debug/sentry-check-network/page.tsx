/**
 * Sentry Network Check Page
 *
 * Checks if Sentry requests are actually being sent to the server
 */

"use client";

import { useEffect, useState } from "react";
import * as Sentry from "@sentry/nextjs";

export default function SentryNetworkCheckPage() {
  const [networkCheck, setNetworkCheck] = useState<string>("Checking...");

  useEffect(() => {
    const checkNetwork = async () => {
      const results: string[] = [];

      results.push("=== Sentry Network Check ===\n");

      // Check Sentry client
      const client = Sentry.getClient();
      results.push(
        `Sentry Client: ${client ? "✅ Connected" : "❌ Not Connected"}\n`,
      );

      if (client) {
        const dsn = client.getDsn();
        results.push(`DSN: ${dsn ? "✅ Present" : "❌ Missing"}\n`);

        if (dsn) {
          results.push(`DSN Host: ${dsn.host}\n`);
          results.push(`DSN Project: ${dsn.projectId}\n`);
        }
      }

      // Test sending an error
      results.push("\n=== Sending Test Error ===\n");

      const testError = new Error("Network check test error");
      const eventId = Sentry.captureException(testError, {
        tags: {
          test_type: "network_check",
          timestamp: new Date().toISOString(),
        },
      });

      results.push(`Event ID: ${eventId || "❌ No ID returned"}\n`);

      // Flush and wait
      results.push("\n=== Flushing Event ===\n");
      try {
        const flushed = await Sentry.flush(2000);
        results.push(`Flushed: ${flushed ? "✅ Yes" : "❌ No"}\n`);
      } catch (error) {
        results.push(`Flush Error: ${error}\n`);
      }

      results.push("\n=== Network Instructions ===\n");
      results.push("1. Open DevTools → Network tab\n");
      results.push("2. Filter by: 'sentry' or 'ingest'\n");
      results.push(
        "3. Look for POST requests to: *.ingest.sentry.io/api/*/envelope/\n",
      );
      results.push("4. Check the request:\n");
      results.push("   - Status should be 200\n");
      results.push("   - Check Response tab for any errors\n");
      results.push("   - Request payload should contain error data\n");

      if (eventId) {
        results.push(`\n=== Event ID to Check ===\n`);
        results.push(`Event ID: ${eventId}\n`);
        results.push(`\nCheck your Sentry dashboard:\n`);
        results.push(
          `https://sentry.io/organizations/[your-org]/issues/?query=${eventId}\n`,
        );
      }

      setNetworkCheck(results.join(""));
    };

    checkNetwork();
  }, []);

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">Sentry Network Check</h1>

      <div className="bg-gray-100 p-4 rounded">
        <pre className="whitespace-pre-wrap font-mono text-sm">
          {networkCheck}
        </pre>
      </div>

      <div className="mt-6 bg-blue-100 p-4 rounded">
        <h2 className="font-bold mb-2">Next Steps:</h2>
        <ol className="list-decimal list-inside space-y-1">
          <li>Check the Network tab for requests to sentry.io</li>
          <li>
            If requests are blocked (CORS/403), Sentry won't receive events
          </li>
          <li>
            If requests return 200 but no events in dashboard, check Inbound
            Filters
          </li>
          <li>Go to Sentry → Settings → Inbound Filters</li>
          <li>
            Make sure "Filter out events from localhost" is DISABLED for testing
          </li>
        </ol>
      </div>
    </div>
  );
}
