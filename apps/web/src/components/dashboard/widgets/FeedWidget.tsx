"use client";

import React, { useState, useEffect } from "react";
import { Rss, Loader2 } from "lucide-react";

interface FeedWidgetProps {
  content: string;
  onSelectArticle?: (article: unknown, source: string) => void;
}

const FeedWidget: React.FC<FeedWidgetProps> = ({
  content,
  onSelectArticle,
}) => {
  const [items, setItems] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Placeholder for GraphQL integration
    setLoading(false);
  }, [content]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-matcha-500" />
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="flex flex-col items-center justify-center text-industrial-400 py-8">
        <Rss className="w-12 h-12 mb-4 opacity-50" />
        <p className="text-sm">Feed widget - GraphQL integration pending</p>
        <p className="text-xs mt-2">Source: {content}</p>
      </div>
    </div>
  );
};

export default FeedWidget;
