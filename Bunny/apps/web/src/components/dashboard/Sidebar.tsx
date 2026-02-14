"use client";

import React, { useState, useEffect, useMemo } from "react";
import * as Icons from "lucide-react";
import {
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Settings2,
  Lock,
  Unlock,
  GripHorizontal,
  Plus,
  Monitor,
  X,
  Edit3,
  ExternalLink,
} from "lucide-react";
import {
  ToolbarItem,
  ToolbarActionType,
  FeedNode,
  SidebarSection,
  SidebarSectionId,
  Tag,
  SavedBoard,
  DashboardTab,
  NavPosition,
} from "@/lib/types/dashboard";
import FeedTree from "./FeedTree";
import TagManager from "./TagManager";
import ViewManager from "./ViewManager";
import { useUserSources } from "@/lib/hooks/use-user-sources";

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  onAction: (id: ToolbarActionType) => void;
  toolbarItems: ToolbarItem[];
  isUnlocked?: boolean;
  currentTabs: DashboardTab[];
  activeTabId: string;
  onSelectTab: (id: string) => void;
  onRenameTab: (id: string, label: string) => void;
  onDeleteTab: (id: string) => void;
  boards: SavedBoard[];
  onLoadBoard: (tabs: DashboardTab[]) => void;
  onDeleteBoard: (id: string) => void;
  onTagClick?: (tag: Tag) => void;
  navPosition: NavPosition;
}

const DEFAULT_SECTIONS: SidebarSection[] = [
  { id: "WORKSPACE_TABS", title: "Active Workspaces", isVisible: true },
  { id: "NAV", title: "Navigation", isVisible: true },
  { id: "FEEDS", title: "Feeds & Sources", isVisible: true },
  { id: "VIEWS", title: "Saved Boards", isVisible: true },
  { id: "TAGS", title: "Workspace Tags", isVisible: true },
];

