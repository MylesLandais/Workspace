"use client";

import React from "react";
import { BookOpen, ExternalLink, Clock, Share2 } from "lucide-react";

interface ReaderWidgetProps {
  content: string;
}

const ReaderWidget: React.FC<ReaderWidgetProps> = ({ content }) => {
  if (!content) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-industrial-50 dark:bg-industrial-950">
        <BookOpen className="w-12 h-12 text-industrial-200 dark:text-industrial-800 mb-4" />
        <h4 className="text-xs font-bold text-industrial-400 dark:text-industrial-600 uppercase tracking-widest font-mono">
          Select an article to read
        </h4>
      </div>
    );
  }

  const [title, source, date, body, link] = content.split("|");

  return (
    <div className="h-full flex flex-col bg-white dark:bg-industrial-900 animate-in fade-in duration-500 transition-colors overflow-y-auto">
      <div className="shrink-0 p-6 bg-matcha-50 dark:bg-industrial-925 border-b border-matcha-200 dark:border-industrial-800">
        <div className="flex items-center gap-2 mb-2">
          <span className="px-2 py-0.5 bg-matcha-200 dark:bg-matcha-800 text-matcha-800 dark:text-matcha-200 text-[10px] font-bold uppercase tracking-wider font-mono rounded">
            {source || "Article"}
          </span>
          <div className="flex items-center gap-1 text-[10px] text-industrial-400 dark:text-industrial-500 font-medium uppercase tracking-wider font-mono">
            <Clock className="w-3 h-3" />
            {date || "Recent"}
          </div>
        </div>
        <h2 className="text-xl font-bold text-industrial-900 dark:text-white leading-tight tracking-tight">
          {title}
        </h2>
      </div>

      <div className="flex-1 p-8 prose prose-industrial dark:prose-invert max-w-none">
        <div className="text-base leading-relaxed text-industrial-600 dark:text-industrial-300 space-y-4">
          {body ? (
            body.split("\n").map((para, i) => <p key={i}>{para}</p>)
          ) : (
            <p className="italic text-industrial-400 dark:text-industrial-500 text-sm">
              No preview content available for this article.
            </p>
          )}
        </div>

        {link && (
          <div className="mt-12 pt-8 border-t border-industrial-100 dark:border-industrial-800 flex items-center justify-between">
            <a
              href={link}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 bg-matcha-600 hover:bg-matcha-700 text-white px-6 py-2.5 text-xs font-bold transition-all uppercase tracking-wider font-mono rounded"
            >
              Continue to Full Source <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <button className="p-2 text-industrial-400 dark:text-industrial-500 hover:text-matcha-600 dark:hover:text-matcha-400 transition-colors">
              <Share2 className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReaderWidget;
