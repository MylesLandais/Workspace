"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Loader2, LockKeyhole } from "lucide-react";
import { authClient } from "@/lib/auth-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const errorParam = searchParams.get("error");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(errorParam);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      setLoading(false);
      return;
    }

    // Token is automatically read from URL by better-auth if not passed,
    // but passing it explicitly is safer if we extracted it.
    // However, better-auth docs say requestPasswordReset handles the flow.
    // For resetPassword, we need the new password.
    try {
      const { error } = await authClient.resetPassword({
        newPassword: password,
        // better-auth client will look for ?token=... in window.location automatically
        // but we can pass it if we have it from searchParams just to be sure
        token: token || undefined,
      });

      if (error) {
        setError(error.message || "An error occurred");
      } else {
        router.push("/auth?reset=success");
      }
    } catch (err) {
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (!token && !errorParam) {
    return (
      <div className="text-center space-y-4">
        <div className="bg-red-500/10 border border-red-500/20 text-red-500 p-4 rounded-lg text-sm">
          Invalid or missing reset token. Please request a new link.
        </div>
        <Link href="/auth/forgot-password">
          <Button
            variant="outline"
            className="w-full border-white/10 text-white hover:bg-white/5 hover:text-white"
          >
            Request new link
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-500 p-3 rounded-md text-sm">
          {error}
        </div>
      )}
      <div className="space-y-4">
        <div className="space-y-2">
          <Input
            type="password"
            placeholder="New password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            className="bg-black/20 border-white/10 text-white placeholder:text-zinc-500 focus:border-white/20"
          />
        </div>
        <div className="space-y-2">
          <Input
            type="password"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={8}
            className="bg-black/20 border-white/10 text-white placeholder:text-zinc-500 focus:border-white/20"
          />
        </div>
      </div>
      <Button
        type="submit"
        disabled={loading}
        className="w-full bg-white text-black hover:bg-white/90"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Resetting...
          </>
        ) : (
          "Set New Password"
        )}
      </Button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center p-4 relative overflow-hidden">
      <Link
        href="/auth"
        className="absolute top-8 left-8 text-zinc-500 hover:text-white transition-colors flex items-center gap-2"
      >
        <ArrowLeft className="w-5 h-5" />
        <span className="text-sm">Back to Sign In</span>
      </Link>

      <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-20">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-white/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-zinc-500/5 rounded-full blur-[120px]" />
      </div>

      <div className="w-full max-w-md relative z-10">
        <Card className="bg-black/50 border-white/10 backdrop-blur-xl">
          <CardHeader className="text-center space-y-2">
            <div className="mx-auto w-12 h-12 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center mb-2">
              <LockKeyhole className="w-6 h-6 text-white" />
            </div>
            <CardTitle className="text-2xl font-bold text-white">
              Set New Password
            </CardTitle>
            <CardDescription className="text-zinc-400">
              Please enter your new password below
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Suspense
              fallback={
                <div className="flex justify-center p-4">
                  <Loader2 className="h-6 w-6 animate-spin text-white" />
                </div>
              }
            >
              <ResetPasswordContent />
            </Suspense>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
