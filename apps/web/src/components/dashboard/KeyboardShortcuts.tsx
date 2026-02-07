"use client";

import React, { useState, useEffect, useCallback } from "react";
import { X, Keyboard, Grid, LayoutTemplate, Move } from "lucide-react";
import { LayoutMode } from "@/lib/types/dashboard";

interface KeyBinding {
  keys: string[];
  action: string;
  description: string;
  category: "navigation" | "layout" | "widgets" | "system";
}

const KEY_BINDINGS: KeyBinding[] = [
  // Navigation
  {
    keys: ["Mod", "j"],
    action: "focusLeft",
    description: "Focus tile left",
    category: "navigation",
  },
  {
    keys: ["Mod", "k"],
    action: "focusDown",
    description: "Focus tile down",
    category: "navigation",
  },
  {
    keys: ["Mod", "l"],
    action: "focusRight",
    description: "Focus tile right",
    category: "navigation",
  },
  {
    keys: ["Mod", "i"],
    action: "focusUp",
    description: "Focus tile up",
    category: "navigation",
  },
  {
    keys: ["Mod", "Shift", "j"],
    action: "moveLeft",
    description: "Move tile left",
    category: "navigation",
  },
  {
    keys: ["Mod", "Shift", "k"],
    action: "moveDown",
    description: "Move tile down",
    category: "navigation",
  },
  {
    keys: ["Mod", "Shift", "l"],
    action: "moveRight",
    description: "Move tile right",
    category: "navigation",
  },
  {
    keys: ["Mod", "Shift", "i"],
    action: "moveUp",
    description: "Move tile up",
    category: "navigation",
  },

  // Layout modes
  {
    keys: ["Mod", "m"],
    action: "layoutManual",
    description: "Manual (free) layout",
    category: "layout",
  },
  {
    keys: ["Mod", "e"],
    action: "layoutMaster",
    description: "Master layout (left)",
    category: "layout",
  },
  {
    keys: ["Mod", "v"],
    action: "layoutMasterV",
    description: "Master layout (top)",
    category: "layout",
  },
  {
    keys: ["Mod", "g"],
    action: "layoutGrid",
    description: "Grid layout",
    category: "layout",
  },
  {
    keys: ["Mod", "c"],
    action: "layoutColumns",
    description: "Columns layout",
    category: "layout",
  },
  {
    keys: ["Mod", "r"],
    action: "layoutRows",
    description: "Rows layout",
    category: "layout",
  },
  {
    keys: ["Mod", "f"],
    action: "layoutMonocle",
    description: "Monocle (fullscreen) layout",
    category: "layout",
  },

  // Widget actions
  {
    keys: ["Mod", "n"],
    action: "addWidget",
    description: "Add new widget",
    category: "widgets",
  },
  {
    keys: ["Mod", "q"],
    action: "closeWidget",
    description: "Close focused widget",
    category: "widgets",
  },
  {
    keys: ["Mod", "Return"],
    action: "swapMaster",
    description: "Swap with master",
    category: "widgets",
  },

  // System
  {
    keys: ["Mod", "?"],
    action: "showHelp",
    description: "Toggle cheat sheet",
    category: "system",
  },
  {
    keys: ["Mod", "t"],
    action: "addTab",
    description: "Create new tab",
    category: "system",
  },
  {
    keys: ["Mod", "1-9"],
    action: "switchTab",
    description: "Switch to tab N",
    category: "system",
  },
  {
    keys: ["Mod", "d"],
    action: "toggleDarkMode",
    description: "Toggle dark/light mode",
    category: "system",
  },
  {
    keys: ["Mod", "b"],
    action: "toggleSidebar",
    description: "Toggle sidebar",
    category: "system",
  },
];

interface KeyboardShortcutsProps {
  isOpen: boolean;
  onClose: () => void;
}

