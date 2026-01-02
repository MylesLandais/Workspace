import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";

/**
 * Better Auth Route Handler for Next.js 15.
 * Handles all /api/auth/* requests.
 * 
 * We explicitly pin the runtime to "nodejs" to ensure compatibility with 
 * native SQLite drivers even when using the Bun runtime.
 */
export const runtime = "nodejs";
export const { GET, POST } = toNextJsHandler(auth);
