/**
 * Invite Validation Page
 *
 * Validates invitation codes for System Nebula beta access.
 *
 * Valid Code Patterns:
 * - Keys starting with "SN-" prefix
 * - Specific codes: ASDF-WHALECUM
 *
 * Flow:
 * 1. User enters invite key
 * 2. System validates (mock validation - add API for prod)
 * 3. Valid: Redirect to signup with key
 * 4. Invalid: Show error message
 *
 * @module app/invite/page
 */

"use client";

import { useState } from "react";
import { Key, Check, X, Loader2, ArrowLeft } from "lucide-react";
import Link from "next/link";

export const dynamic = "force-dynamic";

/**
 * Invite validation page component
 *
 * Handles invite key validation with mock logic.
 * In production, replace setTimeout with actual API call.
 */
export default function InvitePage() {
  const [inviteKey, setInviteKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<"idle" | "valid" | "invalid">("idle");

  const handleValidate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteKey.trim()) return;

    setLoading(true);

    try {
      const response = await fetch(
        `/api/invite/validate?code=${encodeURIComponent(inviteKey)}`,
      );
      const data = await response.json();

      setLoading(false);
      setStatus(data.valid ? "valid" : "invalid");
    } catch (error) {
      console.error("Invite validation error:", error);
      setLoading(false);
      setStatus("invalid");
    }
  };

  const handleCreateAccount = () => {
    window.location.href =
      "/auth?mode=signup&invite=" + encodeURIComponent(inviteKey);
  };

  return (
    <main className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center p-4 relative overflow-hidden">
      <Link
        href="/"
        className="absolute top-8 left-8 text-zinc-500 hover:text-white transition-colors flex items-center gap-2"
      >
        <ArrowLeft className="w-5 h-5" />
        <span className="text-sm">Back</span>
      </Link>

      <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-20">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-white/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-zinc-500/5 rounded-full blur-[120px]" />
      </div>

      <div className="w-full max-w-md flex flex-col items-center gap-8 relative z-10">
        <div className="flex flex-col items-center space-y-4 text-center">
          <div className="w-20 h-20 bg-white/5 backdrop-blur-sm border border-white/10 flex items-center justify-center rounded-2xl">
            <Key className="w-10 h-10 text-zinc-400" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-white">
            Have an invite key?
          </h1>
          <p className="text-zinc-500 text-sm max-w-xs">
            Enter your invitation key to unlock access to System Nebula
          </p>
        </div>

        {!status || status === "idle" ? (
          <form onSubmit={handleValidate} className="w-full space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2 px-1">
                Invitation Key
              </label>
              <input
                type="text"
                value={inviteKey}
                onChange={(e) => {
                  setInviteKey(e.target.value.toUpperCase());
                  setStatus("idle");
                }}
                placeholder="Enter your invite key"
                className="w-full px-4 py-4 bg-zinc-900/50 border border-white/10 rounded-xl text-zinc-200 font-mono text-lg focus:outline-none focus:ring-2 focus:ring-white/10 focus:border-white/20 transition-all placeholder:text-zinc-600 disabled:opacity-50"
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              disabled={loading || !inviteKey.trim()}
              className="w-full py-4 px-4 bg-white text-black font-semibold rounded-xl hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Validating...
                </>
              ) : (
                "Validate Invite"
              )}
            </button>
          </form>
        ) : status === "valid" ? (
          <div className="w-full space-y-4">
            <div className="w-full p-6 bg-green-950/20 border border-green-500/20 rounded-xl flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center">
                <Check className="w-5 h-5 text-green-500" />
              </div>
              <div className="flex-1">
                <h3 className="text-green-400 font-semibold mb-1">
                  Valid Invitation
                </h3>
                <p className="text-zinc-400 text-sm">
                  Your invite key has been verified. You can now create your
                  account.
                </p>
              </div>
            </div>

            <button
              onClick={handleCreateAccount}
              className="w-full py-4 px-4 bg-white text-black font-semibold rounded-xl hover:bg-zinc-200 transition-colors flex items-center justify-center gap-2"
            >
              Create Account
            </button>
          </div>
        ) : (
          <div className="w-full space-y-4">
            <div className="w-full p-6 bg-red-950/20 border border-red-500/20 rounded-xl flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-red-500/20 rounded-full flex items-center justify-center">
                <X className="w-5 h-5 text-red-500" />
              </div>
              <div className="flex-1">
                <h3 className="text-red-400 font-semibold mb-1">
                  Invalid Invitation
                </h3>
                <p className="text-zinc-400 text-sm">
                  This invite key is not valid or has already been used. Please
                  check the key and try again.
                </p>
              </div>
            </div>

            <button
              onClick={() => {
                setStatus("idle");
                setInviteKey("");
              }}
              className="w-full py-4 px-4 bg-zinc-800 text-white font-semibold rounded-xl hover:bg-zinc-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        <div className="text-zinc-700 text-[10px] font-mono uppercase tracking-[0.2em]">
          Protocol 43-B // Invite Verification
        </div>
      </div>
    </main>
  );
}
