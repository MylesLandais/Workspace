"use client";

import { useState } from "react";
import { signIn, signUp } from "@/lib/auth-client";
import { Github, Mail, Loader2, Globe, UserPlus, LogIn } from "lucide-react";

/**
 * Sign In / Sign Up component for the landing page.
 * 
 * Handles:
 * - Email/Password registration with client-side validation.
 * - Email/Password login.
 * - Social login integration (GitHub, Google, Discord).
 * - Automatic redirection upon successful authentication.
 * - Robust error handling with specific Better Auth error code support.
 */
export function SignIn() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    if (isSignUp && password.length < 8) {
      setError("Password must be at least 8 characters");
      setLoading(false);
      return;
    }
    setError(null);
    const timeoutId = setTimeout(() => {
      if (loading) {
        setError("Request timed out. Please check server logs.");
        setLoading(false);
      }
    }, 15000);

    try {
      if (isSignUp) {
        const { data, error } = await signUp.email({
          email,
          password,
          name,
          callbackURL: "/feed",
        });
        clearTimeout(timeoutId);
        if (error) {
          if (error.code === "USER_WITH_EMAIL_ALREADY_EXISTS") {
            setError("This email is already in use. Try signing in instead.");
          } else {
            setError(error.message || "Failed to sign up");
          }
        } else if (data) {
          // Success is handled by callbackURL or automatic redirect
        }
      } else {
        const { data, error } = await signIn.email({
          email,
          password,
          callbackURL: "/feed",
        });
        clearTimeout(timeoutId);
        if (error) {
          setError(error.message || "Failed to sign in");
        } else if (data) {
          // Success
        }
      }
    } catch (err: any) {
      clearTimeout(timeoutId);
      console.error("Auth fetch exception:", err);
      setError(
        err.message?.includes("fetch") 
          ? "Network error: Make sure the server is reachable"
          : "An unexpected error occurred"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSocialSignIn = async (provider: "github" | "google" | "discord") => {
    await signIn.social({
      provider,
      callbackURL: "/feed",
    });
  };

  return (
    <div className="w-full max-w-md p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl">
      <div className="mb-8 text-center">
        <h2 className="text-2xl font-bold tracking-tight text-white">
          {isSignUp ? "Create Account" : "Access Bunny"}
        </h2>
        <p className="text-sm text-zinc-400 mt-2">
          {isSignUp ? "Join the distribution network" : "Enter your credentials or use a social provider"}
        </p>
      </div>

      <form onSubmit={handleAuth} className="space-y-4">
        {isSignUp && (
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

        {error && <p className="text-xs text-red-500 px-1">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 px-4 bg-white text-black font-semibold rounded-xl hover:bg-zinc-200 transition-colors flex items-center justify-center disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
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
            onClick={() => setIsSignUp(!isSignUp)}
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
          <span className="bg-[#0a0a0a] px-2 text-zinc-500">Or continue with</span>
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
          <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.086 2.157 2.419c0 1.334-.966 2.419-2.157 2.419zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.086 2.157 2.419c0 1.334-.946 2.419-2.157 2.419z"/>
          </svg>
        </button>
      </div>
    </div>
  );
}
