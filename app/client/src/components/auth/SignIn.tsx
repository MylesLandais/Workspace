/**
 * Sign In / Sign Up Component
 *
 * Authentication component supporting both login and registration.
 *
 * Features:
 * - Email/password authentication with client-side validation
 * - Social login (GitHub, Google, Discord)
 * - Invite key support for beta access
 * - Automatic redirect on success
 * - Comprehensive error handling
 *
 * @module components/auth/SignIn
 */

"use client";

import { useState } from "react";
import { signIn, signUp } from "@/lib/auth-client";
import { Github, Loader2, Globe } from "lucide-react";
import { withSpan, addSpanEvent } from "@/lib/tracing/tracer";
import { logError } from "@/lib/errorLogger";
import * as Sentry from "@sentry/nextjs";
import { AuthErrorFeedback } from "@/components/feedback";

/**
 * Expected auth error codes that shouldn't be logged to Sentry
 * These are normal user errors, not bugs
 */
const EXPECTED_AUTH_ERROR_CODES = [
  "INVALID_EMAIL_OR_PASSWORD",
  "USER_NOT_FOUND",
  "INVALID_PASSWORD",
  "EMAIL_NOT_VERIFIED",
  "INVALID_EMAIL",
  "INVALID_CREDENTIALS",
  "USER_WITH_EMAIL_ALREADY_EXISTS",
];

/**
 * Sign in/up form component
 *
 * @param inviteKey - Optional invite code from validation page
 * @param defaultIsSignUp - Whether to start in sign up mode
 */
