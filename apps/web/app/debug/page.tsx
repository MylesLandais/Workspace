"use client";

/**
 * Debug Dashboard
 *
 * Developer-only page showing environment status, build info, and system health.
 */

import { useEffect, useState } from "react";
import { createLogger } from "@/lib/debug/logger";

const log = createLogger("page:debug");

interface DebugData {
  environment?: {
    variables: Record<string, string>;
    validation: {
      valid: boolean;
      missing: string[];
      warnings: number;
      errors: number;
    };
  };
  connectivity?: {
    database: boolean;
    redis: boolean;
  };
  build?: {
    routes?: string[];
    routeCount?: number;
    hasRootPage?: boolean;
    error?: string;
  };
  timestamp?: string;
}

export default function DebugPage() {
  const [envData, setEnvData] = useState<DebugData>({});
  const [buildData, setBuildData] = useState<DebugData>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    log.info("Debug dashboard mounted");
    fetchDebugData();
  }, []);

  const fetchDebugData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [envResponse, buildResponse] = await Promise.all([
        fetch("/api/debug/env"),
        fetch("/api/debug/build"),
      ]);

      if (envResponse.ok) {
        const envJson = await envResponse.json();
        setEnvData(envJson);
      }

      if (buildResponse.ok) {
        const buildJson = await buildResponse.json();
        setBuildData(buildJson);
      }

      log.info("Debug data fetched successfully");
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Unknown error";
      log.error("Failed to fetch debug data", err);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-4xl font-bold">Debug Dashboard</h1>
          <button
            onClick={fetchDebugData}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
          >
            Refresh
          </button>
        </div>

        {loading && (
          <div className="text-zinc-400 text-center py-12">
            Loading debug information...
          </div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-6">
            <h2 className="text-red-400 font-semibold mb-2">Error</h2>
            <p className="text-red-300">{error}</p>
          </div>
        )}

        {!loading && !error && (
          <>
            <section className="space-y-4">
              <h2 className="text-2xl font-semibold">Connectivity</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <StatusCard
                  title="Database"
                  status={envData.connectivity?.database}
                />
                <StatusCard
                  title="Redis"
                  status={envData.connectivity?.redis}
                />
              </div>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold">Environment Validation</h2>
              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6 space-y-4">
                {envData.environment?.validation && (
                  <>
                    <div className="flex items-center gap-3">
                      <span
                        className={`px-3 py-1 rounded-full text-sm font-medium ${
                          envData.environment.validation.valid
                            ? "bg-green-900/30 text-green-400"
                            : "bg-yellow-900/30 text-yellow-400"
                        }`}
                      >
                        {envData.environment.validation.valid
                          ? "Valid"
                          : "Using Defaults"}
                      </span>
                    </div>
                    {envData.environment.validation.missing.length > 0 && (
                      <div>
                        <h3 className="text-yellow-400 font-medium mb-2">
                          Missing Required Variables:
                        </h3>
                        <ul className="list-disc list-inside text-zinc-400">
                          {envData.environment.validation.missing.map((key) => (
                            <li key={key}>{key}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <div className="text-sm text-zinc-400">
                      Warnings: {envData.environment.validation.warnings} |
                      Errors: {envData.environment.validation.errors}
                    </div>
                  </>
                )}
              </div>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold">Environment Variables</h2>
              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
                <div className="grid grid-cols-1 gap-2 font-mono text-sm">
                  {envData.environment?.variables &&
                    Object.entries(envData.environment.variables).map(
                      ([key, value]) => (
                        <div key={key} className="flex gap-4">
                          <span className="text-zinc-500 w-48">{key}:</span>
                          <span
                            className={
                              value === "[NOT SET]"
                                ? "text-zinc-600"
                                : value === "[REDACTED]"
                                  ? "text-yellow-400"
                                  : "text-zinc-300"
                            }
                          >
                            {value}
                          </span>
                        </div>
                      ),
                    )}
                </div>
              </div>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold">Build Information</h2>
              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6 space-y-4">
                <div className="flex items-center gap-4">
                  <span className="text-zinc-400">Root Page:</span>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${
                      buildData.build?.hasRootPage
                        ? "bg-green-900/30 text-green-400"
                        : "bg-red-900/30 text-red-400"
                    }`}
                  >
                    {buildData.build?.hasRootPage ? "Compiled" : "Missing"}
                  </span>
                </div>
                <div className="text-zinc-400">
                  Total Routes: {buildData.build?.routeCount || 0}
                </div>
                {buildData.build?.error && (
                  <div className="text-red-400">
                    Error: {buildData.build.error}
                  </div>
                )}
                {buildData.build?.routes && (
                  <details className="mt-4">
                    <summary className="cursor-pointer text-zinc-400 hover:text-white">
                      View All Routes ({buildData.build.routes.length})
                    </summary>
                    <ul className="mt-2 pl-4 space-y-1 font-mono text-sm text-zinc-500">
                      {buildData.build.routes.map((route) => (
                        <li key={route}>{route}</li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold">Quick Tests</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <TestButton
                  label="Test Waitlist API"
                  endpoint="/api/waitlist"
                  method="POST"
                  body={{
                    email: `test-${Date.now()}@example.com`,
                    name: "Debug Test",
                  }}
                />
                <TestButton
                  label="Test Health API"
                  endpoint="/api/health"
                  method="GET"
                />
                <TestButton
                  label="Test Auth API"
                  endpoint="/api/auth/session"
                  method="GET"
                />
              </div>
            </section>
          </>
        )}

        <div className="text-center text-zinc-600 text-sm pt-8">
          Last updated: {envData.timestamp || buildData.timestamp || "N/A"}
        </div>
      </div>
    </div>
  );
}

function StatusCard({ title, status }: { title: string; status?: boolean }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">{title}</h3>
        <div
          className={`w-3 h-3 rounded-full ${
            status ? "bg-green-500" : "bg-red-500"
          }`}
        />
      </div>
      <p className="text-sm text-zinc-400 mt-2">
        {status ? "Connected" : "Disconnected"}
      </p>
    </div>
  );
}

function TestButton({
  label,
  endpoint,
  method,
  body,
}: {
  label: string;
  endpoint: string;
  method: string;
  body?: unknown;
}) {
  const [result, setResult] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);

  const runTest = async () => {
    setTesting(true);
    setResult(null);

    try {
      const response = await fetch(endpoint, {
        method,
        headers: body ? { "Content-Type": "application/json" } : {},
        body: body ? JSON.stringify(body) : undefined,
      });

      const text = await response.text();
      setResult(`${response.status}: ${text.substring(0, 100)}`);
    } catch (error) {
      setResult(`Error: ${error instanceof Error ? error.message : "Unknown"}`);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3">
      <button
        onClick={runTest}
        disabled={testing}
        className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-700 disabled:cursor-not-allowed rounded-lg transition-colors text-sm font-medium"
      >
        {testing ? "Testing..." : label}
      </button>
      {result && (
        <pre className="text-xs text-zinc-400 bg-black/30 p-2 rounded overflow-x-auto">
          {result}
        </pre>
      )}
    </div>
  );
}
