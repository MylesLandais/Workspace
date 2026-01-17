/**
 * Dashboard Type Definitions
 *
 * Unified type system merging grid-stuff-main and omni-dash prototypes
 */

export enum WidgetType {
  TEXT = "TEXT",
  IMAGE = "IMAGE",
  CHART = "CHART",
  IFRAME = "IFRAME",
  AI = "AI",
  FEED = "FEED",
  READER = "READER",
  SEARCH = "SEARCH",
  MERMAID = "MERMAID",
  MASONRY = "MASONRY",
  TAG_MONITOR = "TAG_MONITOR",
  SOURCES = "SOURCES",
}

export enum LayoutMode {
  MANUAL = "MANUAL",
  MASTER = "MASTER",
  MASTER_V = "MASTER_V",
  GRID = "GRID",
  MONOCLE = "MONOCLE",
  COLUMNS = "COLUMNS",
  ROWS = "ROWS",
}

export interface Widget {
  id: string;
  type: WidgetType;
  title: string;
  content: string;
  config?: Record<string, unknown>;
}

export type DashboardTabType = "grid" | "canvas";

export interface DashboardTab {
  id: string;
  label: string;
  type?: DashboardTabType;
  widgets: Widget[];
  layout: LayoutItem[];
  layoutMode?: LayoutMode;
  canvasData?: unknown;
}

export interface LayoutItem {
  i: string;
  x: number;
  y: number;
  w: number;
  h: number;
  minW?: number;
  minH?: number;
}

export type ToolbarActionType =
  | "ADD_WIDGET"
  | "ADD_TAB"
  | "ADD_CANVAS"
  | "COLLAB"
  | "THEME"
  | "SAVE_LAYOUT"
  | "SETTINGS"
  | "HELP"
  | "RESET"
  | "CUSTOMIZE"
  | "TOGGLE_TILING"
  | "TOGGLE_NAV_POS";

export interface ToolbarItem {
  id: ToolbarActionType;
  label: string;
  iconName: string;
  isVisible: boolean;
}

export interface FeedNode {
  id: string;
  title: string;
  type: "feed" | "folder";
  url?: string;
  isOpen?: boolean;
  children?: FeedNode[];
}

export type SidebarSectionId =
  | "WORKSPACE_TABS"
  | "NAV"
  | "FEEDS"
  | "TAGS"
  | "VIEWS";

export interface SidebarSection {
  id: SidebarSectionId;
  title: string;
  isVisible: boolean;
}

export interface Tag {
  id: string;
  label: string;
  color: string;
}

export interface SavedBoard {
  id: string;
  name: string;
  timestamp: number;
  tabs: DashboardTab[];
}

export type NavPosition = "sidebar" | "top";

export type SidebarPosition = "left" | "right" | "top" | "bottom";

// Collaboration Types

export interface CollabUser {
  id: string;
  name: string;
  color: string;
  cursor: { x: number; y: number } | null;
}

export interface ChatMessage {
  id: string;
  userId: string;
  userName: string;
  userColor: string;
  text: string;
  timestamp: number;
}

export interface CollaborationState {
  isConnected: boolean;
  roomId: string | null;
  userId: string | null;
  userName: string | null;
  userColor: string | null;
  users: CollabUser[];
  chatMessages: ChatMessage[];
  followingUserId: string | null;
  followedBy: string[];
  error: string | null;
}
