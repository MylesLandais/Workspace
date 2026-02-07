"use client";

/**
 * CollabCursors Component
 * Displays other users' cursors in real-time during collaboration
 */

import React from "react";
import { MousePointer2 } from "lucide-react";

interface CursorUser {
  id: string;
  name: string;
  color: string;
  cursor: { x: number; y: number } | null;
}

interface CollabCursorsProps {
  users: CursorUser[];
  containerRef?: React.RefObject<HTMLElement>;
}

const CollabCursors: React.FC<CollabCursorsProps> = ({ users }) => {
  return (
    <div className="pointer-events-none fixed inset-0 z-[1000] overflow-hidden">
      {users.map((user) => {
        if (!user.cursor) return null;

        return (
          <div
            key={user.id}
            className="absolute transition-all duration-75 ease-out"
            style={{
              left: user.cursor.x,
              top: user.cursor.y,
              transform: "translate(-2px, -2px)",
            }}
          >
            <div className="relative" style={{ color: user.color }}>
              <MousePointer2
                className="w-5 h-5 drop-shadow-lg"
                style={{
                  fill: user.color,
                  stroke: "white",
                  strokeWidth: 1.5,
                }}
              />

              <div
                className="absolute left-4 top-4 px-2 py-0.5 text-[10px] font-bold text-white whitespace-nowrap shadow-lg rounded-sm"
                style={{
                  backgroundColor: user.color,
                }}
              >
                {user.name}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default CollabCursors;
