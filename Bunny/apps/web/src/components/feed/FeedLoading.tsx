"use client";

import { Loader2 } from "lucide-react";

export function FeedLoading() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-app-muted gap-4">
      <Loader2 className="w-10 h-10 animate-spin text-app-accent" />
      <p className="text-sm font-medium animate-pulse">Loading your feed...</p>
    </div>
  );
}
