"use client";

import React from "react";
import { Plus, X, Hash } from "lucide-react";
import { Tag } from "@/lib/types/dashboard";

const COLORS = [
  "bg-red-500",
  "bg-orange-500",
  "bg-amber-500",
  "bg-emerald-500",
  "bg-indigo-500",
  "bg-violet-500",
  "bg-rose-500",
  "bg-slate-500",
];

interface TagManagerProps {
  tags: Tag[];
  onUpdate: (tags: Tag[]) => void;
  onTagClick?: (tag: Tag) => void;
}

const TagManager: React.FC<TagManagerProps> = ({
  tags,
  onUpdate,
  onTagClick,
}) => {
  const addTag = () => {
    const label = prompt("Enter tag name:");
    if (!label) return;

    const newTag: Tag = {
      id: Math.random().toString(36).substr(2, 9),
      label,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
    };

    onUpdate([...tags, newTag]);
  };

  const removeTag = (id: string) => {
    onUpdate(tags.filter((t) => t.id !== id));
  };

  const handleDragStart = (e: React.DragEvent, tag: Tag) => {
    e.dataTransfer.setData("application/bunny-tag", JSON.stringify(tag));
    e.dataTransfer.effectAllowed = "copy";
  };

  return (
    <div className="flex flex-col gap-2 p-2">
      <div className="flex flex-wrap gap-1.5">
        {tags.map((tag) => (
          <div
            key={tag.id}
            draggable
            onDragStart={(e) => handleDragStart(e, tag)}
            onClick={() => onTagClick?.(tag)}
            className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-white text-[10px] font-bold shadow-sm transition-all hover:scale-105 cursor-pointer group ${tag.color} cursor-grab active:cursor-grabbing`}
          >
            <Hash className="w-2.5 h-2.5 opacity-70" />
            <span>{tag.label}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                removeTag(tag.id);
              }}
              className="ml-1 opacity-0 group-hover:opacity-100 hover:text-white/80 transition-opacity"
              title="Remove Tag"
            >
              <X className="w-2.5 h-2.5" />
            </button>
          </div>
        ))}
      </div>
      {tags.length === 0 && (
        <div className="text-center py-4 text-industrial-400 text-xs italic">
          No tags yet. Create one to get started.
        </div>
      )}
      <button
        onClick={addTag}
        className="mt-2 flex items-center justify-center gap-2 py-2 px-3 text-[10px] font-bold text-industrial-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950 rounded-xl transition-all border-2 border-dashed border-industrial-100 dark:border-industrial-800 hover:border-indigo-100 dark:hover:border-indigo-900"
      >
        <Plus className="w-3 h-3" /> New Tag
      </button>
    </div>
  );
};

export default TagManager;
