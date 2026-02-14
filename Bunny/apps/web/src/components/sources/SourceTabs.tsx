"use client";

interface SourceTabsProps {
  activeTab: "organize" | "discover";
  onTabChange: (tab: "organize" | "discover") => void;
}

export function SourceTabs({ activeTab, onTabChange }: SourceTabsProps) {
  return (
    <div className="flex gap-1 mb-6 border-b border-white/5">
      <button
        onClick={() => onTabChange("organize")}
        className={`px-4 py-2 text-sm font-medium transition-colors relative ${
          activeTab === "organize"
            ? "text-app-text"
            : "text-app-muted hover:text-app-text"
        }`}
      >
        Organize Feeds
        {activeTab === "organize" && (
          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-app-accent" />
        )}
      </button>
      <button
        onClick={() => onTabChange("discover")}
        className={`px-4 py-2 text-sm font-medium transition-colors relative ${
          activeTab === "discover"
            ? "text-app-text"
            : "text-app-muted hover:text-app-text"
        }`}
      >
        Discover
        {activeTab === "discover" && (
          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-app-accent" />
        )}
      </button>
    </div>
  );
}
