"use client";

/**
 * Dashboard Page - Main Application View
 *
 * Unified dashboard merging grid-stuff-main and omni-dash prototypes
 * Features:
 * - Customizable grid layout with React Grid Layout
 * - Multiple tabs with grid and canvas modes
 * - Real-time collaboration via Yjs
 * - Widget system for extensible content
 * - Matcha theme integration
 */

import React, {
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef,
} from "react";
import { useRouter } from "next/navigation";
import { Responsive, WidthProvider } from "react-grid-layout";
import {
  Plus,
  X,
  Moon,
  Sun,
  Columns,
  Grid,
  Maximize,
  MousePointer2,
  Rows as RowsIcon,
  LayoutTemplate,
  List,
  Users,
  Pen,
  Eraser,
  RotateCcw,
  Save,
  Trash2,
  PenTool,
} from "lucide-react";
import { ReactSketchCanvasRef } from "react-sketch-canvas";
import {
  DashboardTab,
  LayoutItem,
  LayoutMode,
  Widget,
  WidgetType,
  ToolbarItem,
  ToolbarActionType,
  SavedBoard,
  NavPosition,
  Tag,
} from "@/lib/types/dashboard";
import WidgetFrame from "@/components/dashboard/WidgetFrame";
import DrawingCanvas from "@/components/dashboard/DrawingCanvas";
import CollabCursors from "@/components/dashboard/CollabCursors";
import ContextMenu, {
  ContextMenuItem,
} from "@/components/dashboard/ContextMenu";
import Sidebar from "@/components/dashboard/Sidebar";
import ThemeCustomizer from "@/components/dashboard/ThemeCustomizer";
import KeyboardShortcuts, {
  useKeyboardShortcuts,
} from "@/components/dashboard/KeyboardShortcuts";
import GroupBoardModal from "@/components/dashboard/GroupBoardModal";
import AddWidgetModal from "@/components/dashboard/AddWidgetModal";
import useCollaboration from "@/hooks/useCollaboration";
import { useSession } from "@/lib/auth-client";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";

const ResponsiveGridLayout = WidthProvider(Responsive);

const INITIAL_TABS: DashboardTab[] = [
  {
    id: "tab-1",
    label: "Main Workspace",
    type: "grid",
    layoutMode: LayoutMode.GRID,
    widgets: [
      {
        id: "w-1",
        type: WidgetType.TEXT,
        title: "Welcome Note",
        content:
          "# Welcome to Bunny Dashboard\n\nDrag widgets to rearrange. Add new widgets with the + button.",
      },
      {
        id: "w-2",
        type: WidgetType.MASONRY,
        title: "UnixPorn Feed",
        content: "unixporn",
        config: { subreddit: "unixporn", limit: 20 },
      },
      {
        id: "w-3",
        type: WidgetType.CHART,
        title: "Activity",
        content: "weekly activity",
      },
    ],
    layout: [
      { i: "w-1", x: 0, y: 0, w: 4, h: 4 },
      { i: "w-2", x: 4, y: 0, w: 8, h: 10 },
      { i: "w-3", x: 0, y: 4, w: 4, h: 6 },
    ],
  },
];

