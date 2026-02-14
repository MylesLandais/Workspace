"use client";

import { useState, useRef, useEffect } from "react";
import { X, Tag } from "lucide-react";
import { cn } from "@/lib/utils";
import { TagChip } from "./tag-chip";

interface BulkTagDialogProps {
  open: boolean;
  onClose: () => void;
  selectedCount: number;
  selectedIds: string[];
  allTags: string[];
  onBulkAddTags: (ids: string[], tags: string[]) => Promise<number>;
  onBulkRemoveTags: (ids: string[], tags: string[]) => Promise<number>;
  onComplete: () => void;
}

export function BulkTagDialog({
  open,
  onClose,
  selectedCount,
  selectedIds,
  allTags,
  onBulkAddTags,
  onBulkRemoveTags,
  onComplete,
}: BulkTagDialogProps) {
  const [mode, setMode] = useState<"add" | "remove">("add");
  const [inputValue, setInputValue] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
    }
    if (!open) {
      setInputValue("");
      setSelectedTags([]);
      setMode("add");
    }
  }, [open]);

  if (!open) return null;

  const suggestions = inputValue.trim()
    ? allTags
        .filter(
          (t) =>
            t.toLowerCase().includes(inputValue.toLowerCase()) &&
            !selectedTags.includes(t),
        )
        .slice(0, 5)
    : allTags.filter((t) => !selectedTags.includes(t)).slice(0, 8);

  const handleAddTag = (tag: string) => {
    const trimmed = tag.trim().toLowerCase();
    if (!trimmed || selectedTags.includes(trimmed)) return;
    setSelectedTags((prev) => [...prev, trimmed]);
    setInputValue("");
  };

  const handleRemoveTag = (tag: string) => {
    setSelectedTags((prev) => prev.filter((t) => t !== tag));
  };

  const handleSubmit = async () => {
    if (selectedTags.length === 0) return;
    setIsSubmitting(true);

    try {
      if (mode === "add") {
        await onBulkAddTags(selectedIds, selectedTags);
      } else {
        await onBulkRemoveTags(selectedIds, selectedTags);
      }
      onComplete();
      onClose();
    } catch (err) {
      console.error("Bulk tag operation failed:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && inputValue.trim()) {
      e.preventDefault();
      handleAddTag(inputValue);
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative w-full max-w-md bg-zinc-900 border border-white/10 rounded-2xl shadow-2xl">
        <div className="flex items-center justify-between p-4 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Tag className="w-4 h-4 text-white/60" />
            <h2 className="text-sm font-semibold text-white">
              {mode === "add" ? "Add" : "Remove"} Tags
            </h2>
            <span className="text-xs text-white/40">
              ({selectedCount} sources)
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-4 h-4 text-white/60" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          <div className="flex gap-2">
            <button
              onClick={() => setMode("add")}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
                mode === "add"
                  ? "bg-app-accent text-black"
                  : "bg-white/5 text-white/60 hover:bg-white/10",
              )}
            >
              Add tags
            </button>
            <button
              onClick={() => setMode("remove")}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
                mode === "remove"
                  ? "bg-red-500/80 text-white"
                  : "bg-white/5 text-white/60 hover:bg-white/10",
              )}
            >
              Remove tags
            </button>
          </div>

          <div className="flex flex-wrap gap-1.5 min-h-[32px] p-2 rounded-lg border border-white/10 bg-white/5">
            {selectedTags.map((tag) => (
              <TagChip
                key={tag}
                tag={tag}
                removable
                onRemove={() => handleRemoveTag(tag)}
                size="md"
              />
            ))}
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                selectedTags.length > 0 ? "Add more..." : "Type a tag name..."
              }
              className="flex-1 min-w-[100px] bg-transparent text-sm text-white/80 outline-none placeholder:text-white/30"
            />
          </div>

          {suggestions.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              <span className="text-[10px] text-white/30 w-full">
                Suggestions:
              </span>
              {suggestions.map((tag) => (
                <TagChip
                  key={tag}
                  tag={tag}
                  onClick={() => handleAddTag(tag)}
                  size="sm"
                />
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-2 p-4 border-t border-white/5">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs text-white/60 hover:bg-white/10 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={selectedTags.length === 0 || isSubmitting}
            className={cn(
              "px-4 py-2 rounded-lg text-xs font-medium transition-colors",
              selectedTags.length > 0 && !isSubmitting
                ? mode === "add"
                  ? "bg-app-accent text-black hover:bg-app-accent-hover"
                  : "bg-red-500/80 text-white hover:bg-red-500"
                : "bg-white/5 text-white/30 cursor-not-allowed",
            )}
          >
            {isSubmitting
              ? "Applying..."
              : `${mode === "add" ? "Add" : "Remove"} ${selectedTags.length} tag${selectedTags.length !== 1 ? "s" : ""}`}
          </button>
        </div>
      </div>
    </div>
  );
}
