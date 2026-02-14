"use client";

import * as Sentry from "@sentry/nextjs";
import { Button } from "@/components/ui/button";
import { MessageSquare } from "lucide-react";
import type { ButtonProps } from "@/components/ui/button";

interface FeedbackButtonProps extends Omit<ButtonProps, "onClick"> {
  source: string;
  messagePlaceholder?: string;
  formTitle?: string;
  enableScreenshot?: boolean;
  showName?: boolean;
  showEmail?: boolean;
  isEmailRequired?: boolean;
  successMessageText?: string;
  tags?: Record<string, string>;
  onSubmitSuccess?: () => void;
  onFormClose?: () => void;
}

export function FeedbackButton({
  source,
  messagePlaceholder = "How can we improve?",
  formTitle,
  enableScreenshot = false,
  showName = true,
  showEmail = true,
  isEmailRequired = false,
  successMessageText,
  tags = {},
  onSubmitSuccess,
  onFormClose,
  children,
  ...buttonProps
}: FeedbackButtonProps) {
  const feedback = Sentry.getFeedback();

  if (!feedback) {
    return null;
  }

  const handleClick = async () => {
    const form = await feedback.createForm({
      messagePlaceholder,
      formTitle,
      enableScreenshot,
      showName,
      showEmail,
      isEmailRequired,
      successMessageText,
      tags: {
        "feedback.source": source,
        ...tags,
      },
      onSubmitSuccess,
      onFormClose,
    });
    form.appendToDom();
    form.open();
  };

  return (
    <Button onClick={handleClick} {...buttonProps}>
      {children || (
        <>
          <MessageSquare className="w-4 h-4" />
          Give Feedback
        </>
      )}
    </Button>
  );
}
