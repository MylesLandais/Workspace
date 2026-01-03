/**
 * Authentication Page
 *
 * Existing user authentication page for System Nebula.
 *
 * Features:
 * - Sign in form (email/password)
 * - Sign up form with invite key support
 * - Social login providers (GitHub, Google, Discord)
 * - Invite key display if passed from validation
 *
 * Query Params:
 * - mode=signup: Pre-opens sign up form
 * - invite=KEY: Displays and uses invite key
 *
 * @module app/auth/page
 */

import { SignIn } from "@/components/auth/SignIn";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

export const dynamic = "force-dynamic";

/**
 * Auth page server component
 *
 * Receives query params for signup mode and invite keys,
 * passes to client-side SignIn component.
 */
export default async function AuthPage({
  searchParams,
}: {
  searchParams: Promise<{ mode?: string; invite?: string }>;
}) {
  const params = await searchParams;
  const isSignUp = params.mode === "signup";
  const inviteKey = params.invite;
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
      
      <div className="w-full flex flex-col items-center gap-8 relative z-10">
        <div className="flex flex-col items-center space-y-4 text-center">
          <div className="w-16 h-16 bg-white/5 backdrop-blur-sm border border-white/10 flex items-center justify-center rounded-2xl rotate-3">
            <span className="text-white text-3xl font-black">SN</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Existing Users
          </h1>
          <p className="text-zinc-500 text-sm">
            Sign in to access your account
          </p>
        </div>

        <SignIn inviteKey={inviteKey} defaultIsSignUp={isSignUp} />
      </div>
    </main>
  );
}
