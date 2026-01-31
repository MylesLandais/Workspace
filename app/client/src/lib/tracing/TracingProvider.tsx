"use client";

import { useEffect } from "react";
import { initBrowserTracing } from "@/lib/tracing/instrumentation.browser";

export function TracingProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    try {
      initBrowserTracing();
    } catch (error) {
      console.warn(
        "Tracing initialization failed, continuing without tracing:",
        error,
      );
    }
  }, []);

  return <>{children}</>;
}
