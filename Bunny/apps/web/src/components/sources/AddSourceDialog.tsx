"use client";

import { useState } from "react";
import { X, Loader2, Plus } from "lucide-react";
import { SourceType, type CreateSourceInput } from "@/lib/types/sources";

interface AddSourceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (input: CreateSourceInput) => Promise<void>;
}

export function AddSourceDialog({
  isOpen,
  onClose,
  onAdd,
}: AddSourceDialogProps) {
  const [sourceType, setSourceType] = useState<SourceType>(SourceType.RSS);
  const [value, setValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!value.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const input: CreateSourceInput = {
        name: value,
        sourceType,
      };

      // Set the appropriate handle field based on source type
      switch (sourceType) {
        case SourceType.RSS:
          input.url = value.startsWith("http") ? value : `https://${value}`;
          input.name = value;
          break;
        case SourceType.REDDIT:
          input.subredditName = value.replace(/^r\//, "");
          input.name = `r/${input.subredditName}`;
          break;
        case SourceType.YOUTUBE:
          input.youtubeHandle = value.replace(/^@/, "");
          input.name = `@${input.youtubeHandle}`;
          break;
        case SourceType.TWITTER:
          input.twitterHandle = value.replace(/^@/, "");
          input.name = `@${input.twitterHandle}`;
          break;
        case SourceType.INSTAGRAM:
          input.instagramHandle = value.replace(/^@/, "");
          input.name = `@${input.instagramHandle}`;
          break;
        case SourceType.TIKTOK:
          input.tiktokHandle = value.replace(/^@/, "");
          input.name = `@${input.tiktokHandle}`;
          break;
      }

      await onAdd(input);
      handleClose();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setValue("");
    setError(null);
    setSourceType(SourceType.RSS);
    onClose();
  };

  if (!isOpen) return null;

  const placeholders: Record<SourceType, string> = {
    [SourceType.RSS]: "https://example.com/feed.xml",
    [SourceType.REDDIT]: "r/technology or technology",
    [SourceType.YOUTUBE]: "@channelname or channelname",
    [SourceType.TWITTER]: "@username or username",
    [SourceType.INSTAGRAM]: "@username or username",
    [SourceType.TIKTOK]: "@username or username",
    [SourceType.VSCO]: "username",
    [SourceType.IMAGEBOARD]: "board name",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-md bg-zinc-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
          <h2 className="text-lg font-semibold text-app-text">Add Source</h2>
          <button
            onClick={handleClose}
            className="p-1 rounded hover:bg-white/5 text-app-muted hover:text-app-text transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6">
          {/* Source Type Selection */}
          <div className="mb-4">
            <label className="block text-xs font-medium text-app-muted uppercase tracking-wider mb-2">
              Source Type
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                SourceType.RSS,
                SourceType.REDDIT,
                SourceType.YOUTUBE,
                SourceType.TWITTER,
                SourceType.INSTAGRAM,
                SourceType.TIKTOK,
              ].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setSourceType(type)}
                  className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                    sourceType === type
                      ? "bg-white/10 border-white/20 text-app-text"
                      : "bg-zinc-800/50 border-white/5 text-app-muted hover:border-white/10"
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div className="mb-4">
            <label className="block text-xs font-medium text-app-muted uppercase tracking-wider mb-2">
              {sourceType === SourceType.RSS ? "Feed URL" : "Handle / Username"}
            </label>
            <input
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={placeholders[sourceType]}
              className="w-full px-4 py-3 bg-zinc-800/50 border border-white/5 rounded-xl text-app-text placeholder:text-app-muted focus:outline-none focus:ring-2 focus:ring-white/10"
            />
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-app-muted hover:text-app-text transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!value.trim() || isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-white text-black font-semibold rounded-xl hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              Add Source
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