const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  onToggle,
  onAction,
  toolbarItems,
  isUnlocked = false,
  currentTabs,
  activeTabId,
  onSelectTab,
  onRenameTab,
  onDeleteTab,
  boards,
  onLoadBoard,
  onDeleteBoard,
  onTagClick,
  navPosition,
}) => {
  const [sections, setSections] = useState<SidebarSection[]>(() => {
    if (typeof window === "undefined") return DEFAULT_SECTIONS;
    const saved = localStorage.getItem("bunny-sidebar-sections-v1");
    return saved ? JSON.parse(saved) : DEFAULT_SECTIONS;
  });

  const { sources, feedGroups, isLoading: sourcesLoading } = useUserSources();

  // Transform sources and groups into FeedNode tree structure
  const feeds = useMemo(() => {
    if (sourcesLoading || !sources.length) {
      return [];
    }

    // Group sources by their group
    const groupMap = new Map<string, FeedNode>();

    // Create folder nodes for each group
    feedGroups.forEach((group) => {
      groupMap.set(group.id, {
        id: group.id,
        title: group.name,
        type: "folder",
        isOpen: true,
        children: [],
      });
    });

    // Add sources to their respective groups
    sources.forEach((source) => {
      const feedNode: FeedNode = {
        id: source.id,
        title: source.subredditName || source.name,
        type: "feed",
        url: source.url,
      };

      if (source.groupId && groupMap.has(source.groupId)) {
        groupMap.get(source.groupId)!.children!.push(feedNode);
      }
    });

    return Array.from(groupMap.values()).filter(
      (group) => group.children && group.children.length > 0,
    );
  }, [sources, feedGroups, sourcesLoading]);

  const [tags, setTags] = useState<Tag[]>(() => {
    if (typeof window === "undefined") return [];
    const saved = localStorage.getItem("bunny-tags-v1");
    return saved
      ? JSON.parse(saved)
      : [
          { id: "t-1", label: "Priority", color: "bg-red-500" },
          { id: "t-2", label: "Research", color: "bg-indigo-500" },
        ];
  });

  const [draggedSectionIdx, setDraggedSectionIdx] = useState<number | null>(
    null,
  );
  const [dragOverSectionIdx, setDragOverSectionIdx] = useState<number | null>(
    null,
  );
  const [renamingId, setRenamingId] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    localStorage.setItem("bunny-sidebar-sections-v1", JSON.stringify(sections));
  }, [sections]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    localStorage.setItem("bunny-tags-v1", JSON.stringify(tags));
  }, [tags]);

  const handleSectionDragOver = (e: React.DragEvent, index: number) => {
    if (!isUnlocked || draggedSectionIdx === null) return;
    e.preventDefault();
    if (dragOverSectionIdx !== index) setDragOverSectionIdx(index);
  };

  const renderTabsSection = () => (
    <div
      className={`flex flex-col gap-1 w-full transition-opacity duration-300 ${navPosition === "top" ? "opacity-30 grayscale pointer-events-none" : ""}`}
    >
      {currentTabs.map((tab) => (
        <div
          key={tab.id}
          onClick={() => onSelectTab(tab.id)}
          onDoubleClick={() => setRenamingId(tab.id)}
          className={`group flex items-center gap-3 p-2.5 rounded-xl cursor-pointer transition-all border-2 ${
            activeTabId === tab.id
              ? "bg-indigo-600 border-indigo-600 text-white shadow-lg"
              : "bg-white dark:bg-industrial-800 border-transparent hover:border-industrial-100 dark:hover:border-industrial-700 text-industrial-500 dark:text-industrial-400"
          }`}
        >
          <Monitor
            className={`w-4 h-4 shrink-0 ${activeTabId === tab.id ? "text-indigo-100" : "text-industrial-400"}`}
          />
          {!isCollapsed && (
            <div className="flex-1 min-w-0">
              {renamingId === tab.id ? (
                <input
                  autoFocus
                  className="w-full bg-white dark:bg-industrial-900 text-industrial-900 dark:text-white px-1 text-xs font-bold rounded outline-none"
                  defaultValue={tab.label}
                  onBlur={(e) => {
                    onRenameTab(tab.id, e.target.value);
                    setRenamingId(null);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") e.currentTarget.blur();
                    if (e.key === "Escape") setRenamingId(null);
                  }}
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span className="text-[12px] font-bold truncate block">
                  {tab.label}
                </span>
              )}
            </div>
          )}
          {!isCollapsed && (
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setRenamingId(tab.id);
                }}
                className="p-1 hover:bg-black/10 dark:hover:bg-white/10 rounded"
                title="Rename"
              >
                <Edit3 className="w-3 h-3" />
              </button>
              {currentTabs.length > 1 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteTab(tab.id);
                  }}
                  className="p-1 hover:bg-black/10 dark:hover:bg-white/10 rounded"
                  title="Delete"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          )}
        </div>
      ))}
      {!isCollapsed && (
        <button
          onClick={() => onAction("ADD_TAB")}
          className="mt-2 flex items-center justify-center gap-2 py-2 px-3 text-[10px] font-black uppercase text-industrial-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950 rounded-xl transition-all border-2 border-dashed border-industrial-100 dark:border-industrial-800"
        >
          <Plus className="w-3.5 h-3.5" /> New Workspace
        </button>
      )}
    </div>
  );

  return (
    <aside
      className={`sidebar-transition bg-white dark:bg-industrial-900 border-r border-industrial-200 dark:border-industrial-800 flex flex-col z-[60] sticky top-0 h-screen overflow-hidden ${isCollapsed ? "w-20" : "w-72"} ${isUnlocked ? "ring-2 ring-amber-400" : ""}`}
    >
      <div className="p-4 mb-4 flex items-center justify-between overflow-hidden shrink-0">
        <div className="flex items-center gap-3">
          <div
            className={`transition-all duration-500 ${isUnlocked ? "bg-amber-500" : "bg-indigo-600"} p-2.5 rounded-xl shadow-lg shrink-0`}
          >
            {isUnlocked ? (
              <Unlock className="w-5 h-5 text-white" />
            ) : (
              <LayoutDashboard className="w-5 h-5 text-white" />
            )}
          </div>
          {!isCollapsed && (
            <span className="font-black text-xl tracking-tight text-industrial-800 dark:text-industrial-100">
              Bunny
            </span>
          )}
        </div>
      </div>

      <div className="flex-1 px-2 overflow-y-auto no-scrollbar pb-10 flex flex-col">
        {sections.map((section, idx) => (
          <div
            key={section.id}
            className="flex flex-col relative"
            onDragOver={(e) => handleSectionDragOver(e, idx)}
          >
            {isUnlocked && (
              <div
                draggable
                className="flex items-center gap-2 cursor-grab active:cursor-grabbing p-2 mb-2 bg-industrial-50 dark:bg-industrial-800 rounded-lg border border-industrial-200 dark:border-industrial-700 shadow-sm text-industrial-400"
              >
                <GripHorizontal className="w-4 h-4" />
                <span className="text-[10px] font-black uppercase tracking-widest">
                  {section.title}
                </span>
              </div>
            )}
            {!isUnlocked && !isCollapsed && (
              <div className="px-4 py-2 flex items-center justify-between text-[10px] font-bold text-industrial-400 dark:text-industrial-600 uppercase tracking-widest mb-1 group/sec">
                <span>{section.title}</span>
                {section.id === "WORKSPACE_TABS" && (
                  <button
                    onClick={() => onAction("TOGGLE_NAV_POS")}
                    className="opacity-0 group-hover/sec:opacity-100 hover:text-indigo-600 transition-all p-1"
                    title={
                      navPosition === "sidebar"
                        ? "Undock to Header"
                        : "Restore to Sidebar"
                    }
                  >
                    <ExternalLink className="w-3 h-3" />
                  </button>
                )}
              </div>
            )}

            <div className={isCollapsed ? "flex justify-center" : ""}>
              {section.id === "WORKSPACE_TABS" && renderTabsSection()}
              {section.id === "NAV" && (
                <div className="flex flex-col w-full">
                  {toolbarItems.map((item) => {
                    if (!item.isVisible && !isUnlocked) return null;
                    if (item.id === "ADD_TAB") return null;
                    const Icon =
                      (Icons as unknown as Record<string, React.ElementType>)[
                        item.iconName
                      ] || Icons.HelpCircle;
                    return (
                      <button
                        key={item.id}
                        onClick={() => onAction(item.id)}
                        disabled={isUnlocked && item.id !== "CUSTOMIZE"}
                        className="flex items-center gap-3 p-3 rounded-xl h-12 transition-all text-industrial-500 dark:text-industrial-400 hover:text-indigo-600 hover:bg-industrial-50 dark:hover:bg-industrial-800 disabled:opacity-50"
                      >
                        <Icon className="w-5 h-5 shrink-0" />
                        {!isCollapsed && (
                          <span className="text-sm font-semibold truncate">
                            {item.label}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
              {section.id === "FEEDS" &&
                !isCollapsed &&
                (sourcesLoading ? (
                  <div className="px-4 py-8 text-center">
                    <div className="animate-spin w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full mx-auto mb-2" />
                    <p className="text-xs text-industrial-400">
                      Loading sources...
                    </p>
                  </div>
                ) : (
                  <FeedTree
                    nodes={feeds}
                    onUpdate={() => {
                      // TODO: Implement source mutations when user reorganizes feeds
                      console.log("Feed tree update - not yet implemented");
                    }}
                    onSelect={(node) => {
                      // TODO: Implement feed selection to filter dashboard
                      console.log("Selected feed:", node);
                    }}
                    isUnlocked={isUnlocked}
                  />
                ))}
              {section.id === "TAGS" && !isCollapsed && (
                <TagManager
                  tags={tags}
                  onUpdate={setTags}
                  onTagClick={onTagClick}
                />
              )}
              {section.id === "VIEWS" && !isCollapsed && (
                <ViewManager
                  boards={boards}
                  onSaveCurrent={() => onAction("SAVE_LAYOUT")}
                  onLoadBoard={onLoadBoard}
                  onDeleteBoard={onDeleteBoard}
                />
              )}
            </div>
            <div className="h-6" />
          </div>
        ))}
      </div>

      <div className="p-3 border-t border-industrial-100 dark:border-industrial-800 shrink-0 space-y-1">
        <button
          onClick={() => onAction("CUSTOMIZE")}
          className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all ${
            isUnlocked
              ? "bg-amber-500 text-white"
              : "hover:bg-industrial-50 dark:hover:bg-industrial-800 text-industrial-400"
          }`}
        >
          {isUnlocked ? (
            <Lock className="w-5 h-5" />
          ) : (
            <Settings2 className="w-5 h-5" />
          )}
          {!isCollapsed && (
            <span className="text-xs font-bold uppercase">
              {isUnlocked ? "Lock UI" : "Customize"}
            </span>
          )}
        </button>
        <button
          onClick={onToggle}
          className="w-full flex items-center justify-center p-3 text-industrial-400 hover:bg-industrial-50 dark:hover:bg-industrial-800 rounded-xl"
        >
          {isCollapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <ChevronLeft className="w-5 h-5" />
          )}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