export default function DashboardPage() {
  const { data: session, isPending } = useSession();
  const router = useRouter();

  // Protect dashboard - require authentication
  useEffect(() => {
    if (!isPending && !session) {
      router.replace("/auth");
    }
  }, [session, isPending, router]);

  const [tabs, setTabs] = useState<DashboardTab[]>(() => {
    if (typeof window === "undefined") return INITIAL_TABS;
    try {
      const saved = localStorage.getItem("bunny-dashboard-state-v1");
      return saved ? JSON.parse(saved) : INITIAL_TABS;
    } catch (e) {
      return INITIAL_TABS;
    }
  });

  const [activeTabId, setActiveTabId] = useState<string>(
    () => tabs[0]?.id || "tab-1",
  );
  const [darkMode, setDarkMode] = useState<boolean>(true);
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    type: "TAB" | "WIDGET";
    targetId: string;
  } | null>(null);

  // UI state
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSidebarUnlocked, setIsSidebarUnlocked] = useState(false);
  const [isThemeOpen, setIsThemeOpen] = useState(false);
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [isGroupBoardOpen, setIsGroupBoardOpen] = useState(false);
  const [isAddWidgetOpen, setIsAddWidgetOpen] = useState(false);
  const [navPosition, setNavPosition] = useState<NavPosition>("sidebar");
  const [focusedWidgetIndex, setFocusedWidgetIndex] = useState(0);

  // Sidebar data
  const [savedBoards, setSavedBoards] = useState<SavedBoard[]>(() => {
    if (typeof window === "undefined") return [];
    const saved = localStorage.getItem("bunny-saved-boards-v1");
    return saved ? JSON.parse(saved) : [];
  });

  const [toolbarItems] = useState<ToolbarItem[]>([
    {
      id: "ADD_WIDGET",
      label: "Add Widget",
      iconName: "Plus",
      isVisible: true,
    },
    { id: "ADD_TAB", label: "New Tab", iconName: "Plus", isVisible: true },
    {
      id: "ADD_CANVAS",
      label: "New Canvas",
      iconName: "PenTool",
      isVisible: true,
    },
    {
      id: "COLLAB",
      label: "Collaboration",
      iconName: "Users",
      isVisible: true,
    },
    { id: "THEME", label: "Themes", iconName: "Palette", isVisible: true },
    { id: "HELP", label: "Shortcuts", iconName: "Keyboard", isVisible: true },
    {
      id: "CUSTOMIZE",
      label: "Customize",
      iconName: "Settings2",
      isVisible: true,
    },
  ]);

  // Canvas state
  const canvasRef = useRef<ReactSketchCanvasRef | null>(null);
  const [canvasStrokeColor, setCanvasStrokeColor] = useState("#000000");
  const [canvasStrokeWidth, setCanvasStrokeWidth] = useState(4);
  const [isEraser, setIsEraser] = useState(false);

  // Collaboration
  const collaboration = useCollaboration({
    onBoardSync: (state) => {
      setTabs(state);
    },
    currentBoard: tabs,
  });

  const activeTab = useMemo(
    () => tabs.find((t) => t.id === activeTabId) || tabs[0] || INITIAL_TABS[0],
    [tabs, activeTabId],
  );

  // Persist state
  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("bunny-dashboard-state-v1", JSON.stringify(tabs));
    }
  }, [tabs]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem(
        "bunny-saved-boards-v1",
        JSON.stringify(savedBoards),
      );
    }
  }, [savedBoards]);

  // Apply dark mode
  useEffect(() => {
    if (typeof document !== "undefined") {
      if (darkMode) {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    }
  }, [darkMode]);

  // Sync collaboration
  useEffect(() => {
    if (collaboration.roomId) {
      collaboration.syncBoardState(tabs);
    }
  }, [tabs, collaboration.roomId]);

  const setLayoutMode = (mode: LayoutMode) => {
    setTabs((prev) =>
      prev.map((tab) =>
        tab.id === activeTabId ? { ...tab, layoutMode: mode } : tab,
      ),
    );
  };

  const handleAddTab = () => {
    const newTab: DashboardTab = {
      id: `tab-${Date.now()}`,
      label: `Tab ${tabs.length + 1}`,
      type: "grid",
      widgets: [],
      layout: [],
      layoutMode: LayoutMode.GRID,
    };
    setTabs([...tabs, newTab]);
    setActiveTabId(newTab.id);
  };

  const handleAddCanvas = () => {
    const newTab: DashboardTab = {
      id: `canvas-${Date.now()}`,
      label: `Canvas ${tabs.length + 1}`,
      type: "canvas",
      widgets: [],
      layout: [],
      canvasData: null,
    };
    setTabs([...tabs, newTab]);
    setActiveTabId(newTab.id);
  };

  // Track cursor for collaboration
  useEffect(() => {
    if (!collaboration.roomId || typeof window === "undefined") return;
    const handleMouseMove = (e: MouseEvent) => {
      collaboration.sendCursorPosition(e.clientX, e.clientY);
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [collaboration.roomId, collaboration.sendCursorPosition]);

  // Keyboard shortcuts
  useKeyboardShortcuts({
    onLayoutChange: setLayoutMode,
    onAddWidget: () => setIsAddWidgetOpen(true),
    onCloseWidget: () => {
      if (activeTab.widgets.length > 0) {
        handleDeleteWidget(activeTab.widgets[focusedWidgetIndex]?.id);
      }
    },
    onAddTab: handleAddTab,
    onSwitchTab: (index) => {
      if (tabs[index]) setActiveTabId(tabs[index].id);
    },
    onToggleDarkMode: () => setDarkMode(!darkMode),
    onToggleSidebar: () => setIsSidebarCollapsed(!isSidebarCollapsed),
    onToggleHelp: () => setIsHelpOpen(!isHelpOpen),
    onFocusWidget: (direction) => {
      const maxIndex = activeTab.widgets.length - 1;
      if (direction === "left" || direction === "up") {
        setFocusedWidgetIndex(Math.max(0, focusedWidgetIndex - 1));
      } else {
        setFocusedWidgetIndex(Math.min(maxIndex, focusedWidgetIndex + 1));
      }
    },
    onMoveWidget: (direction) => {
      console.log("Move widget", direction);
    },
    onSwapMaster: () => {
      console.log("Swap master");
    },
    focusedWidgetIndex,
    widgetCount: activeTab.widgets.length,
  });

  const handleLayoutChange = (layout: LayoutItem[]) => {
    setTabs((prev) =>
      prev.map((tab) => (tab.id === activeTabId ? { ...tab, layout } : tab)),
    );
  };

  const handleAddWidget = (widget?: Widget) => {
    const newWidget: Widget = widget || {
      id: `w-${Date.now()}`,
      type: WidgetType.TEXT,
      title: "New Widget",
      content: "",
    };

    const newLayoutItem: LayoutItem = {
      i: newWidget.id,
      x: 0,
      y: Infinity,
      w: 4,
      h: 4,
    };

    setTabs((prev) =>
      prev.map((tab) =>
        tab.id === activeTabId
          ? {
              ...tab,
              widgets: [...tab.widgets, newWidget],
              layout: [...tab.layout, newLayoutItem],
            }
          : tab,
      ),
    );
  };

  const handleToolbarAction = (action: ToolbarActionType) => {
    switch (action) {
      case "ADD_WIDGET":
        setIsAddWidgetOpen(true);
        break;
      case "ADD_TAB":
        handleAddTab();
        break;
      case "ADD_CANVAS":
        handleAddCanvas();
        break;
      case "COLLAB":
        setIsGroupBoardOpen(true);
        break;
      case "THEME":
        setIsThemeOpen(true);
        break;
      case "HELP":
        setIsHelpOpen(true);
        break;
      case "CUSTOMIZE":
        setIsSidebarUnlocked(!isSidebarUnlocked);
        break;
      case "TOGGLE_NAV_POS":
        setNavPosition(navPosition === "sidebar" ? "top" : "sidebar");
        break;
      case "SAVE_LAYOUT":
        const name = prompt("Save board as:");
        if (name) {
          const newBoard: SavedBoard = {
            id: `board-${Date.now()}`,
            name,
            timestamp: Date.now(),
            tabs: tabs,
          };
          setSavedBoards((prev) => [...prev, newBoard]);
        }
        break;
    }
  };

  const handleLoadBoard = (boardTabs: DashboardTab[]) => {
    setTabs(boardTabs);
    setActiveTabId(boardTabs[0]?.id || "tab-1");
  };

  const handleDeleteBoard = (boardId: string) => {
    setSavedBoards((prev) => prev.filter((b) => b.id !== boardId));
  };

  const handleTagClick = (tag: Tag) => {
    console.log("Tag clicked:", tag);
  };

  const handleDeleteWidget = (widgetId: string) => {
    setTabs((prev) =>
      prev.map((tab) =>
        tab.id === activeTabId
          ? { ...tab, widgets: tab.widgets.filter((w) => w.id !== widgetId) }
          : tab,
      ),
    );
  };

  const handleCloseTab = (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (tabs.length <= 1) return;
    const newTabs = tabs.filter((t) => t.id !== id);
    setTabs(newTabs);
    if (activeTabId === id) setActiveTabId(newTabs[0].id);
  };

  const handleTabContextMenu = (e: React.MouseEvent, tabId: string) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      type: "TAB",
      targetId: tabId,
    });
  };

  const handleWidgetContextMenu = (e: React.MouseEvent, widgetId: string) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      type: "WIDGET",
      targetId: widgetId,
    });
  };

  const getContextMenuItems = (): ContextMenuItem[] => {
    if (!contextMenu) return [];

    if (contextMenu.type === "TAB") {
      return [
        {
          label: "Rename Tab",
          icon: Pen,
          action: () => {
            const newName = prompt(
              "New Tab Name:",
              tabs.find((t) => t.id === contextMenu.targetId)?.label,
            );
            if (newName) {
              setTabs((prev) =>
                prev.map((t) =>
                  t.id === contextMenu.targetId ? { ...t, label: newName } : t,
                ),
              );
            }
          },
        },
        {
          label: "Close Tab",
          icon: X,
          color: "text-red-500",
          action: () => {
            if (confirm("Are you sure you want to close this tab?")) {
              const newTabs = tabs.filter((t) => t.id !== contextMenu.targetId);
              if (newTabs.length > 0) {
                setTabs(newTabs);
                if (activeTabId === contextMenu.targetId)
                  setActiveTabId(newTabs[0].id);
              }
            }
          },
        },
      ];
    } else {
      return [
        {
          label: "Rename Widget",
          icon: Pen,
          action: () => {
            const widget = activeTab.widgets.find(
              (w) => w.id === contextMenu.targetId,
            );
            const newTitle = prompt("New Widget Title:", widget?.title);
            if (newTitle) {
              setTabs((prev) =>
                prev.map((t) =>
                  t.id === activeTabId
                    ? {
                        ...t,
                        widgets: t.widgets.map((w) =>
                          w.id === contextMenu.targetId
                            ? { ...w, title: newTitle }
                            : w,
                        ),
                      }
                    : t,
                ),
              );
            }
          },
        },
        {
          label: "Delete Widget",
          icon: Trash2,
          color: "text-red-500",
          action: () => handleDeleteWidget(contextMenu.targetId),
        },
      ];
    }
  };

  // Show loading while checking auth
  if (isPending) {
    return (
      <div className="min-h-screen bg-industrial-50 dark:bg-industrial-950 flex items-center justify-center">
        <div className="text-industrial-600 dark:text-industrial-400">
          Loading dashboard...
        </div>
      </div>
    );
  }

  // Don't render dashboard if not authenticated (redirect will happen)
  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen flex bg-industrial-50 dark:bg-industrial-950 transition-colors">
      {/* Sidebar */}
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        onAction={handleToolbarAction}
        toolbarItems={toolbarItems}
        isUnlocked={isSidebarUnlocked}
        currentTabs={tabs}
        activeTabId={activeTabId}
        onSelectTab={setActiveTabId}
        onRenameTab={(id, label) => {
          setTabs((prev) =>
            prev.map((t) => (t.id === id ? { ...t, label } : t)),
          );
        }}
        onDeleteTab={(id) => {
          if (tabs.length > 1) {
            const newTabs = tabs.filter((t) => t.id !== id);
            setTabs(newTabs);
            if (activeTabId === id) setActiveTabId(newTabs[0].id);
          }
        }}
        boards={savedBoards}
        onLoadBoard={handleLoadBoard}
        onDeleteBoard={handleDeleteBoard}
        onTagClick={handleTagClick}
        navPosition={navPosition}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white dark:bg-industrial-925 border-b border-industrial-200 dark:border-industrial-800 px-6 h-16 flex items-center justify-between shrink-0 shadow-sm">
          {/* Tabs */}
          <nav className="flex items-center gap-0 h-full overflow-x-auto no-scrollbar">
            {tabs.map((tab, idx) => (
              <div
                key={tab.id}
                className={`h-full flex items-center px-4 border-b-2 transition-all cursor-pointer group whitespace-nowrap ${
                  activeTabId === tab.id
                    ? "border-matcha-600 dark:border-matcha-400 bg-matcha-50/50 dark:bg-matcha-900/20"
                    : "border-transparent hover:bg-industrial-100 dark:hover:bg-industrial-900/30"
                }`}
                onClick={() => setActiveTabId(tab.id)}
                onContextMenu={(e) => handleTabContextMenu(e, tab.id)}
              >
                <span className="text-xs font-black mr-2 text-industrial-300 dark:text-industrial-600">
                  {idx + 1}
                </span>
                <span
                  className={`text-sm font-bold ${
                    activeTabId === tab.id
                      ? "text-industrial-900 dark:text-white"
                      : "text-industrial-400 group-hover:text-industrial-600 dark:group-hover:text-industrial-300"
                  }`}
                >
                  {tab.label}
                </span>
                {tabs.length > 1 && (
                  <button
                    onClick={(e) => handleCloseTab(tab.id, e)}
                    className="ml-2 p-1 opacity-0 group-hover:opacity-100 text-industrial-400 hover:text-red-500 transition-all"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
            <button
              onClick={handleAddTab}
              className="p-2 ml-4 text-industrial-400 hover:text-matcha-600 dark:hover:text-matcha-400 transition-all hover:scale-110"
            >
              <Plus className="w-5 h-5" />
            </button>
          </nav>

          {/* Controls */}
          <div className="flex items-center gap-2">
            {activeTab.type === "canvas" ? (
              <>
                <button
                  onClick={() => setIsEraser(false)}
                  className={`p-2 rounded-md transition-all ${!isEraser ? "bg-matcha-100 dark:bg-matcha-900/30 text-matcha-600 dark:text-matcha-400" : "text-industrial-500 hover:text-industrial-900 dark:hover:text-white"}`}
                  title="Pen Tool"
                >
                  <Pen className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setIsEraser(true)}
                  className={`p-2 rounded-md transition-all ${isEraser ? "bg-matcha-100 dark:bg-matcha-900/30 text-matcha-600 dark:text-matcha-400" : "text-industrial-500 hover:text-industrial-900 dark:hover:text-white"}`}
                  title="Eraser Tool"
                >
                  <Eraser className="w-4 h-4" />
                </button>
                <input
                  type="color"
                  value={canvasStrokeColor}
                  onChange={(e) => setCanvasStrokeColor(e.target.value)}
                  className="w-8 h-8 rounded cursor-pointer"
                  title="Brush Color"
                  disabled={isEraser}
                />
                <select
                  value={canvasStrokeWidth}
                  onChange={(e) => setCanvasStrokeWidth(Number(e.target.value))}
                  className="bg-transparent text-xs font-bold text-industrial-600 dark:text-industrial-300 outline-none cursor-pointer px-2 py-1 rounded border border-industrial-200 dark:border-industrial-700"
                  title="Brush Size"
                >
                  <option value={2}>Thin</option>
                  <option value={4}>Normal</option>
                  <option value={8}>Thick</option>
                  <option value={16}>Marker</option>
                </select>
                <button
                  onClick={() => canvasRef.current?.undo()}
                  className="p-2 text-industrial-500 hover:text-industrial-900 dark:hover:text-white transition-all"
                  title="Undo"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
                <button
                  onClick={() => {
                    if (confirm("Clear canvas?"))
                      canvasRef.current?.clearCanvas();
                  }}
                  className="p-2 text-industrial-500 hover:text-red-500 transition-all"
                  title="Clear Canvas"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </>
            ) : (
              <>
                {[
                  {
                    mode: LayoutMode.MANUAL,
                    icon: MousePointer2,
                    label: "Free",
                  },
                  { mode: LayoutMode.MASTER, icon: Columns, label: "Master" },
                  {
                    mode: LayoutMode.MASTER_V,
                    icon: LayoutTemplate,
                    label: "Split",
                  },
                  { mode: LayoutMode.GRID, icon: Grid, label: "Grid" },
                ].map(({ mode, icon: Icon, label }) => (
                  <button
                    key={mode}
                    onClick={() => setLayoutMode(mode)}
                    className={`p-2 rounded-md transition-all ${
                      activeTab.layoutMode === mode
                        ? "bg-matcha-100 dark:bg-matcha-900/30 text-matcha-600 dark:text-matcha-400 shadow-sm"
                        : "text-industrial-500 hover:text-industrial-700 dark:hover:text-industrial-300"
                    }`}
                    title={label}
                  >
                    <Icon className="w-4 h-4" />
                  </button>
                ))}
              </>
            )}

            <div className="w-px h-6 bg-industrial-200 dark:border-industrial-800 mx-2" />

            <button
              onClick={() => setIsAddWidgetOpen(true)}
              className="p-2 bg-matcha-600 hover:bg-matcha-700 text-white rounded-md transition-all"
              title="Add Widget"
            >
              <Plus className="w-4 h-4" />
            </button>

            <button
              onClick={handleAddCanvas}
              className="p-2 bg-industrial-100 dark:bg-industrial-900 text-industrial-500 hover:text-industrial-900 dark:hover:text-white transition-all rounded-md border border-industrial-200 dark:border-industrial-800"
              title="New Canvas"
            >
              <PenTool className="w-4 h-4" />
            </button>

            <button
              onClick={() => setIsGroupBoardOpen(true)}
              className={`p-2 rounded-md transition-all border relative ${
                collaboration.roomId
                  ? "bg-matcha-500 text-white border-matcha-500"
                  : "bg-industrial-100 dark:bg-industrial-900 text-industrial-500 hover:text-industrial-900 dark:hover:text-white border-industrial-200 dark:border-industrial-800"
              }`}
              title={
                collaboration.roomId
                  ? `In room: ${collaboration.roomId}`
                  : "Collaboration"
              }
            >
              <Users className="w-4 h-4" />
              {collaboration.roomId && collaboration.users.length > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-industrial-900 dark:bg-white text-[8px] text-white dark:text-industrial-900 font-black flex items-center justify-center rounded-full">
                  {collaboration.users.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 bg-industrial-100 dark:bg-industrial-900 text-industrial-500 hover:text-industrial-900 dark:hover:text-white transition-all rounded-md border border-industrial-200 dark:border-industrial-800"
            >
              {darkMode ? (
                <Sun className="w-4 h-4" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
            </button>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden p-2 bg-industrial-100 dark:bg-industrial-950">
          {activeTab.type !== "canvas" ? (
            <ResponsiveGridLayout
              className="layout"
              layouts={{ lg: activeTab.layout }}
              breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
              cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
              rowHeight={80}
              draggableHandle=".drag-handle"
              onLayoutChange={handleLayoutChange}
              margin={[8, 8]}
              containerPadding={[0, 0]}
              useCSSTransforms={true}
              compactType={null}
              preventCollision={false}
            >
              {activeTab.widgets.map((widget) => (
                <div
                  key={widget.id}
                  onContextMenu={(e) => handleWidgetContextMenu(e, widget.id)}
                >
                  <WidgetFrame
                    widget={widget}
                    onDelete={() => handleDeleteWidget(widget.id)}
                  />
                </div>
              ))}
            </ResponsiveGridLayout>
          ) : (
            <div className="h-full w-full overflow-hidden rounded-lg border border-industrial-200 dark:border-industrial-700">
              <DrawingCanvas
                key={activeTab.id}
                canvasRef={canvasRef}
                initialData={activeTab.canvasData}
                strokeColor={canvasStrokeColor}
                strokeWidth={canvasStrokeWidth}
                isEraser={isEraser}
                onChange={(newData) => {
                  setTabs((prev) =>
                    prev.map((t) =>
                      t.id === activeTabId ? { ...t, canvasData: newData } : t,
                    ),
                  );
                }}
              />
            </div>
          )}
        </main>
      </div>

      {/* Collaboration Cursors */}
      {collaboration.roomId && <CollabCursors users={collaboration.users} />}

      {/* Context Menu */}
      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          items={getContextMenuItems()}
          onClose={() => setContextMenu(null)}
        />
      )}

      {/* Modals */}
      <ThemeCustomizer
        isOpen={isThemeOpen}
        onClose={() => setIsThemeOpen(false)}
      />

      <KeyboardShortcuts
        isOpen={isHelpOpen}
        onClose={() => setIsHelpOpen(false)}
      />

      <GroupBoardModal
        isOpen={isGroupBoardOpen}
        onClose={() => setIsGroupBoardOpen(false)}
        isConnected={collaboration.isConnected}
        roomId={collaboration.roomId}
        userId={collaboration.userId}
        userName={collaboration.userName}
        userColor={collaboration.userColor}
        users={collaboration.users}
        error={collaboration.error}
        chatMessages={collaboration.chatMessages}
        followingUserId={collaboration.followingUserId}
        followedBy={collaboration.followedBy}
        onConnect={collaboration.connect}
        onJoinRoom={collaboration.joinRoom}
        onLeaveRoom={collaboration.leaveRoom}
        onSendMessage={collaboration.sendChatMessage}
        onFollowUser={collaboration.followUser}
        onStopFollowing={collaboration.stopFollowing}
        onSetUserName={collaboration.setUserName}
      />

      <AddWidgetModal
        isOpen={isAddWidgetOpen}
        onClose={() => setIsAddWidgetOpen(false)}
        onAdd={(widget) => {
          handleAddWidget(widget);
          setIsAddWidgetOpen(false);
        }}
      />
    </div>
  );
}
