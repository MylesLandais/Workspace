"use client";

import React, { useState, useEffect } from "react";
import { Hash, Loader2, Sparkles, AlertCircle, RefreshCcw } from "lucide-react";
import { askGemini } from "@/lib/services/geminiService";

interface TagMonitorWidgetProps {
  tagId: string;
}

const TagMonitorWidget: React.FC<TagMonitorWidgetProps> = ({ tagId }) => {
  const [insight, setInsight] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [tagName, setTagName] = useState("Workspace Tag");

  const fetchInsight = async () => {
    setLoading(true);

    // Fetch tag info from localStorage
    if (typeof window !== "undefined") {
      const savedTags = localStorage.getItem("bunny-dashboard-tags-v1");
      if (savedTags) {
        try {
          const tags = JSON.parse(savedTags);
          const tag = tags.find(
            (t: { id: string; label: string }) => t.id === tagId,
          );
          if (tag) setTagName(tag.label);
        } catch (error) {
          console.error("[TagMonitor] Error parsing tags:", error);
        }
      }
    }

    const response = await askGemini(
      `Generate a brief intelligence summary for the workspace tag "${tagName}". 
       Focus on trends, potential action items, and cross-project impacts. 
       Keep it under 100 words.`,
    );
    setInsight(
      response || "No specific insights available for this tag at the moment.",
    );
    setLoading(false);
  };

  useEffect(() => {
    fetchInsight();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tagId]);

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 bg-industrial-50 dark:bg-industrial-900/50">
        <Loader2 className="w-8 h-8 text-matcha-500 animate-spin mb-4" />
        <p className="text-[10px] font-bold uppercase text-industrial-400 tracking-widest animate-pulse">
          Analyzing Tag Metadata...
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-industrial-900 p-5 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-matcha-50 dark:bg-matcha-900/30 rounded-lg">
            <Hash className="w-4 h-4 text-matcha-600 dark:text-matcha-400" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-industrial-800 dark:text-industrial-100 uppercase tracking-wider">
              {tagName}
            </h4>
            <span className="text-[9px] text-industrial-400 font-bold uppercase">
              AI Insights
            </span>
          </div>
        </div>
        <button
          onClick={fetchInsight}
          className="p-1.5 text-industrial-300 hover:text-matcha-500 transition-colors"
        >
          <RefreshCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="flex-1 space-y-4">
        <div className="bg-matcha-50/50 dark:bg-matcha-900/10 p-4 rounded-xl border border-matcha-100 dark:border-matcha-900/30 relative">
          <Sparkles className="absolute -top-1.5 -right-1.5 w-4 h-4 text-amber-400" />
          <p className="text-[12px] leading-relaxed text-industrial-600 dark:text-industrial-400 font-medium italic">
            &ldquo;{insight}&rdquo;
          </p>
        </div>

        <div className="flex items-start gap-3 p-3 bg-industrial-50 dark:bg-industrial-800/50 rounded-lg">
          <AlertCircle className="w-3.5 h-3.5 text-industrial-400 mt-0.5" />
          <div className="flex-1">
            <p className="text-[10px] font-bold text-industrial-500 dark:text-industrial-400 uppercase tracking-tight">
              Active Context
            </p>
            <p className="text-[9px] text-industrial-400">
              Monitoring related streams and files.
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-industrial-100 dark:border-industrial-800 flex justify-between">
        <div className="flex -space-x-1.5">
          <div className="w-5 h-5 rounded-full bg-industrial-200 dark:bg-industrial-700 border border-white dark:border-industrial-900" />
          <div className="w-5 h-5 rounded-full bg-industrial-300 dark:bg-industrial-600 border border-white dark:border-industrial-900" />
        </div>
        <span className="text-[9px] font-bold text-industrial-400 uppercase">
          Synced 1m ago
        </span>
      </div>
    </div>
  );
};

export default TagMonitorWidget;
