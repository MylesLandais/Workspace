"use client";

import React from "react";
import { X, ArrowUp, ArrowDown, Eye, EyeOff, GripVertical } from "lucide-react";
import { ToolbarItem } from "@/lib/types/dashboard";

interface ConfigureToolbarModalProps {
  isOpen: boolean;
  onClose: () => void;
  items: ToolbarItem[];
  onUpdate: (items: ToolbarItem[]) => void;
}

const ConfigureToolbarModal: React.FC<ConfigureToolbarModalProps> = ({
  isOpen,
  onClose,
  items,
  onUpdate,
}) => {
  if (!isOpen) return null;

  const moveItem = (index: number, direction: "up" | "down") => {
    const newItems = [...items];
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= newItems.length) return;

    [newItems[index], newItems[targetIndex]] = [
      newItems[targetIndex],
      newItems[index],
    ];
    onUpdate(newItems);
  };

  const toggleVisibility = (id: string) => {
    const newItems = items.map((item) =>
      item.id === id ? { ...item, isVisible: !item.isVisible } : item,
    );
    onUpdate(newItems);
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
      <div className="bg-neutral-900 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden border border-neutral-700">
        <div className="p-6 border-b border-neutral-700 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-neutral-100 font-mono">
              Organize Toolbar
            </h2>
            <p className="text-xs text-neutral-500 mt-1 font-medium uppercase tracking-wider">
              Customize your workflow
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-neutral-500 hover:text-neutral-300 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-2 max-h-[60vh] overflow-y-auto">
          {items
            .filter((i) => i.id !== "CUSTOMIZE")
            .map((item, index) => (
              <div
                key={item.id}
                className={`flex items-center gap-4 p-3 rounded-xl border transition-all ${
                  item.isVisible
                    ? "bg-neutral-800 border-neutral-600 shadow-sm"
                    : "bg-neutral-850 border-neutral-700 opacity-60"
                }`}
              >
                <div className="text-neutral-500">
                  <GripVertical className="w-4 h-4" />
                </div>

                <div className="flex-1">
                  <span className="text-sm font-bold text-neutral-200 font-mono">
                    {item.label}
                  </span>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    onClick={() => toggleVisibility(item.id)}
                    className={`p-2 rounded-lg transition-colors ${
                      item.isVisible
                        ? "text-amber-500 hover:bg-amber-500/10"
                        : "text-neutral-500 hover:bg-neutral-700"
                    }`}
                    title={item.isVisible ? "Hide item" : "Show item"}
                  >
                    {item.isVisible ? (
                      <Eye className="w-4 h-4" />
                    ) : (
                      <EyeOff className="w-4 h-4" />
                    )}
                  </button>
                  <div className="h-4 w-px bg-neutral-700 mx-1" />
                  <button
                    onClick={() => moveItem(index, "up")}
                    disabled={index === 0}
                    className="p-2 text-neutral-500 hover:text-amber-500 hover:bg-amber-500/10 rounded-lg disabled:opacity-30 disabled:hover:bg-transparent"
                  >
                    <ArrowUp className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => moveItem(index, "down")}
                    disabled={
                      index ===
                      items.filter((i) => i.id !== "CUSTOMIZE").length - 1
                    }
                    className="p-2 text-neutral-500 hover:text-amber-500 hover:bg-amber-500/10 rounded-lg disabled:opacity-30 disabled:hover:bg-transparent"
                  >
                    <ArrowDown className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
        </div>

        <div className="p-6 bg-neutral-800/50 border-t border-neutral-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-8 py-3 bg-amber-600 text-neutral-900 font-bold rounded-xl hover:bg-amber-500 transition-all font-mono"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfigureToolbarModal;
