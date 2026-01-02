"use client";

import { RedditComment, RedditPost } from "@/lib/types/reddit";
import { ExternalLink, Loader2 } from "lucide-react";

interface LightboxCommentsSidebarProps {
  post: RedditPost;
  comments: RedditComment[];
  isLoading?: boolean;
  onClose?: () => void;
}

function formatScore(score: number): string {
  if (score >= 1000000) return `${(score / 1000000).toFixed(1)}M`;
  if (score >= 1000) return `${(score / 1000).toFixed(1)}K`;
  return score.toString();
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return "now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return date.toLocaleDateString();
}

export function LightboxCommentsSidebar({
  post,
  comments,
  isLoading = false,
  onClose,
}: LightboxCommentsSidebarProps) {
  const redditUrl = `https://reddit.com${post.permalink}`;

  return (
    <div className="flex flex-col h-full bg-black/40 backdrop-blur-sm border-l border-white/5 overflow-hidden">
      {/* Header */}
      <div className="sticky top-0 z-10 border-b border-white/5 p-4 bg-black/60 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-bold uppercase tracking-widest text-white/60">
            Comments
          </h3>
          {isLoading && <Loader2 className="w-4 h-4 animate-spin text-app-accent" />}
        </div>
        <a
          href={redditUrl}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2 text-xs text-app-accent hover:text-app-accent-hover transition-colors"
        >
          <span>View on Reddit</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      {/* Comments List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32 text-white/40">
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              <p className="text-xs">Loading discussion...</p>
            </div>
          </div>
        ) : comments.length > 0 ? (
          <div className="space-y-4 p-4">
            {comments.map((comment) => (
              <div
                key={comment.id}
                className="flex gap-3 text-xs group animate-in fade-in"
                style={{
                  marginLeft: Math.min(comment.depth * 8, 24),
                }}
              >
                <div className="flex-shrink-0">
                  <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-[10px] font-bold text-white/60 border border-white/5">
                    {comment.author?.[0]?.toUpperCase() || "?"}
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2">
                    <span className="font-semibold text-white/90 text-xs truncate">
                      {comment.author || "[deleted]"}
                    </span>
                    <span className="text-white/40 text-[10px] flex-shrink-0">
                      {formatScore(comment.score)} pts
                    </span>
                    {comment.is_submitter && (
                      <span className="text-[9px] font-bold text-app-accent bg-app-accent/20 px-1.5 py-0.5 rounded flex-shrink-0">
                        OP
                      </span>
                    )}
                  </div>
                  <p className="text-white/70 mt-1 leading-relaxed text-xs break-words">
                    {comment.body}
                  </p>
                  <span className="text-white/30 text-[9px] mt-1 block">
                    {formatTime(comment.created_utc)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-32 text-white/40">
            <p className="text-xs">No comments yet</p>
          </div>
        )}
      </div>
    </div>
  );
}
