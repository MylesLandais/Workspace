"use client";

import { useState, useRef, useEffect } from "react";
import { Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { TagChip } from "./tag-chip";

interface InlineTagEditorProps {
  sourceId: string;
  tags: string[];
  allTags: string[];
  onAddTags: (id: string, tags: string[]) => Promise<string[]>;
  onRemoveTags: (id: string, tags: string[]) => Promise<string[]>;
  onTagsChanged?: () => void;
}

export function InlineTagEditor({
  sourceId,
  tags,
  allTags,
  onAddTags,
  onRemoveTags,
  onTagsChanged,
}: InlineTagEditorProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [localTags, setLocalTags] = useState(tags);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLocalTags(tags);
  }, [tags]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  useEffect(() => {
    if (!isEditing) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsEditing(false);
        setInputValue("");
        setSuggestions([]);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isEditing]);

  useEffect(() => {
    if (!inputValue.trim()) {
      setSuggestions([]);
      return;
    }
    const query = inputValue.toLowerCase();
    const filtered = allTags
      .filter((t) => t.toLowerCase().includes(query) && !localTags.includes(t))
      .slice(0, 5);
    setSuggestions(filtered);
  }, [inputValue, allTags, localTags]);

  const handleAdd = async (tag: string) => {
    const trimmed = tag.trim().toLowerCase();
    if (!trimmed || localTags.includes(trimmed)) return;

    setLocalTags((prev) => [...prev, trimmed]);
    setInputValue("");
    setSuggestions([]);

    try {
      await onAddTags(sourceId, [trimmed]);
      onTagsChanged?.();
    } catch {
      setLocalTags(tags);
    }
  };

  const handleRemove = async (tag: string) => {
    setLocalTags((prev) => prev.filter((t) => t !== tag));

    try {
      await onRemoveTags(sourceId, [tag]);
      onTagsChanged?.();
    } catch {
      setLocalTags(tags);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && inputValue.trim()) {
      e.preventDefault();
      handleAdd(inputValue);
    } else if (e.key === "Escape") {
      setIsEditing(false);
      setInputValue("");
      setSuggestions([]);
    } else if (e.key === "Backspace" && !inputValue && localTags.length > 0) {
      handleRemove(localTags[localTags.length - 1]);
    }
  };

  return (
    <div ref={containerRef} className="relative">
      <div className="flex items-center gap-1 flex-wrap">
        {localTags.map((tag) => (
          <TagChip
            key={tag}
            tag={tag}
            removable={isEditing}
            onRemove={() => handleRemove(tag)}
            size="sm"
          />
        ))}

        {isEditing ? (
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Add tag..."
            className="bg-transparent text-xs text-white/80 outline-none placeholder:text-white/30 w-20 min-w-[60px]"
          />
        ) : (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsEditing(true);
            }}
            className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] text-white/30 hover:text-white/50 hover:bg-white/5 transition-colors"
          >
            <Plus className="w-2.5 h-2.5" />
            <span>tag</span>
          </button>
        )}
      </div>

      {suggestions.length > 0 && isEditing && (
        <div className="absolute left-0 top-full mt-1 w-40 py-1 bg-zinc-900 border border-white/10 rounded-lg shadow-xl z-50">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              onClick={(e) => {
                e.stopPropagation();
                handleAdd(suggestion);
              }}
              className="w-full px-3 py-1.5 text-xs text-left text-white/70 hover:bg-white/10"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
