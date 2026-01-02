import { createAuthClient } from "better-auth/react";

/**
 * Better Auth client-side instance.
 * 
 * Provides React hooks and methods for authentication:
 * - useSession(): Client-side session state
 * - signIn.email(): Email/password login
 * - signUp.email(): User registration
 * - signOut(): End session
 * 
 * The baseURL is dynamically handled to support different access origins
 * (e.g. localhost vs IP) in development.
 */
export const authClient = createAuthClient({
    // If running in browser, omit baseURL to use current origin
    // If running on server, use the provided environment variable
    baseURL: typeof window === "undefined" 
        ? process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"
        : undefined,
});

export const { useSession, signIn, signOut, signUp } = authClient;
