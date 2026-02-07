"use client";

import React, { useEffect, useRef } from "react";
import { type LucideIcon } from "lucide-react";

export interface ContextMenuItem {
  label: string;
  icon?: LucideIcon;
  action: () => void;
  color?: string;
}

interface ContextMenuProps {
  x: number;
  y: number;
  items: ContextMenuItem[];
  onClose: () => void;
}

const ContextMenu: React.FC<ContextMenuProps> = ({ x, y, items, onClose }) => {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onClose]);

  const style: React.CSSProperties = {
    top: y,
    left: x,
  };

  return (
    <div
      ref={menuRef}
      className="fixed z-50 min-w-[160px] bg-white dark:bg-industrial-900 border border-industrial-200 dark:border-industrial-700 rounded-lg shadow-xl py-1 animate-in fade-in zoom-in-95 duration-100"
      style={style}
    >
      {items.map((item, index) => (
        <button
          key={index}
          onClick={() => {
            item.action();
            onClose();
          }}
          className={`w-full text-left px-3 py-2 text-sm flex items-center gap-2 hover:bg-industrial-100 dark:hover:bg-industrial-800 transition-colors ${
            item.color || "text-industrial-700 dark:text-industrial-300"
          }`}
        >
          {item.icon && <item.icon className="w-4 h-4" />}
          {item.label}
        </button>
      ))}
    </div>
  );
};

export default ContextMenu;