export function SignIn({
  inviteKey,
  defaultIsSignUp = false,
}: {
  inviteKey?: string;
  defaultIsSignUp?: boolean;
}) {
  const [isSignUp, setIsSignUp] = useState(defaultIsSignUp);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState<string | null>(null);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<{
    message?: string;
    code?: string;
    status?: number;
    statusText?: string;
  } | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    if (isSignUp && password.length < 8) {
      setError("Password must be at least 8 characters");
      setLoading(false);
      return;
    }

    if (isSignUp && inviteKey && !username) {
      setError("Username is required for invite-based signups");
      setLoading(false);
      return;
    }

    if (
      isSignUp &&
      inviteKey &&
      username &&
      !/^[a-z0-9_]{3,20}$/.test(username)
    ) {
      setError(
        "Username must be 3-20 characters, lowercase letters, numbers, or underscores only",
      );
      setLoading(false);
      return;
    }

    setError(null);
    setErrorDetails(null);
    const timeoutId = setTimeout(() => {
      if (loading) {
        setError("Request timed out. Please check server logs.");
        setLoading(false);
      }
    }, 15000);

    try {
      if (isSignUp) {
        await withSpan(
          "auth.signup.client",
          async (span) => {
            span.setAttributes({
              "user.email": email,
              "user.has_name": !!name,
              "user.has_username": !!username,
              "user.has_invite": !!inviteKey,
              component: "auth-client",
              operation: "signup",
            });

            console.log("Attempting sign up with:", {
              email,
              name,
              username,
              inviteKey,
            });
            setLoadingMessage("Creating account...");
            setLoadingProgress(0);

            const progressInterval = setInterval(() => {
              setLoadingProgress((prev) => {
                if (prev >= 90) return prev;
                return prev + 10;
              });
            }, 500);

            addSpanEvent(span, "signup.api.call.start");

            try {
              const result = await signUp.email({
                email,
                password,
                name,
                callbackURL: "/dashboard",
              });
              clearInterval(progressInterval);
              setLoadingProgress(100);
              clearTimeout(timeoutId);
              console.log("Sign up result:", JSON.stringify(result, null, 2));

              addSpanEvent(span, "signup.api.call.complete", {
                hasError: !!result.error ? "1" : "0",
                hasData: !!result.data ? "1" : "0",
              });

              // Handle the response structure
              if (result.error) {
                const error = result.error;

                // Extract error details from various possible structures
                let errorCode = "unknown";
                let errorMessage = "Unknown error";
                let errorStatus: number | undefined;
                let errorData: unknown = null;

                if (typeof error === "object" && error !== null) {
                  // Better Auth error structure
                  errorCode =
                    (error as any).code || (error as any).status || "unknown";
                  errorMessage =
                    (error as any).message ||
                    (error as any).statusText ||
                    (error as any).error ||
                    String(error);
                  errorStatus =
                    (error as any).status || (error as any).statusCode;
                  errorData =
                    (error as any).data || (error as any).body || error;
                } else if (typeof error === "string") {
                  errorMessage = error;
                }

                // Log full error details to console for debugging
                console.error("Signup error details:", {
                  error,
                  errorCode,
                  errorMessage,
                  errorStatus,
                  errorData,
                  fullResult: result,
                });

                span.setAttribute("error", true);
                span.setAttribute("error.code", String(errorCode));
                span.setAttribute("error.message", errorMessage);
                if (errorStatus) {
                  span.setAttribute("error.status", errorStatus);
                }

                addSpanEvent(span, "signup.error", {
                  code: String(errorCode),
                  message: errorMessage,
                  status: errorStatus ? String(errorStatus) : undefined,
                });

                // Build a clean error message for logging
                const logMessage =
                  errorCode !== "unknown" && errorMessage
                    ? `Signup error: ${errorCode} - ${errorMessage}`
                    : errorMessage || "Signup error: unknown";

                // Store error details for feedback component
                setErrorDetails({
                  message: errorMessage,
                  code: errorCode,
                  status: errorStatus,
                  statusText: errorStatus ? String(errorStatus) : undefined,
                });

                // Only log unexpected errors to Sentry (not user mistakes)
                if (!EXPECTED_AUTH_ERROR_CODES.includes(errorCode)) {
                  logError(new Error(logMessage), {
                    tags: {
                      auth_flow: "signup",
                      error_code: String(errorCode),
                      "feedback.source": "auth-signup",
                      ...(errorStatus && { http_status: String(errorStatus) }),
                    },
                    extra: {
                      email: email,
                      error_message: errorMessage,
                      error_code: errorCode,
                      error_status: errorStatus,
                      error_data: errorData,
                      error_object: error,
                      full_result: result,
                    },
                  });
                } else {
                  // Just log to console for debugging
                  console.log(`[Auth] Expected signup error: ${errorCode}`, {
                    message: errorMessage,
                    status: errorStatus,
                  });
                }

                if (errorCode === "USER_WITH_EMAIL_ALREADY_EXISTS") {
                  setError(
                    "This email is already in use. Try signing in instead.",
                  );
                } else {
                  setError(errorMessage || "Failed to sign up");
                }
              } else if (result.data) {
                span.setAttribute("signup.success", true);
                span.setAttribute("user.id", result.data.user?.id || "unknown");

                addSpanEvent(span, "signup.success", {
                  userId: result.data.user?.id || "unknown",
                });

                setSuccess("Account created successfully! Redirecting...");
                setError(null);
                setErrorDetails(null);

                if (inviteKey && username) {
                  addSpanEvent(span, "profile.complete.start", {
                    username,
                    inviteCode: inviteKey,
                  });

                  fetch("/api/user/complete-profile", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      userId: result.data.user.id,
                      username,
                      inviteCode: inviteKey,
                    }),
                  })
                    .then(() => {
                      addSpanEvent(span, "profile.complete.success");
                    })
                    .catch((profileErr) => {
                      span.setAttribute("profile.complete.error", true);
                      addSpanEvent(span, "profile.complete.error", {
                        error:
                          profileErr instanceof Error
                            ? profileErr.message
                            : "Unknown error",
                      });
                      console.error(
                        "Background profile completion error:",
                        profileErr,
                      );
                    });
                }

                addSpanEvent(span, "signup.redirect");
                window.location.href = "/dashboard";
              } else {
                span.setAttribute("error", true);
                span.setAttribute("error.message", "Unexpected response");
                addSpanEvent(span, "signup.unexpected-response");
                console.warn("Sign up returned no error and no data");
                setError("Unexpected response from server. Please try again.");
              }
            } catch (err) {
              clearTimeout(timeoutId);

              // Extract comprehensive error information
              const errorMessage =
                err instanceof Error ? err.message : "Unknown error";
              const errorStack = err instanceof Error ? err.stack : undefined;
              const errorName = err instanceof Error ? err.name : typeof err;

              // Log full error details to console for debugging
              console.error("Sign up exception details:", {
                error: err,
                errorMessage,
                errorStack,
                errorName,
                errorType: typeof err,
                errorString: String(err),
              });

              span.setAttribute("error", true);
              span.setAttribute("error.message", errorMessage);
              span.setAttribute("error.type", errorName);

              addSpanEvent(span, "signup.exception", {
                error: errorMessage,
                errorType: errorName,
              });

              // Store error details for feedback component
              setErrorDetails({
                message: errorMessage,
                code: errorName,
              });

              // Log signup exception for debugging with full context
              logError(err, {
                tags: {
                  auth_flow: "signup",
                  error_type: "exception",
                  error_name: errorName,
                  "feedback.source": "auth-signup",
                },
                extra: {
                  email: email,
                  error_message: errorMessage,
                  error_stack: errorStack,
                  error_name: errorName,
                  error_type: typeof err,
                  error_string: String(err),
                  full_error: err,
                },
              });

              setError(
                err instanceof Error
                  ? err.message
                  : "An unexpected error occurred",
              );
            }
          },
          {
            attributes: {
              component: "auth-client",
              operation: "signup",
            },
            kind: "client",
          },
        );
      } else {
        console.log("Attempting sign in with:", { email });

        // Start Sentry span for signin (using Performance Monitoring API)
        await Sentry.startSpan(
          {
            name: "auth.signin",
            op: "auth.signin",
            attributes: {
              auth_flow: "signin",
            },
          },
          async (span) => {
            try {
              const result = await signIn.email({
                email,
                password,
                callbackURL: "/dashboard",
              });
              clearTimeout(timeoutId);
              console.log("Sign in result:", JSON.stringify(result, null, 2));

              if (result.error) {
                const error = result.error;

                // Extract error details from various possible structures
                let errorCode = "unknown";
                let errorMessage = "Unknown error";
                let errorStatus: number | undefined;
                let errorData: unknown = null;

                if (typeof error === "object" && error !== null) {
                  // Better Auth error structure
                  errorCode =
                    (error as any).code || (error as any).status || "unknown";
                  errorMessage =
                    (error as any).message ||
                    (error as any).statusText ||
                    (error as any).error ||
                    String(error);
                  errorStatus =
                    (error as any).status || (error as any).statusCode;
                  errorData =
                    (error as any).data || (error as any).body || error;
                } else if (typeof error === "string") {
                  errorMessage = error;
                }

                // Log full error details to console for debugging
                console.error("Signin error details:", {
                  error,
                  errorCode,
                  errorMessage,
                  errorStatus,
                  errorData,
                  fullResult: result,
                });

                // Mark span as failed
                span.setStatus({ status: "internal_error" });
                span.setAttribute("error_code", String(errorCode));
                span.setAttribute("error_message", errorMessage);
                if (errorStatus) {
                  span.setAttribute("error_status", errorStatus);
                }

                // Build a clean error message for logging
                const logMessage =
                  errorCode !== "unknown" && errorMessage
                    ? `Signin error: ${errorCode} - ${errorMessage}`
                    : errorMessage || "Signin error: unknown";

                // Store error details for feedback component
                setErrorDetails({
                  message: errorMessage,
                  code: errorCode,
                  status: errorStatus,
                  statusText: errorStatus ? String(errorStatus) : undefined,
                });

                // Only log unexpected errors to Sentry (not user mistakes)
                if (!EXPECTED_AUTH_ERROR_CODES.includes(errorCode)) {
                  logError(new Error(logMessage), {
                    tags: {
                      auth_flow: "signin",
                      error_code: String(errorCode),
                      "feedback.source": "auth-signin",
                      ...(errorStatus && { http_status: String(errorStatus) }),
                    },
                    extra: {
                      email: email,
                      error_message: errorMessage,
                      error_code: errorCode,
                      error_status: errorStatus,
                      error_data: errorData,
                      error_object: error,
                      full_result: result,
                    },
                  });
                } else {
                  // Just log to console for debugging
                  console.log(`[Auth] Expected signin error: ${errorCode}`, {
                    message: errorMessage,
                    status: errorStatus,
                  });
                }
                setError(errorMessage || "Failed to sign in");
              } else if (result.data) {
                // Mark span as successful
                span.setStatus({ status: "ok" });
                setSuccess("Signed in successfully! Redirecting...");
                setError(null);
                setErrorDetails(null);
                window.location.href = "/dashboard";
              } else {
                span.setStatus({ status: "unknown_error" });
                console.warn("Sign in returned no error and no data");
                setError("Unexpected response from server. Please try again.");
              }
            } catch (err) {
              clearTimeout(timeoutId);

              // Extract comprehensive error information
              const errorMessage =
                err instanceof Error ? err.message : "Unknown error";
              const errorStack = err instanceof Error ? err.stack : undefined;
              const errorName = err instanceof Error ? err.name : typeof err;

              // Log full error details to console for debugging
              console.error("Sign in exception details:", {
                error: err,
                errorMessage,
                errorStack,
                errorName,
                errorType: typeof err,
                errorString: String(err),
              });

              // Mark span as failed
              span.setStatus({ status: "internal_error" });
              span.setAttribute("error_type", "exception");
              span.setAttribute("error_message", errorMessage);
              span.setAttribute("error_name", errorName);

              // Store error details for feedback component
              setErrorDetails({
                message: errorMessage,
                code: errorName,
              });

              // Log signin exception for debugging with full context
              logError(err, {
                tags: {
                  auth_flow: "signin",
                  error_type: "exception",
                  error_name: errorName,
                  "feedback.source": "auth-signin",
                },
                extra: {
                  email: email,
                  error_message: errorMessage,
                  error_stack: errorStack,
                  error_name: errorName,
                  error_type: typeof err,
                  error_string: String(err),
                  full_error: err,
                },
              });

              setError(
                err instanceof Error && err.message?.includes("fetch")
                  ? "Network error: Make sure the server is reachable"
                  : "An unexpected error occurred",
              );
            }
          },
        );
      }
    } catch (err) {
      clearTimeout(timeoutId);
      console.error("Auth fetch exception:", err);

      // Store error details for feedback component
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setErrorDetails({
        message: errorMessage,
        code: err instanceof Error ? err.name : "unknown",
      });

      // Log outer auth exception for debugging
      logError(err, {
        tags: {
          auth_flow: isSignUp ? "signup" : "signin",
          error_type: "outer_exception",
          "feedback.source": isSignUp ? "auth-signup" : "auth-signin",
        },
        extra: {
          error_message: errorMessage,
        },
      });

      setError(
        err instanceof Error && err.message?.includes("fetch")
          ? "Network error: Make sure the server is reachable"
          : "An unexpected error occurred",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSocialSignIn = async (
    provider: "github" | "google" | "discord",
  ) => {
    try {
      await signIn.social({
        provider,
        callbackURL: "/dashboard",
      });
    } catch (err) {
      // Log social signin exception for debugging
      const errorMessage = err instanceof Error ? err.message : "Unknown error";

      // Store error details for feedback component
      setErrorDetails({
        message: errorMessage,
        code: err instanceof Error ? err.name : "unknown",
      });
      setError(`Failed to sign in with ${provider}. Please try again.`);

      logError(err, {
        tags: {
          auth_flow: "social_signin",
          provider: provider,
          error_type: "exception",
          "feedback.source": "auth-social-signin",
        },
        extra: {
          error_message: errorMessage,
          provider,
        },
      });
      console.error(`Social sign-in error (${provider}):`, err);
    }
  };

  return (
    <div className="w-full max-w-md p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl">
      <div className="mb-8 text-center">
        <h2 className="text-2xl font-bold tracking-tight text-white">
          {isSignUp ? "Create Account" : "Access System Nebula"}
        </h2>
        <p className="text-sm text-zinc-400 mt-2">
          {isSignUp
            ? "Join the System Nebula community"
            : "Enter your credentials or use a social provider"}
        </p>
        {inviteKey && (
          <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 bg-zinc-800/50 border border-white/10 rounded-full">
            <span className="text-xs text-zinc-500 uppercase tracking-wider">
              Invite Key:
            </span>
            <span className="text-xs text-zinc-300 font-mono">{inviteKey}</span>
          </div>
        )}
      </div>

      <form onSubmit={handleAuth} className="space-y-4">
        {isSignUp && (
          <>
            <div>
              <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1 px-1">
                Full Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-4 py-3 bg-zinc-900/50 border border-white/5 rounded-xl text-zinc-200 focus:outline-none focus:ring-2 focus:ring-white/10 transition-all sm:text-sm"
                placeholder="John Doe"
              />
            </div>
            {inviteKey && (
              <div>
                <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1 px-1">
                  Username
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value.toLowerCase())}
                  required
                  className="w-full px-4 py-3 bg-zinc-900/50 border border-white/5 rounded-xl text-zinc-200 font-mono focus:outline-none focus:ring-2 focus:ring-white/10 transition-all sm:text-sm"
                  placeholder="username"
                  pattern="^[a-z0-9_]{3,20}$"
                  title="Username must be 3-20 characters, lowercase letters, numbers, or underscores only"
                />
              </div>
            )}
          </>
        )}
        <div>
          <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1 px-1">
            Email Address
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-4 py-3 bg-zinc-900/50 border border-white/5 rounded-xl text-zinc-200 focus:outline-none focus:ring-2 focus:ring-white/10 transition-all sm:text-sm"
            placeholder="name@example.com"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider mb-1 px-1">
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full px-4 py-3 bg-zinc-900/50 border border-white/5 rounded-xl text-zinc-200 focus:outline-none focus:ring-2 focus:ring-white/10 transition-all sm:text-sm"
            placeholder="••••••••"
          />
        </div>

        {success && <p className="text-xs text-green-500 px-1">{success}</p>}

        {error && (
          <AuthErrorFeedback
            error={errorDetails}
            authFlow={isSignUp ? "signup" : "signin"}
            email={email}
            className="mt-2"
          />
        )}

        {loading && loadingProgress > 0 && (
          <div className="w-full">
            <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-zinc-400 to-white transition-all duration-500 ease-out"
                style={{ width: `${loadingProgress}%` }}
              />
            </div>
            <p className="text-xs text-zinc-500 text-center mt-2">
              {loadingProgress}%
            </p>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 px-4 bg-white text-black font-semibold rounded-xl hover:bg-zinc-200 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              {loadingMessage || "Processing..."}
            </>
          ) : isSignUp ? (
            "Create Account"
          ) : (
            "Sign In"
          )}
        </button>

        <p className="text-center text-xs text-zinc-500 mt-4">
          {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
          <button
            type="button"
            onClick={() => {
              setIsSignUp(!isSignUp);
              setSuccess(null);
              setError(null);
              setErrorDetails(null);
            }}
            className="text-white hover:underline font-medium"
          >
            {isSignUp ? "Sign In" : "Sign Up"}
          </button>
        </p>
      </form>

      <div className="relative my-8">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/5"></div>
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-[#0a0a0a] px-2 text-zinc-500">
            Or continue with
          </span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <button
          onClick={() => handleSocialSignIn("github")}
          className="flex items-center justify-center py-3 bg-zinc-900/50 border border-white/5 rounded-xl hover:bg-zinc-800 transition-colors"
        >
          <Github className="w-5 h-5 text-white" />
        </button>
        <button
          onClick={() => handleSocialSignIn("google")}
          className="flex items-center justify-center py-3 bg-zinc-900/50 border border-white/5 rounded-xl hover:bg-zinc-800 transition-colors"
        >
          <Globe className="w-5 h-5 text-white" />
        </button>
        <button
          onClick={() => handleSocialSignIn("discord")}
          className="flex items-center justify-center py-3 bg-zinc-900/50 border border-white/5 rounded-xl hover:bg-zinc-800 transition-colors"
        >
          <svg
            className="w-5 h-5 text-white"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.086 2.157 2.419c0 1.334-.966 2.419-2.157 2.419zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.086 2.157 2.419c0 1.334-.946 2.419-2.157 2.419z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
