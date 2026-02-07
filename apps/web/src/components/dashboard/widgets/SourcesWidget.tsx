"use client";

import React, { Suspense } from "react";
import { Loader2 } from "lucide-react";
import { SourceManagerWidget } from "@/components/sources/SourceManagerWidget";

interface SourcesWidgetProps {
  content?: string;
}

const SourcesWidget: React.FC<SourcesWidgetProps> = ({ content }) => {
  return (
    <div className="h-full w-full p-2">
      <Suspense
        fallback={
          <div className="h-full flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-matcha-500" />
          </div>
        }
      >
        <SourceManagerWidget
          className="h-full border-none shadow-none bg-transparent"
          title={content || "Content Sources"}
        />
      </Suspense>
    </div>
  );
};

export default SourcesWidget;
