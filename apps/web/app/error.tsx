"use client";

import { useEffect } from "react";
import { logError } from "@/lib/errorLogger";

export const dynamic = "force-dynamic";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Error page:", error);

    // Capture error to Sentry
    logError(error, {
      tags: {
        error_type: "nextjs_error_boundary",
        error_digest: error.digest || "no_digest",
      },
      extra: {
        error_name: error.name,
        error_message: error.message,
        error_stack: error.stack,
      },
    });
  }, [error]);

  return (
    <main className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center p-4">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-bold text-white">Something went wrong</h1>
        <p className="text-zinc-400 max-w-md">
          {error.message || "An unexpected error occurred"}
        </p>
        <button
          onClick={() => (window.location.href = "/")}
          className="inline-block px-6 py-3 bg-white text-black rounded-lg hover:bg-zinc-200 transition-colors"
        >
          Go Home
        </button>
      </div>
    </main>
  );
}
