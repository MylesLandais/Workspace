"use client";

import React from "react";
import { ExternalLink } from "lucide-react";

interface IframeWidgetProps {
  content: string;
}

const IframeWidget: React.FC<IframeWidgetProps> = ({ content: url }) => {
  if (!url) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-industrial-400">
        <ExternalLink className="w-12 h-12 mb-4 opacity-50" />
        <p className="text-sm">No URL provided</p>
      </div>
    );
  }

  return (
    <div className="h-full w-full">
      <iframe
        src={url}
        className="w-full h-full border-none"
        sandbox="allow-scripts allow-same-origin"
        title="Embedded content"
      />
    </div>
  );
};

export default IframeWidget;
