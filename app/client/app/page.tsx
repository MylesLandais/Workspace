/**
 * Home Page - System Nebula Landing Page
 *
 * Stealth-mode landing page for invite-only community platform.
 *
 * Features:
 * - Email collection for beta waitlist/mailing list
 * - Link to invite key validation for those with codes
 * - Subtle door icon for existing users to access auth
 *
 * @module app/page
 */

"use client";

import { DoorOpen, Key } from "lucide-react";
import Link from "next/link";
import { WaitlistForm } from "@/components/waitlist/WaitlistForm";

export const dynamic = "force-dynamic";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center p-4 relative overflow-hidden">
      <Link
        href="/auth"
        className="fixed bottom-8 left-1/2 -translate-x-1/2 text-zinc-700 hover:text-zinc-500 transition-colors group"
        aria-label="Existing users sign in"
      >
        <DoorOpen className="w-6 h-6 opacity-30 group-hover:opacity-50 transition-opacity" />
      </Link>

      <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-20">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-white/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-zinc-500/5 rounded-full blur-[120px]" />
      </div>
      
      <div className="w-full flex flex-col items-center gap-16 relative z-10">
        <div className="flex flex-col items-center space-y-6 text-center">
          <div className="w-20 h-20 bg-white/5 backdrop-blur-sm border border-white/10 flex items-center justify-center rounded-2xl rotate-3">
            <span className="text-white text-5xl font-black">SN</span>
          </div>
          <div className="space-y-2">
            <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-white uppercase italic">
              System Nebula
            </h1>
            <div className="inline-block px-4 py-2 bg-zinc-800/50 border border-white/10 rounded-full">
              <p className="text-zinc-400 text-sm font-mono uppercase tracking-[0.3em]">
                Under Construction
              </p>
            </div>
          </div>
          <p className="text-zinc-500 max-w-md text-lg font-medium tracking-tight">
            Community pages coming soon. Join the mailing list to receive a beta invite.
          </p>
        </div>

        <WaitlistForm />

        <div className="flex items-center gap-4">
          <Link
            href="/invite"
            className="flex items-center gap-2 text-zinc-500 hover:text-white transition-colors group"
          >
            <Key className="w-4 h-4 opacity-50 group-hover:opacity-100 transition-opacity" />
            <span className="text-sm">Have an invite key?</span>
          </Link>
        </div>

        <div className="text-zinc-700 text-[10px] font-mono uppercase tracking-[0.2em]">
          Protocol 43-B // Restricted Access
        </div>
      </div>
    </main>
  );
}
