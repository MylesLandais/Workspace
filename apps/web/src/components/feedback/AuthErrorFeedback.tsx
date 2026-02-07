"use client";

import * as Sentry from "@sentry/nextjs";
import { Button } from "@/components/ui/button";
import { MessageSquare, AlertCircle } from "lucide-react";

interface AuthErrorFeedbackProps {
  error: {
    message?: string;
    code?: string;
    status?: number;
    statusText?: string;
  } | null;
  authFlow: "signin" | "signup" | "social_signin";
  email?: string;
  provider?: string;
  className?: string;
}

export function AuthErrorFeedback({
  error,
  authFlow,
  email,
  provider,
  className,
}: AuthErrorFeedbackProps) {
  const feedback = Sentry.getFeedback();

  if (!error || !feedback) {
    return null;
  }

  const openFeedbackForm = async () => {
    const flowLabel =
      authFlow === "signup"
        ? "sign up"
        : authFlow === "social_signin"
          ? `sign in with ${provider || "social provider"}`
          : "sign in";

    const formTitle =
      authFlow === "signup"
        ? "Report Sign Up Problem"
        : authFlow === "social_signin"
          ? `Report ${provider ? provider.charAt(0).toUpperCase() + provider.slice(1) : "Social"} Sign In Problem`
          : "Report Sign In Problem";

    const form = await feedback.createForm({
      messagePlaceholder: `What happened when you tried to ${flowLabel}?`,
      formTitle,
      enableScreenshot: true,
      showName: false,
      showEmail: true,
      isEmailRequired: false,
      tags: {
        "feedback.source": `auth-${authFlow}`,
        "feedback.type": "bug-report",
        auth_flow: authFlow,
        ...(error.code && { "error.code": error.code }),
        ...(error.status && { "error.status": String(error.status) }),
        ...(provider && { "auth.provider": provider }),
      },
      onSubmitSuccess: () => {
        console.log("[Feedback] User submitted feedback for auth error");
      },
    });

    form.appendToDom();
    form.open();
  };

  return (
    <div className={`space-y-3 ${className || ""}`}>
      <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
        <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-red-400 font-medium">
            {error.message || "An error occurred"}
          </p>
          {error.code && (
            <p className="text-xs text-red-500/70 mt-1">
              Error code: {error.code}
              {error.status && ` (HTTP ${error.status})`}
            </p>
          )}
        </div>
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={openFeedbackForm}
        className="w-full"
      >
        <MessageSquare className="w-4 h-4" />
        Report this issue
      </Button>
    </div>
  );
}
