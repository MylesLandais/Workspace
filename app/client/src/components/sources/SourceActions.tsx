"use client";

import { useState, useRef, useEffect } from "react";
import { MoreHorizontal, Pause, Play, FolderInput, Trash2 } from "lucide-react";
import type { Source } from "@/lib/types/sources";

interface SourceActionsProps {
  source: Source;
  onPause: (id: string) => void;
  onMove: (id: string) => void;
  onDelete: (id: string) => void;
}

export function SourceActions({ source, onPause, onMove, onDelete }: SourceActionsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-1.5 rounded hover:bg-white/5 text-app-muted hover:text-app-text transition-colors"
      >
        <MoreHorizontal className="w-4 h-4" />
      </button>

      {isOpen && (
        <div className="absolute z-50 right-0 top-full mt-1 w-40 bg-zinc-900 border border-white/10 rounded-xl shadow-xl overflow-hidden">
          <button
            onClick={() => {
              onPause(source.id);
              setIsOpen(false);
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-app-muted hover:bg-white/5 hover:text-app-text transition-colors"
          >
            {source.isPaused ? (
              <>
                <Play className="w-4 h-4" />
                Resume
              </>
            ) : (
              <>
                <Pause className="w-4 h-4" />
                Pause
              </>
            )}
          </button>
          <button
            onClick={() => {
              onMove(source.id);
              setIsOpen(false);
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-app-muted hover:bg-white/5 hover:text-app-text transition-colors"
          >
            <FolderInput className="w-4 h-4" />
            Move to folder
          </button>
          <button
            onClick={() => {
              onDelete(source.id);
              setIsOpen(false);
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Unsubscribe
          </button>
        </div>
      )}
    </div>
  );
}
