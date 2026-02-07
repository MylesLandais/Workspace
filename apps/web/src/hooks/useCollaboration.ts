/**
 * useCollaboration Hook (Yjs Version)
 *
 * Handles real-time CRDT collaboration for dashboard
 * Ported from grid-stuff-main prototype
 */

import { useState, useEffect, useCallback, useRef } from "react";
import * as Y from "yjs";
import { WebsocketProvider } from "y-websocket";
import { DashboardTab } from "@/lib/types/dashboard";

interface CollabUser {
  id: string;
  name: string;
  color: string;
  cursor: { x: number; y: number } | null;
}

interface ChatMessage {
  id: string;
  userId: string;
  userName: string;
  userColor: string;
  text: string;
  timestamp: number;
}

interface CollaborationState {
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

interface UseCollaborationOptions {
  wsUrl?: string;
  onBoardSync?: (state: DashboardTab[]) => void;
  currentBoard?: DashboardTab[];
}

export function useCollaboration(options: UseCollaborationOptions = {}) {
  const {
    wsUrl = typeof window !== "undefined"
      ? `ws://${window.location.hostname}:3001`
      : "ws://localhost:3001",
    onBoardSync,
  } = options;

  const [state, setState] = useState<CollaborationState>({
    isConnected: false,
    roomId: null,
    userId: null,
    userName: null,
    userColor: null,
    users: [],
    chatMessages: [],
    followingUserId: null,
    followedBy: [],
    error: null,
  });

  const ydocRef = useRef<Y.Doc>(new Y.Doc());
  const providerRef = useRef<WebsocketProvider | null>(null);

  // Connect to Yjs Room
  const joinRoom = useCallback(
    (roomId: string, userName?: string) => {
      if (providerRef.current) {
        providerRef.current.destroy();
      }

      try {
        console.log(`[Collab] Connecting to room: ${roomId}`);
        const provider = new WebsocketProvider(wsUrl, roomId, ydocRef.current);
        providerRef.current = provider;

        // Generate Identity
        const userId = provider.awareness.clientID.toString();
        const userColor =
          "#" + Math.floor(Math.random() * 16777215).toString(16);
        const name = userName || `User ${userId.slice(-4)}`;

        // Update Local State with Identity
        setState((prev) => ({
          ...prev,
          roomId,
          userId,
          userName: name,
          userColor,
          isConnected: true,
        }));

        // Set Awareness (Presence)
        provider.awareness.setLocalStateField("user", {
          name,
          color: userColor,
          cursor: null,
        });

        // Handle Connection Status
        provider.on("status", (event: { status: string }) => {
          const connected = event.status === "connected";
          setState((prev) => ({
            ...prev,
            isConnected: connected,
            error: connected ? null : "Disconnected from server",
          }));
        });

        // Handle Awareness Updates (Cursors, Users)
        provider.awareness.on("change", () => {
          const users: CollabUser[] = [];
          provider.awareness.getStates().forEach((stateData, clientID) => {
            const state = stateData as {
              user?: {
                name: string;
                color: string;
                cursor: { x: number; y: number } | null;
              };
            };
            if (clientID.toString() !== userId && state.user) {
              users.push({
                id: clientID.toString(),
                name: state.user.name,
                color: state.user.color,
                cursor: state.user.cursor,
              });
            }
          });
          setState((prev) => ({ ...prev, users }));
        });

        // Handle Shared Board State
        const yTabs = ydocRef.current.getArray<DashboardTab>("tabs");
        yTabs.observe(() => {
          if (roomId === "lobby") return;
          if (onBoardSync) {
            onBoardSync(yTabs.toArray());
          }
        });

        // Initial sync
        provider.on("sync", (isSynced: boolean) => {
          if (
            isSynced &&
            yTabs.length === 0 &&
            options.currentBoard &&
            options.currentBoard.length > 0
          ) {
            if (roomId !== "lobby") {
              yTabs.insert(0, options.currentBoard);
            }
          } else if (isSynced) {
            if (roomId !== "lobby" && onBoardSync && yTabs.length > 0) {
              onBoardSync(yTabs.toArray());
            }
          }
        });

        // Handle Chat
        const yChat = ydocRef.current.getArray<ChatMessage>("chat");
        yChat.observe(() => {
          setState((prev) => ({
            ...prev,
            chatMessages: yChat.toArray().slice(-100),
          }));
        });
      } catch (err) {
        console.error("[Collab] Connection Error:", err);
        setState((prev) => ({
          ...prev,
          error: "Failed to connect to collaboration server",
        }));
      }
    },
    [wsUrl, onBoardSync, options.currentBoard],
  );

  // Leave Room
  const leaveRoom = useCallback(() => {
    if (providerRef.current) {
      providerRef.current.destroy();
      providerRef.current = null;
    }
    ydocRef.current = new Y.Doc();

    setState((prev) => ({
      ...prev,
      roomId: null,
      userId: null,
      isConnected: false,
      users: [],
      chatMessages: [],
    }));
  }, []);

  // Update Cursor
  const sendCursorPosition = useCallback(
    (x: number, y: number) => {
      if (!providerRef.current || !state.userId) return;

      providerRef.current.awareness.setLocalStateField("user", {
        name: state.userName,
        color: state.userColor,
        cursor: { x, y },
      });
    },
    [state.userId, state.userName, state.userColor],
  );

  // Send Chat
  const sendChatMessage = useCallback(
    (text: string) => {
      if (!text.trim() || !state.userId) return;

      const yChat = ydocRef.current.getArray<ChatMessage>("chat");
      const msg: ChatMessage = {
        id: Date.now().toString(),
        userId: state.userId,
        userName: state.userName || "Unknown",
        userColor: state.userColor || "#ccc",
        text,
        timestamp: Date.now(),
      };
      yChat.push([msg]);
    },
    [state.userId, state.userName, state.userColor],
  );

  // Sync Board (Manual push)
  const syncBoardState = useCallback((boardState: DashboardTab[]) => {
    const yTabs = ydocRef.current.getArray<DashboardTab>("tabs");

    ydocRef.current.transact(() => {
      if (JSON.stringify(yTabs.toArray()) !== JSON.stringify(boardState)) {
        yTabs.delete(0, yTabs.length);
        yTabs.insert(0, boardState);
      }
    });
  }, []);

  // Connect helper
  const connect = useCallback(() => {
    joinRoom("lobby");
  }, [joinRoom]);

  // Auto-join from URL param
  useEffect(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const room = params.get("room");
    if (room && !state.roomId) {
      console.log("[Collab] Auto-joining room from URL:", room);
      joinRoom(room);
    }
  }, [joinRoom, state.roomId]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (providerRef.current) {
        providerRef.current.destroy();
      }
    };
  }, []);

  // Follow user logic
  const followUser = useCallback((userId: string) => {
    setState((prev) => ({ ...prev, followingUserId: userId }));
  }, []);

  const stopFollowing = useCallback(() => {
    setState((prev) => ({ ...prev, followingUserId: null }));
  }, []);

  const setUserName = useCallback((name: string) => {
    setState((prev) => ({ ...prev, userName: name }));
    if (providerRef.current) {
      const currentState = providerRef.current.awareness.getLocalState();
      if (currentState) {
        providerRef.current.awareness.setLocalState({
          ...currentState,
          user: {
            ...(
              currentState as {
                user: {
                  name: string;
                  color: string;
                  cursor: { x: number; y: number } | null;
                };
              }
            ).user,
            name: name,
          },
        });
      }
    }
  }, []);

  return {
    ...state,
    connect,
    joinRoom,
    leaveRoom,
    sendCursorPosition,
    sendChatMessage,
    followUser,
    stopFollowing,
    syncBoardState,
    setUserName,
  };
}

export default useCollaboration;
