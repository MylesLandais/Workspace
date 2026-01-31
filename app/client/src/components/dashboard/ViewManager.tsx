"use client";

import React from "react";
import { Save, Trash2, Calendar, ArrowRight } from "lucide-react";
import { SavedBoard, DashboardTab } from "@/lib/types/dashboard";

interface ViewManagerProps {
  boards: SavedBoard[];
  onSaveCurrent: () => void;
  onLoadBoard: (tabs: DashboardTab[]) => void;
  onDeleteBoard: (id: string) => void;
}

const ViewManager: React.FC<ViewManagerProps> = ({
  boards,
  onSaveCurrent,
  onLoadBoard,
  onDeleteBoard,
}) => {
  return (
    <div className="flex flex-col gap-2 p-2">
      <div className="flex flex-col gap-1.5">
        {boards.length === 0 ? (
          <div className="py-4 text-center border-2 border-dashed border-industrial-100 dark:border-industrial-800 rounded-xl">
            <p className="text-[10px] text-industrial-400 font-medium">
              No saved boards yet
            </p>
          </div>
        ) : (
          boards.map((board) => (
            <div
              key={board.id}
              className="group flex items-center justify-between p-2.5 bg-white dark:bg-industrial-900 border border-industrial-100 dark:border-industrial-800 rounded-xl hover:border-indigo-200 dark:hover:border-indigo-800 hover:shadow-sm transition-all"
            >
              <div
                className="flex flex-col min-w-0 flex-1 cursor-pointer"
                onClick={() => onLoadBoard(board.tabs)}
              >
                <span className="text-[12px] font-bold text-industrial-700 dark:text-industrial-300 truncate group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                  {board.name}
                </span>
                <div className="flex items-center gap-1.5 text-[9px] text-industrial-400 mt-0.5">
                  <Calendar className="w-2.5 h-2.5" />
                  <span>{new Date(board.timestamp).toLocaleDateString()}</span>
                  <span className="mx-0.5">•</span>
                  <span>{board.tabs.length} Tabs</span>
                </div>
              </div>

              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => onLoadBoard(board.tabs)}
                  className="p-1.5 text-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-950 rounded-lg transition-colors"
                  title="Load Board"
                >
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => onDeleteBoard(board.id)}
                  className="p-1.5 text-industrial-300 dark:text-industrial-600 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-950 rounded-lg transition-colors"
                  title="Delete"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <button
        onClick={onSaveCurrent}
        className="mt-2 flex items-center justify-center gap-2 py-2 px-3 text-[10px] font-bold text-industrial-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950 rounded-xl transition-all border-2 border-dashed border-industrial-100 dark:border-industrial-800 hover:border-indigo-100 dark:hover:border-indigo-900"
      >
        <Save className="w-3 h-3" /> Snapshot Current View
      </button>
    </div>
  );
};

export default ViewManager;
