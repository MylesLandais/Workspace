"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  X,
  Users,
  Link2,
  Copy,
  Check,
  Wifi,
  WifiOff,
  UserPlus,
  Eye,
  EyeOff,
  MessageSquare,
  Send,
  Edit2,
  Save,
} from "lucide-react";
import { CollabUser, ChatMessage } from "@/lib/types/dashboard";

interface GroupBoardModalProps {
  isOpen: boolean;
  onClose: () => void;
  isConnected: boolean;
  roomId: string | null;
  userId: string | null;
  userName: string | null;
  userColor: string | null;
  users: CollabUser[];
  error: string | null;
  chatMessages: ChatMessage[];
  followingUserId: string | null;
  followedBy: string[];
  onConnect: () => void;
  onJoinRoom: (roomId: string, userName?: string) => void;
  onLeaveRoom: () => void;
  onSendMessage: (text: string) => void;
  onFollowUser: (userId: string) => void;
  onStopFollowing: () => void;
  onSetUserName: (name: string) => void;
}

const GroupBoardModal: React.FC<GroupBoardModalProps> = ({
  isOpen,
  onClose,
  isConnected,
  roomId,
  userId,
  userName,
  userColor,
  users,
  error,
  chatMessages,
  followingUserId,
  followedBy,
  onConnect,
  onJoinRoom,
  onLeaveRoom,
  onSendMessage,
  onFollowUser,
  onStopFollowing,
  onSetUserName,
}) => {
  const [inputRoomId, setInputRoomId] = useState("");
  const [inputUserName, setInputUserName] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [copied, setCopied] = useState(false);
  const [isEditingName, setIsEditingName] = useState(false);
  const [editNameInput, setEditNameInput] = useState("");

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages, isOpen]);

  const handleSendMessage = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (chatInput.trim()) {
      onSendMessage(chatInput);
      setChatInput("");
    }
  };

  const generateRoomId = () => {
    if (typeof crypto !== "undefined" && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
      /[xy]/g,
      function (c) {
        const r = (Math.random() * 16) | 0;
        const v = c == "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      },
    );
  };

  const handleCreateRoom = () => {
    const newRoomId = generateRoomId();
    onJoinRoom(newRoomId, inputUserName || undefined);
  };

  const handleJoinRoom = () => {
    if (inputRoomId.trim()) {
      onJoinRoom(inputRoomId.trim(), inputUserName || undefined);
    }
  };

  const copyRoomLink = () => {
    if (roomId && typeof window !== "undefined") {
      navigator.clipboard.writeText(`${window.location.origin}?room=${roomId}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md bg-white dark:bg-industrial-925 border border-industrial-200 dark:border-industrial-800 overflow-hidden animate-in fade-in zoom-in-95 duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-industrial-100 dark:border-industrial-800 bg-industrial-50 dark:bg-industrial-900 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-industrial-900 dark:bg-white">
              <Users className="w-5 h-5 text-white dark:text-industrial-900" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-industrial-900 dark:text-white uppercase tracking-wider font-mono">
                Group Board
              </h2>
              <p className="text-[10px] text-industrial-500 dark:text-industrial-400 font-mono tracking-wider">
                Real-time collaboration
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

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Connection Status */}
          <div className="flex items-center gap-3 p-3 bg-industrial-50 dark:bg-industrial-900 border border-industrial-200 dark:border-industrial-800">
            {isConnected ? (
              <>
                <Wifi className="w-5 h-5 text-green-500" />
                <span className="text-sm font-medium text-green-600 dark:text-green-400">
                  Connected to server
                </span>
              </>
            ) : (
              <>
                <WifiOff className="w-5 h-5 text-industrial-400" />
                <span className="text-sm text-industrial-500">
                  Not connected
                </span>
                <button
                  onClick={onConnect}
                  className="ml-auto px-3 py-1 text-xs font-bold uppercase bg-industrial-900 dark:bg-white text-white dark:text-industrial-900"
                >
                  Connect
                </button>
              </>
            )}
          </div>

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          {roomId ? (
            // In a room
            <div className="space-y-4">
              {/* Room Info */}
              <div className="space-y-2">
                <label className="text-[10px] font-bold uppercase tracking-widest text-industrial-500 font-mono">
                  Room ID
                </label>
                <div className="flex items-center gap-2">
                  <div className="flex-1 p-3 bg-industrial-100 dark:bg-industrial-800 font-mono text-sm text-industrial-900 dark:text-white truncate">
                    {roomId}
                  </div>
                  <button
                    onClick={copyRoomLink}
                    className="p-3 bg-industrial-900 dark:bg-white text-white dark:text-industrial-900 transition-all"
                    title="Copy room link"
                  >
                    {copied ? (
                      <Check className="w-5 h-5" />
                    ) : (
                      <Copy className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>

              {/* Your Info */}
              <div className="flex items-center gap-3 p-3 border border-industrial-200 dark:border-industrial-800 bg-industrial-50 dark:bg-industrial-900/50">
                <div
                  className="w-8 h-8 flex items-center justify-center text-white font-bold text-sm rounded"
                  style={{ backgroundColor: userColor || "#6366f1" }}
                >
                  {userName?.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  {isEditingName ? (
                    <div className="flex gap-2">
                      <input
                        autoFocus
                        type="text"
                        value={editNameInput}
                        onChange={(e) => setEditNameInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            onSetUserName(editNameInput);
                            setIsEditingName(false);
                          }
                        }}
                        className="w-full px-1 py-0.5 text-sm bg-white dark:bg-industrial-800 border border-industrial-300 dark:border-industrial-600 rounded"
                      />
                      <button
                        onClick={() => {
                          onSetUserName(editNameInput);
                          setIsEditingName(false);
                        }}
                        title="Save"
                      >
                        <Save className="w-4 h-4 text-green-500" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between group">
                      <div>
                        <div className="font-medium text-industrial-900 dark:text-white text-sm truncate">
                          {userName}
                        </div>
                        <div className="text-[10px] text-industrial-500 font-mono">
                          You
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          setEditNameInput(userName || "");
                          setIsEditingName(true);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 text-industrial-400 hover:text-industrial-600 dark:hover:text-industrial-300 transition-opacity"
                        title="Edit Name"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Active Users */}
              <div className="space-y-2">
                <label className="text-[10px] font-bold uppercase tracking-widest text-industrial-500 font-mono">
                  Active Users ({users.length + 1})
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {users.map((user) => (
                    <div
                      key={user.id}
                      className="flex items-center gap-3 p-2 bg-industrial-50 dark:bg-industrial-900 border border-transparent hover:border-industrial-200 dark:hover:border-industrial-700 transition-all rounded-sm"
                    >
                      <div
                        className="w-6 h-6 flex items-center justify-center text-white font-bold text-xs"
                        style={{ backgroundColor: user.color }}
                      >
                        {user.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex flex-col">
                        <span className="text-sm text-industrial-700 dark:text-industrial-300 font-medium">
                          {user.name}
                        </span>
                        {followedBy.includes(user.id) && (
                          <span className="text-[9px] text-green-600 dark:text-green-400 font-mono flex items-center gap-1">
                            <Eye className="w-3 h-3" /> Following you
                          </span>
                        )}
                      </div>

                      <div className="ml-auto flex items-center gap-2">
                        {user.cursor && (
                          <span className="text-[10px] text-industrial-400 font-mono hidden sm:inline-block">
                            ({Math.round(user.cursor.x)},{" "}
                            {Math.round(user.cursor.y)})
                          </span>
                        )}

                        {user.id !== userId && (
                          <button
                            onClick={() =>
                              followingUserId === user.id
                                ? onStopFollowing()
                                : onFollowUser(user.id)
                            }
                            className={`p-1.5 rounded-sm transition-all ${followingUserId === user.id ? "bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400" : "text-industrial-400 hover:text-industrial-900 dark:hover:text-white hover:bg-industrial-100 dark:hover:bg-industrial-800"}`}
                            title={
                              followingUserId === user.id
                                ? "Stop following"
                                : "Follow cursor"
                            }
                          >
                            {followingUserId === user.id ? (
                              <EyeOff className="w-4 h-4" />
                            ) : (
                              <Eye className="w-4 h-4" />
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                  {users.length === 0 && (
                    <div className="text-center py-4 text-industrial-400 text-sm italic">
                      Waiting for others to join...
                    </div>
                  )}
                </div>
              </div>

              {/* Chat Section */}
              <div className="flex flex-col h-60 border border-industrial-200 dark:border-industrial-800 bg-industrial-50 dark:bg-industrial-900/50">
                <div className="p-2 border-b border-industrial-200 dark:border-industrial-800 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-industrial-500" />
                  <span className="text-xs font-bold uppercase tracking-wider text-industrial-600 dark:text-industrial-400">
                    Team Chat
                  </span>
                </div>

                <div className="flex-1 overflow-y-auto p-3 space-y-3">
                  {chatMessages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-industrial-400 text-xs">
                      <p>No messages yet.</p>
                      <p>Say hello to the team!</p>
                    </div>
                  ) : (
                    chatMessages.map((msg) => {
                      const isMe = msg.userId === userId;
                      return (
                        <div
                          key={msg.id}
                          className={`flex flex-col ${isMe ? "items-end" : "items-start"}`}
                        >
                          <div className="flex items-center gap-1 mb-1">
                            {!isMe && (
                              <div
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: msg.userColor }}
                              />
                            )}
                            <span className="text-[10px] font-bold text-industrial-500">
                              {msg.userName}
                            </span>
                            <span className="text-[9px] text-industrial-400 ml-1">
                              {new Date(msg.timestamp).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                          </div>
                          <div
                            className={`px-3 py-2 rounded-lg text-xs max-w-[85%] break-words ${
                              isMe
                                ? "bg-industrial-900 dark:bg-white text-white dark:text-industrial-900 rounded-tr-none"
                                : "bg-white dark:bg-industrial-800 text-industrial-800 dark:text-industrial-200 border border-industrial-200 dark:border-industrial-700 rounded-tl-none"
                            }`}
                          >
                            {msg.text}
                          </div>
                        </div>
                      );
                    })
                  )}
                  <div ref={chatEndRef} />
                </div>

                <form
                  onSubmit={handleSendMessage}
                  className="p-2 border-t border-industrial-200 dark:border-industrial-800 bg-white dark:bg-industrial-900 flex gap-2"
                >
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Type a message..."
                    className="flex-1 px-3 py-2 bg-industrial-100 dark:bg-industrial-800 border-none rounded text-xs focus:ring-1 focus:ring-industrial-500 outline-none text-industrial-900 dark:text-white"
                  />
                  <button
                    type="submit"
                    disabled={!chatInput.trim()}
                    className="p-2 bg-industrial-900 dark:bg-white text-white dark:text-industrial-900 rounded hover:opacity-90 disabled:opacity-50 transition-all"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>

              {/* Leave Button */}
              <button
                onClick={onLeaveRoom}
                className="w-full p-3 border border-red-500 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 font-bold uppercase tracking-wider text-sm transition-all"
              >
                Leave Room
              </button>
            </div>
          ) : (
            // Not in a room
            <div className="space-y-4">
              {/* Username Input */}
              <div className="space-y-2">
                <label className="text-[10px] font-bold uppercase tracking-widest text-industrial-500 font-mono">
                  Your Name (optional)
                </label>
                <input
                  type="text"
                  value={inputUserName}
                  onChange={(e) => setInputUserName(e.target.value)}
                  placeholder="Enter your name..."
                  className="w-full p-3 border border-industrial-200 dark:border-industrial-700 bg-white dark:bg-industrial-900 font-mono text-sm text-industrial-900 dark:text-white focus:ring-1 focus:ring-industrial-900 dark:focus:ring-white outline-none transition-all"
                />
              </div>

              {/* Create New Room */}
              <button
                onClick={handleCreateRoom}
                disabled={!isConnected}
                className="w-full p-4 bg-industrial-900 dark:bg-white text-white dark:text-industrial-900 font-bold uppercase tracking-wider text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-industrial-800 dark:hover:bg-industrial-100 transition-all flex items-center justify-center gap-2"
              >
                <UserPlus className="w-5 h-5" />
                Create New Group Board
              </button>

              <div className="flex items-center gap-4">
                <div className="flex-1 h-px bg-industrial-200 dark:bg-industrial-800" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-industrial-400 font-mono">
                  or
                </span>
                <div className="flex-1 h-px bg-industrial-200 dark:bg-industrial-800" />
              </div>

              {/* Join Existing Room */}
              <div className="space-y-2">
                <label className="text-[10px] font-bold uppercase tracking-widest text-industrial-500 font-mono">
                  Join Existing Room
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={inputRoomId}
                    onChange={(e) => setInputRoomId(e.target.value)}
                    placeholder="Enter room ID..."
                    className="flex-1 p-3 border border-industrial-200 dark:border-industrial-700 bg-white dark:bg-industrial-900 font-mono text-sm text-industrial-900 dark:text-white focus:ring-1 focus:ring-industrial-900 dark:focus:ring-white outline-none transition-all"
                  />
                  <button
                    onClick={handleJoinRoom}
                    disabled={!isConnected || !inputRoomId.trim()}
                    className="px-4 py-3 bg-industrial-100 dark:bg-industrial-800 text-industrial-600 dark:text-industrial-400 hover:text-industrial-900 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    <Link2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-industrial-100 dark:border-industrial-800 bg-industrial-50 dark:bg-industrial-900">
          <p className="text-[10px] text-industrial-400 dark:text-industrial-500 font-mono">
            Share the room ID with others to collaborate in real-time. Cursors
            and changes sync automatically.
          </p>
        </div>
      </div>
    </div>
  );
};

export default GroupBoardModal;
