"use client";

import React from "react";
import { X, GripVertical, Maximize2, ExternalLink } from "lucide-react";
import { Widget, WidgetType } from "@/lib/types/dashboard";

// Widget component imports (we'll create these)
import TextWidget from "./widgets/TextWidget";
import ImageWidget from "./widgets/ImageWidget";
import ReaderWidget from "./widgets/ReaderWidget";
import AIWidget from "./widgets/AIWidget";
import FeedWidget from "./widgets/FeedWidget";
import MasonryWallWidget from "./widgets/MasonryWallWidget";
import SearchWidget from "./widgets/SearchWidget";
import ChartWidget from "./widgets/ChartWidget";
import IframeWidget from "./widgets/IframeWidget";
import MermaidWidget from "./widgets/MermaidWidget";
import TagMonitorWidget from "./widgets/TagMonitorWidget";

interface WidgetFrameProps {
  widget: Widget;
  onDelete: () => void;
  onSelectArticle?: (article: unknown, source: string) => void;
}

const WidgetFrame: React.FC<WidgetFrameProps> = ({
  widget,
  onDelete,
  onSelectArticle,
}) => {
  const handlePopOut = () => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams();
    params.set("mode", "standalone");
    params.set("type", widget.type);
    params.set("title", widget.title);
    params.set("content", widget.content);

    const url = `${window.location.origin}${window.location.pathname}?${params.toString()}`;
    const features =
      "width=600,height=800,menubar=no,toolbar=no,location=no,status=no,resizable=yes,scrollbars=yes";

    window.open(url, `popout-${widget.id}`, features);
  };

  const renderWidget = () => {
    const props = { content: widget.content, config: widget.config };

    switch (widget.type) {
      case WidgetType.TEXT:
        return <TextWidget {...props} />;
      case WidgetType.IMAGE:
        return <ImageWidget {...props} />;
      case WidgetType.READER:
        return <ReaderWidget {...props} />;
      case WidgetType.AI:
        return <AIWidget {...props} />;
      case WidgetType.FEED:
        return <FeedWidget {...props} onSelectArticle={onSelectArticle} />;
      case WidgetType.MASONRY:
        return <MasonryWallWidget {...props} />;
      case WidgetType.SEARCH:
        return <SearchWidget {...props} />;
      case WidgetType.CHART:
        return <ChartWidget {...props} />;
      case WidgetType.IFRAME:
        return <IframeWidget {...props} />;
      case WidgetType.MERMAID:
        return <MermaidWidget {...props} />;
      case WidgetType.TAG_MONITOR:
        return <TagMonitorWidget tagId={widget.content} />;
      case WidgetType.SOURCES:
        return <SourcesWidget content={widget.content} />;
      default:
        return <div className="p-4">Unknown widget type</div>;
    }
  };

  return (
    <div className="h-full w-full flex flex-col bg-white dark:bg-industrial-900 rounded-lg border border-industrial-200 dark:border-industrial-700 shadow-sm overflow-hidden group">
      {/* Widget Header */}
      <div className="shrink-0 flex items-center justify-between px-3 py-2 border-b border-industrial-200 dark:border-industrial-800 bg-industrial-50 dark:bg-industrial-925">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className="drag-handle cursor-move p-1 hover:bg-industrial-200 dark:hover:bg-industrial-800 rounded transition-colors">
            <GripVertical className="w-4 h-4 text-industrial-400" />
          </div>
          <h3 className="text-sm font-bold text-industrial-900 dark:text-white truncate">
            {widget.title}
          </h3>
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handlePopOut}
            className="shrink-0 p-1 text-industrial-400 hover:text-industrial-900 dark:hover:text-white transition-colors rounded hover:bg-industrial-200 dark:hover:bg-industrial-800"
            title="Pop out widget"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
          {(widget.type === WidgetType.IFRAME ||
            widget.type === WidgetType.FEED) &&
            widget.content && (
              <a
                href={widget.content}
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0 p-1 text-industrial-400 hover:text-industrial-900 dark:hover:text-white transition-colors rounded hover:bg-industrial-200 dark:hover:bg-industrial-800"
                title="Open in new tab"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          <button
            onClick={onDelete}
            className="shrink-0 p-1 text-industrial-400 hover:text-red-500 dark:hover:text-red-400 transition-colors rounded hover:bg-industrial-200 dark:hover:bg-industrial-800"
            aria-label="Delete widget"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Widget Content */}
      <div className="flex-1 overflow-hidden">{renderWidget()}</div>
    </div>
  );
};

export default WidgetFrame;
