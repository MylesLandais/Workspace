/**
 * AuthRedirect - Client Component Island
 *
 * Handles authenticated user redirect logic without blocking page render.
 * This runs in the background after the page paints.
 */
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "@/lib/auth-client";

export function AuthRedirect() {
  const { data: session, isPending } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (!isPending && session) {
      router.replace("/dashboard");
    }
  }, [session, isPending, router]);

  // This component renders nothing - it's just for the redirect side effect
  return null;
}
