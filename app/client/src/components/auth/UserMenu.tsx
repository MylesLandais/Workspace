"use client";

import { useSession, signOut } from "@/lib/auth-client";
import { LogOut, User, Settings, Shield, AlertCircle, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * User Menu navigation component.
 */
export function UserMenu() {
  const { data: session, isPending, error } = useSession();
  const [isOpen, setIsOpen] = useState(false);
  const [isSigningOut, setIsSigningOut] = useState(false);
  const router = useRouter();

  // Debug logging - moved to warn to avoid Next.js error overlay in development
  useEffect(() => {
    if (error) console.warn("UserMenu session error:", error);
    if (!isPending && !session) console.warn("UserMenu: No session found");
  }, [session, isPending, error]);

  const handleSignOut = async () => {
    setIsSigningOut(true);
    
    // Set a safety timeout to force redirect even if the network hangs
    const safetyTimeout = setTimeout(() => {
      window.location.href = "/";
    }, 2000);

    try {
      await signOut();
      clearTimeout(safetyTimeout);
      window.location.href = "/";
    } catch (err) {
      console.warn("Sign out API failed, forcing redirect:", err);
      window.location.href = "/";
    }
  };

  if (isPending) return <div className="w-10 h-10 rounded-full bg-zinc-800 animate-pulse" />;
  
  if (error) {
    return (
      <div className="flex items-center gap-2 p-2 rounded-full border border-red-500/20 bg-red-500/10 text-red-400 text-xs font-medium" title={error.message || "Authentication Error"}>
        <AlertCircle className="w-4 h-4" />
        <span className="hidden md:inline">Auth Error</span>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex items-center gap-2 p-2 rounded-full border border-yellow-500/20 bg-yellow-500/10 text-yellow-400 text-xs font-medium">
        <AlertCircle className="w-4 h-4" />
        <span className="hidden md:inline">No Session</span>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-1 rounded-full border border-white/10 bg-black/50 hover:bg-zinc-800 transition-colors"
      >
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-zinc-700 to-zinc-500 flex items-center justify-center text-white overflow-hidden">
          {session.user.image ? (
            <img src={session.user.image} alt={session.user.name || ""} className="w-full h-full object-cover" />
          ) : (
            <User className="w-5 h-5" />
          )}
        </div>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-56 bg-zinc-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden py-1">
            <div className="px-4 py-3 border-b border-white/5">
              <p className="text-sm font-semibold text-white truncate">{session.user.name}</p>
              <p className="text-xs text-zinc-500 truncate">{session.user.email}</p>
            </div>

            <button
              onClick={() => router.push("/profile/edit")}
              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5 transition-colors text-left font-medium"
            >
              <User className="w-4 h-4" />
              Edit Profile
            </button>

            <button className="w-full flex items-center gap-2 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5 transition-colors text-left font-medium">
              <Settings className="w-4 h-4" />
              Preferences
            </button>
            
            {/* @ts-expect-error - role is added by our auth schema but not in default types */}
            {session.user.role === "admin" && (
                <button className="w-full flex items-center gap-2 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5 transition-colors text-left font-medium">
                    <Shield className="w-4 h-4" />
                    Admin Panel
                </button>
            )}

            <button
              onClick={handleSignOut}
              disabled={isSigningOut}
              className="w-full flex items-center gap-2 px-4 py-3 text-sm text-red-400 hover:bg-red-400/10 transition-colors text-left font-semibold border-t border-white/5 mt-1 disabled:opacity-50"
            >
              {isSigningOut ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <LogOut className="w-4 h-4" />
              )}
              {isSigningOut ? "Signing out..." : "Sign Out"}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
