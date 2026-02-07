"use client";

import React, { useState } from "react";
import {
  X,
  Type,
  Image,
  BarChart3,
  Globe,
  MessageSquare,
  Search,
  Rss,
  BookOpen,
  Grid3x3,
  FileCode,
  Hash,
  Settings2,
} from "lucide-react";
import { Widget, WidgetType } from "@/lib/types/dashboard";

interface AddWidgetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (widget: Widget) => void;
}

const WIDGET_OPTIONS = [
  {
    type: WidgetType.SEARCH,
    label: "Search Hub",
    icon: Search,
    desc: "Multi-provider search portal",
  },
  {
    type: WidgetType.TEXT,
    label: "Text/Markdown",
    icon: Type,
    desc: "Add formatted text or notes",
  },
  {
    type: WidgetType.AI,
    label: "AI Assistant",
    icon: MessageSquare,
    desc: "Real-time AI query widget",
  },
  {
    type: WidgetType.FEED,
    label: "RSS Feed",
    icon: Rss,
    desc: "Display articles from RSS feeds",
  },
  {
    type: WidgetType.READER,
    label: "Reader View",
    icon: BookOpen,
    desc: "Clean article reading experience",
  },
  {
    type: WidgetType.CHART,
    label: "Smart Chart",
    icon: BarChart3,
    desc: "AI-generated data visualization",
  },
  {
    type: WidgetType.IFRAME,
    label: "Live Website",
    icon: Globe,
    desc: "Embed any web page via iframe",
  },
  {
    type: WidgetType.IMAGE,
    label: "Image Gallery",
    icon: Image,
    desc: "Display images from URLs",
  },
  {
    type: WidgetType.MASONRY,
    label: "Masonry Wall",
    icon: Grid3x3,
    desc: "Grid of images or cards",
  },
  {
    type: WidgetType.MERMAID,
    label: "Mermaid Diagram",
    icon: FileCode,
    desc: "Render Mermaid diagrams",
  },
  {
    type: WidgetType.TAG_MONITOR,
    label: "Tag Monitor",
    icon: Hash,
    desc: "Track tagged content",
  },
  {
    type: WidgetType.SOURCES,
    label: "Source Manager",
    icon: Settings2,
    desc: "Manage content subscriptions",
  },
];

const AddWidgetModal: React.FC<AddWidgetModalProps> = ({
  isOpen,
  onClose,
  onAdd,
}) => {
  const [selectedType, setSelectedType] = useState<WidgetType | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedType || !title) return;

    onAdd({
      id: `w-${Date.now()}`,
      type: selectedType,
      title,
      content,
    });

    // Reset and close
    setTitle("");
    setContent("");
    setSelectedType(null);
    onClose();
  };

  const getContentLabel = () => {
    switch (selectedType) {
      case WidgetType.IFRAME:
        return "Website URL";
      case WidgetType.FEED:
        return "RSS Feed URL";
      case WidgetType.IMAGE:
        return "Image URL";
      case WidgetType.CHART:
        return "Chart Data Topic";
      case WidgetType.MERMAID:
        return "Mermaid Diagram Code";
      case WidgetType.SEARCH:
        return "Initial Search Term (Optional)";
      case WidgetType.TAG_MONITOR:
        return "Tag ID to Monitor";
      default:
        return "Initial Content";
    }
  };

  const getContentPlaceholder = () => {
    switch (selectedType) {
      case WidgetType.IFRAME:
        return "https://www.wikipedia.org";
      case WidgetType.FEED:
        return "https://example.com/rss";
      case WidgetType.IMAGE:
        return "https://picsum.photos/800/600";
      case WidgetType.CHART:
        return "Monthly Revenue";
      case WidgetType.MERMAID:
        return "graph TD\n  A[Start] --> B[End]";
      case WidgetType.SEARCH:
        return "e.g. quantum physics";
      case WidgetType.TAG_MONITOR:
        return "tag-id-123";
      default:
        return "Enter content here...";
    }
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-industrial-925 w-full max-w-3xl max-h-[85vh] overflow-hidden animate-in fade-in zoom-in duration-200 border border-industrial-200 dark:border-industrial-800 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-industrial-100 dark:border-industrial-800 flex items-center justify-between bg-industrial-50 dark:bg-industrial-900 shrink-0">
          <h2 className="text-lg font-bold text-industrial-900 dark:text-white uppercase tracking-wider font-mono">
            New Widget
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-industrial-400 hover:text-industrial-900 dark:hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form
          onSubmit={handleSubmit}
          className="p-6 bg-white dark:bg-industrial-925 overflow-y-auto flex-1"
        >
          <div className="mb-6">
            <label className="block text-[10px] font-medium text-industrial-500 dark:text-industrial-400 mb-4 uppercase tracking-widest font-mono">
              Select Widget Type
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {WIDGET_OPTIONS.map((opt) => {
                const Icon = opt.icon;
                return (
                  <button
                    key={opt.type}
                    type="button"
                    onClick={() => setSelectedType(opt.type)}
                    className={`flex flex-col items-start p-4 border transition-all text-left ${
                      selectedType === opt.type
                        ? "border-industrial-900 dark:border-white bg-industrial-50 dark:bg-industrial-800"
                        : "border-industrial-200 dark:border-industrial-700 hover:border-industrial-400 dark:hover:border-industrial-500 hover:bg-industrial-50 dark:hover:bg-industrial-850"
                    }`}
                  >
                    <div className="bg-industrial-100 dark:bg-industrial-800 text-industrial-600 dark:text-industrial-400 p-2 mb-3">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="font-medium text-industrial-900 dark:text-white text-sm mb-1 truncate w-full">
                      {opt.label}
                    </span>
                    <span className="text-xs text-industrial-500 dark:text-industrial-400 line-clamp-2">
                      {opt.desc}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {selectedType && (
            <div className="space-y-4 animate-in slide-in-from-top-2">
              <div>
                <label className="block text-[10px] font-medium text-industrial-500 dark:text-industrial-400 mb-1 uppercase tracking-widest font-mono">
                  Widget Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Search Engine Hub"
                  className="w-full px-4 py-2 border border-industrial-200 dark:border-industrial-700 bg-white dark:bg-industrial-900 focus:ring-1 focus:ring-industrial-900 dark:focus:ring-white focus:border-industrial-900 dark:focus:border-white outline-none transition-all text-industrial-900 dark:text-white font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-[10px] font-medium text-industrial-500 dark:text-industrial-400 mb-1 uppercase tracking-widest font-mono">
                  {getContentLabel()}
                </label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder={getContentPlaceholder()}
                  className="w-full px-4 py-2 border border-industrial-200 dark:border-industrial-700 bg-white dark:bg-industrial-900 focus:ring-1 focus:ring-industrial-900 dark:focus:ring-white focus:border-industrial-900 dark:focus:border-white outline-none transition-all min-h-[80px] text-industrial-900 dark:text-white font-mono text-sm resize-y"
                />
              </div>

              <div className="pt-4 flex items-center gap-3">
                <button
                  type="submit"
                  className="flex-1 bg-industrial-900 dark:bg-white text-white dark:text-industrial-900 font-bold py-3 hover:bg-industrial-800 dark:hover:bg-industrial-100 transition-colors uppercase tracking-wider text-sm font-mono"
                >
                  Create Widget
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-6 py-3 text-industrial-600 dark:text-industrial-400 font-medium hover:bg-industrial-50 dark:hover:bg-industrial-800 transition-colors uppercase tracking-wider text-sm font-mono"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default AddWidgetModal;