const KeyboardShortcuts: React.FC<KeyboardShortcutsProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  const categories = {
    navigation: { title: "Navigation", icon: Move },
    layout: { title: "Layout Modes", icon: Grid },
    widgets: { title: "Widget Actions", icon: LayoutTemplate },
    system: { title: "System", icon: Keyboard },
  };

  const getBindingsByCategory = (cat: string) =>
    KEY_BINDINGS.filter((b) => b.category === cat);

  const renderKey = (key: string) => {
    const isMod = key === "Mod";

    return (
      <kbd
        key={key}
        className={`inline-flex items-center justify-center min-w-[28px] h-6 px-2 text-[10px] font-bold border transition-all font-mono uppercase tracking-wider
          ${
            isMod
              ? "bg-industrial-900 dark:bg-white text-white dark:text-industrial-900 border-industrial-800 dark:border-industrial-200"
              : "bg-industrial-50 dark:bg-industrial-800 text-industrial-700 dark:text-industrial-300 border-industrial-200 dark:border-industrial-700"
          }`}
      >
        {isMod
          ? typeof navigator !== "undefined" &&
            navigator.platform.includes("Mac")
            ? "⌘"
            : "Alt"
          : key}
      </kbd>
    );
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="w-full max-w-4xl max-h-[85vh] bg-white dark:bg-industrial-925 border border-industrial-200 dark:border-industrial-800 overflow-hidden animate-in zoom-in-95 duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-8 py-6 border-b border-industrial-100 dark:border-industrial-800 bg-industrial-50 dark:bg-industrial-900">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-industrial-900 dark:bg-white">
                <Keyboard className="w-5 h-5 text-white dark:text-industrial-900" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-industrial-900 dark:text-white tracking-tight uppercase font-mono">
                  Keyboard Shortcuts
                </h2>
                <p className="text-xs text-industrial-500 dark:text-industrial-400 mt-0.5 font-mono tracking-wider">
                  i3-style window management
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-industrial-100 dark:hover:bg-industrial-800 text-industrial-400 hover:text-industrial-900 dark:hover:text-white transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-8 overflow-y-auto max-h-[calc(85vh-120px)] bg-white dark:bg-industrial-925">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(categories).map(([catKey, cat]) => {
              const bindings = getBindingsByCategory(catKey);
              const Icon = cat.icon;

              return (
                <div
                  key={catKey}
                  className="bg-industrial-50 dark:bg-industrial-900 p-5 border border-industrial-100 dark:border-industrial-800"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-industrial-100 dark:bg-industrial-800">
                      <Icon className="w-4 h-4 text-industrial-600 dark:text-industrial-400" />
                    </div>
                    <h3 className="font-bold text-industrial-900 dark:text-white uppercase text-[10px] tracking-widest font-mono">
                      {cat.title}
                    </h3>
                  </div>

                  <div className="space-y-2">
                    {bindings.map((binding, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between py-2 px-3 hover:bg-industrial-100 dark:hover:bg-industrial-800 transition-all group"
                      >
                        <span className="text-xs text-industrial-600 dark:text-industrial-400 group-hover:text-industrial-900 dark:group-hover:text-white transition-colors">
                          {binding.description}
                        </span>
                        <div className="flex items-center gap-1">
                          {binding.keys.map((key, kidx) => (
                            <React.Fragment key={kidx}>
                              {renderKey(key)}
                              {kidx < binding.keys.length - 1 && (
                                <span className="text-industrial-300 dark:text-industrial-600 mx-0.5 text-xs">
                                  +
                                </span>
                              )}
                            </React.Fragment>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Footer tip */}
          <div className="mt-6 p-4 bg-industrial-100 dark:bg-industrial-900 border border-industrial-200 dark:border-industrial-800">
            <p className="text-center text-xs text-industrial-600 dark:text-industrial-400 font-mono">
              Press{" "}
              <kbd className="mx-1 px-2 py-0.5 bg-industrial-900 dark:bg-white text-white dark:text-industrial-900 font-bold text-[10px]">
                {typeof navigator !== "undefined" &&
                navigator.platform.includes("Mac")
                  ? "⌘"
                  : "Alt"}
              </kbd>{" "}
              +{" "}
              <kbd className="mx-1 px-2 py-0.5 bg-industrial-50 dark:bg-industrial-800 text-industrial-700 dark:text-industrial-300 border border-industrial-200 dark:border-industrial-700 font-bold text-[10px]">
                ?
              </kbd>{" "}
              anytime to toggle this cheat sheet
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Hook for keyboard shortcuts
export function useKeyboardShortcuts({
  onLayoutChange,
  onAddWidget,
  onCloseWidget,
  onAddTab,
  onSwitchTab,
  onToggleDarkMode,
  onToggleSidebar,
  onToggleHelp,
  onFocusWidget,
  onMoveWidget,
  onSwapMaster,
  focusedWidgetIndex,
  widgetCount,
}: {
  onLayoutChange: (mode: LayoutMode) => void;
  onAddWidget: () => void;
  onCloseWidget: () => void;
  onAddTab: () => void;
  onSwitchTab: (index: number) => void;
  onToggleDarkMode: () => void;
  onToggleSidebar: () => void;
  onToggleHelp: () => void;
  onFocusWidget: (direction: "left" | "right" | "up" | "down") => void;
  onMoveWidget: (direction: "left" | "right" | "up" | "down") => void;
  onSwapMaster: () => void;
  focusedWidgetIndex: number;
  widgetCount: number;
}) {
  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Check for modifier key (Alt on Windows/Linux, Cmd on Mac)
      const modKey = navigator.platform.includes("Mac") ? e.metaKey : e.altKey;

      if (!modKey) return;

      const key = e.key.toLowerCase();

      // Prevent default for our shortcuts
      const shortcuts = [
        "j",
        "k",
        "l",
        "i",
        "m",
        "e",
        "v",
        "g",
        "c",
        "r",
        "f",
        "n",
        "q",
        "t",
        "d",
        "b",
        "?",
        "enter",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
      ];
      if (shortcuts.includes(key) || (key >= "1" && key <= "9")) {
        e.preventDefault();
      }

      // Navigation with Shift
      if (e.shiftKey) {
        switch (key) {
          case "j":
            onMoveWidget("left");
            break;
          case "k":
            onMoveWidget("down");
            break;
          case "l":
            onMoveWidget("right");
            break;
          case "i":
            onMoveWidget("up");
            break;
        }
        return;
      }

      // Focus navigation (vim-like)
      switch (key) {
        case "j":
          onFocusWidget("left");
          break;
        case "k":
          onFocusWidget("down");
          break;
        case "l":
          onFocusWidget("right");
          break;
        case "i":
          onFocusWidget("up");
          break;

        // Layout modes
        case "m":
          onLayoutChange(LayoutMode.MANUAL);
          break;
        case "e":
          onLayoutChange(LayoutMode.MASTER);
          break;
        case "v":
          onLayoutChange(LayoutMode.MASTER_V);
          break;
        case "g":
          onLayoutChange(LayoutMode.GRID);
          break;
        case "c":
          onLayoutChange(LayoutMode.COLUMNS);
          break;
        case "r":
          onLayoutChange(LayoutMode.ROWS);
          break;
        case "f":
          onLayoutChange(LayoutMode.MONOCLE);
          break;

        // Widget actions
        case "n":
          onAddWidget();
          break;
        case "q":
          onCloseWidget();
          break;
        case "enter":
          onSwapMaster();
          break;

        // System
        case "t":
          onAddTab();
          break;
        case "d":
          onToggleDarkMode();
          break;
        case "b":
          onToggleSidebar();
          break;
        case "?":
          onToggleHelp();
          break;

        // Tab switching (1-9)
        default:
          if (key >= "1" && key <= "9") {
            onSwitchTab(parseInt(key) - 1);
          }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    onLayoutChange,
    onAddWidget,
    onCloseWidget,
    onAddTab,
    onSwitchTab,
    onToggleDarkMode,
    onToggleSidebar,
    onToggleHelp,
    onFocusWidget,
    onMoveWidget,
    onSwapMaster,
    focusedWidgetIndex,
    widgetCount,
  ]);
}

export default KeyboardShortcuts;
