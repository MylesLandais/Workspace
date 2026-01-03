import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";

/**
 * Better Auth Route Handler for Next.js 15.
 * Handles all /api/auth/* requests.
 * Includes performance logging to debug latency issues.
 */
const { GET: authGET, POST: authPOST } = toNextJsHandler(auth);

export async function POST(request: Request) {
    const start = Date.now();
    const url = new URL(request.url);
    console.log(`[Auth] POST ${url.pathname} started`);
    
    try {
        const response = await authPOST(request);
        const duration = Date.now() - start;
        console.log(`[Auth] POST ${url.pathname} completed in ${duration}ms with status ${response.status}`);
        return response;
    } catch (e) {
        const duration = Date.now() - start;
        console.error(`[Auth] POST ${url.pathname} failed in ${duration}ms`, e);
        throw e;
    }
}

export async function GET(request: Request) {
    const start = Date.now();
    const url = new URL(request.url);
    // Log less frequently for GET to avoid noise, but helpful for debugging now
    console.log(`[Auth] GET ${url.pathname} started`);

    try {
        const response = await authGET(request);
        const duration = Date.now() - start;
        console.log(`[Auth] GET ${url.pathname} completed in ${duration}ms with status ${response.status}`);
        return response;
    } catch (e) {
        const duration = Date.now() - start;
        console.error(`[Auth] GET ${url.pathname} failed in ${duration}ms`, e);
        throw e;
    }
}
