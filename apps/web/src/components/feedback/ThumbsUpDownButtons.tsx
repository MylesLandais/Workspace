"use client";

import * as Sentry from "@sentry/nextjs";
import { Button } from "@/components/ui/button";
import { ThumbsUp, ThumbsDown } from "lucide-react";

interface ThumbsUpDownButtonsProps {
  source: string;
  messagePlaceholderPositive?: string;
  messagePlaceholderNegative?: string;
  showLabel?: boolean;
  className?: string;
}

export function ThumbsUpDownButtons({
  source,
  messagePlaceholderPositive = "What did you like most?",
  messagePlaceholderNegative = "How can we improve?",
  showLabel = true,
  className,
}: ThumbsUpDownButtonsProps) {
  const feedback = Sentry.getFeedback();

  if (!feedback) {
    return null;
  }

  return (
    <div className={className}>
      {showLabel && (
        <strong className="text-sm font-medium text-foreground mb-2 block">
          Was this helpful?
        </strong>
      )}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          title="I like this"
          onClick={async () => {
            const form = await feedback.createForm({
              messagePlaceholder: messagePlaceholderPositive,
              tags: {
                component: "ThumbsUpDownButtons",
                "feedback.source": source,
                "feedback.type": "positive",
              },
            });
            form.appendToDom();
            form.open();
          }}
        >
          <ThumbsUp className="w-4 h-4" />
          Yes
        </Button>

        <Button
          variant="outline"
          size="sm"
          title="I don't like this"
          onClick={async () => {
            const form = await feedback.createForm({
              messagePlaceholder: messagePlaceholderNegative,
              tags: {
                component: "ThumbsUpDownButtons",
                "feedback.source": source,
                "feedback.type": "negative",
              },
            });
            form.appendToDom();
            form.open();
          }}
        >
          <ThumbsDown className="w-4 h-4" />
          No
        </Button>
      </div>
    </div>
  );
}
