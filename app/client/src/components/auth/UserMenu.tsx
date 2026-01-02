"use client";

import { useSession, signOut } from "@/lib/auth-client";
import { LogOut, User, Settings, Shield } from "lucide-react";
import { useState } from "react";

/**
 * User Menu navigation component.
 * 
 * Displayed in the header after the user has logged in.
 * Features:
 * - User avatar (defaults to icon if no image provided).
 * - Dropdown menu with name and email display.
 * - Navigation links for Preferences and Admin Panel (conditional).
 * - Logout trigger.
 */
export function UserMenu() {
  const { data: session, isPending, error } = useSession();
  const [isOpen, setIsOpen] = useState(false);

  if (isPending) return <div className="w-10 h-10 rounded-full bg-zinc-800 animate-pulse" />;
  if (error) return null;
  if (!session) return null;

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
            
            <button className="w-full flex items-center gap-2 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5 transition-colors text-left font-medium">
              <Settings className="w-4 h-4" />
              Preferences
            </button>
            
            {/* @ts-ignore */}
            {session.user.role === "admin" && (
                <button className="w-full flex items-center gap-2 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5 transition-colors text-left font-medium">
                    <Shield className="w-4 h-4" />
                    Admin Panel
                </button>
            )}

            <button
              onClick={() => signOut()}
              className="w-full flex items-center gap-2 px-4 py-3 text-sm text-red-400 hover:bg-red-400/10 transition-colors text-left font-semibold border-t border-white/5 mt-1"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </>
      )}
    </div>
  );
}
