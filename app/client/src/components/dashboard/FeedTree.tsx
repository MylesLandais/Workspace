"use client";

import React from "react";
import {
  Folder,
  FolderOpen,
  Rss,
  ChevronRight,
  ChevronDown,
  Plus,
  Trash2,
} from "lucide-react";
import { FeedNode } from "@/lib/types/dashboard";

interface FeedTreeProps {
  nodes: FeedNode[];
  level?: number;
  onUpdate: (nodes: FeedNode[]) => void;
  onSelect: (node: FeedNode) => void;
  isUnlocked?: boolean;
}

const FeedTree: React.FC<FeedTreeProps> = ({
  nodes,
  level = 0,
  onUpdate,
  onSelect,
  isUnlocked,
}) => {
  const toggleFolder = (id: string) => {
    const updateNodes = (list: FeedNode[]): FeedNode[] => {
      return list.map((node) => {
        if (node.id === id) {
          return { ...node, isOpen: !node.isOpen };
        }
        if (node.children) {
          return { ...node, children: updateNodes(node.children) };
        }
        return node;
      });
    };
    onUpdate(updateNodes(nodes));
  };

  const deleteNode = (id: string) => {
    const filterNodes = (list: FeedNode[]): FeedNode[] => {
      return list
        .filter((node) => node.id !== id)
        .map((node) => ({
          ...node,
          children: node.children ? filterNodes(node.children) : undefined,
        }));
    };
    onUpdate(filterNodes(nodes));
  };

  const handleDragStart = (e: React.DragEvent, node: FeedNode) => {
    e.dataTransfer.setData("application/bunny-feed", JSON.stringify(node));
    e.dataTransfer.effectAllowed = "copy";
  };

  const addNode = (parentId: string, type: "feed" | "folder") => {
    const title = prompt(`Enter ${type} name:`);
    if (!title) return;

    let url = "";
    if (type === "feed") {
      url = prompt("Enter RSS URL:") || "";
      if (!url) return;
    }

    const newNode: FeedNode = {
      id: Math.random().toString(36).substr(2, 9),
      title,
      type,
      url: type === "feed" ? url : undefined,
      isOpen: type === "folder" ? true : undefined,
      children: type === "folder" ? [] : undefined,
    };

    if (parentId === "root") {
      onUpdate([...nodes, newNode]);
    } else {
      const updateNodes = (list: FeedNode[]): FeedNode[] => {
        return list.map((node) => {
          if (node.id === parentId) {
            return {
              ...node,
              children: [...(node.children || []), newNode],
              isOpen: true,
            };
          }
          if (node.children) {
            return { ...node, children: updateNodes(node.children) };
          }
          return node;
        });
      };
      onUpdate(updateNodes(nodes));
    }
  };

  return (
    <div className="flex flex-col w-full select-none">
      {nodes.map((node) => (
        <div key={node.id} className="flex flex-col">
          <div
            draggable
            onDragStart={(e) => handleDragStart(e, node)}
            className={`group flex items-center gap-2 py-1.5 px-2 rounded-lg cursor-pointer transition-all hover:bg-industrial-50 dark:hover:bg-industrial-800 relative ${
              level > 0 ? "ml-3" : ""
            } cursor-grab active:cursor-grabbing`}
            onClick={() =>
              node.type === "folder" ? toggleFolder(node.id) : onSelect(node)
            }
          >
            {level > 0 && (
              <div className="absolute left-[-10px] top-0 bottom-0 w-px bg-industrial-100 dark:bg-industrial-800 group-hover:bg-industrial-200 dark:group-hover:bg-industrial-700" />
            )}

            <div className="w-4 h-4 flex items-center justify-center text-industrial-400">
              {node.type === "folder" ? (
                node.isOpen ? (
                  <ChevronDown className="w-3 h-3" />
                ) : (
                  <ChevronRight className="w-3 h-3" />
                )
              ) : null}
            </div>

            <div
              className={`shrink-0 ${node.type === "folder" ? "text-amber-500" : "text-indigo-500"}`}
            >
              {node.type === "folder" ? (
                node.isOpen ? (
                  <FolderOpen className="w-4 h-4" />
                ) : (
                  <Folder className="w-4 h-4" />
                )
              ) : (
                <Rss className="w-4 h-4" />
              )}
            </div>

            <span
              className={`text-[13px] truncate flex-1 ${node.type === "folder" ? "font-semibold text-industrial-700 dark:text-industrial-300" : "text-industrial-600 dark:text-industrial-400"}`}
            >
              {node.title}
            </span>

            <div className="hidden group-hover:flex items-center gap-1">
              {node.type === "folder" && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    addNode(node.id, "feed");
                  }}
                  className="p-1 text-industrial-400 hover:text-indigo-600 hover:bg-white dark:hover:bg-industrial-900 rounded transition-colors"
                  title="Add Feed"
                >
                  <Plus className="w-3 h-3" />
                </button>
              )}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteNode(node.id);
                }}
                className="p-1 text-industrial-400 hover:text-red-500 hover:bg-white dark:hover:bg-industrial-900 rounded transition-colors"
                title="Delete"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          </div>

          {node.type === "folder" && node.isOpen && (
            <div className="border-l-2 border-industrial-50 dark:border-industrial-800 ml-4 animate-in fade-in slide-in-from-top-1 duration-200">
              <FeedTree
                nodes={node.children || []}
                level={level + 1}
                onUpdate={(newChildren) => {
                  const updateList = (list: FeedNode[]): FeedNode[] => {
                    return list.map((n) =>
                      n.id === node.id ? { ...n, children: newChildren } : n,
                    );
                  };
                  onUpdate(updateList(nodes));
                }}
                onSelect={onSelect}
                isUnlocked={isUnlocked}
              />
              {node.children?.length === 0 && (
                <div className="ml-6 py-1 text-[10px] text-industrial-300 dark:text-industrial-600 italic">
                  Empty Folder
                </div>
              )}
            </div>
          )}
        </div>
      ))}

      {level === 0 && (
        <button
          onClick={() => addNode("root", "folder")}
          className="mt-2 flex items-center gap-2 py-2 px-3 text-[11px] font-bold text-industrial-400 hover:text-indigo-600 hover:bg-industrial-50 dark:hover:bg-industrial-800 rounded-xl transition-all border-2 border-dashed border-industrial-100 dark:border-industrial-800 hover:border-indigo-100 dark:hover:border-indigo-900"
        >
          <Plus className="w-3 h-3" /> Add New Group
        </button>
      )}
    </div>
  );
};

export default FeedTree;
