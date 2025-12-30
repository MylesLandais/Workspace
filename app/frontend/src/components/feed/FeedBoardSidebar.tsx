import { useState, useEffect } from 'react';
import {
  getBoardConfig,
  saveBoardConfig,
  getAllBoards,
  type BoardConfig,
  type EntityFilter,
} from '../../lib/feed-config/board-config';

interface FeedBoardSidebarProps {
  onConfigChange: (config: BoardConfig) => void;
  availableSources: string[]; // List of all available sources/subreddits
  availableEntities: Array<{ id: string; name: string; sources: string[] }>; // Entities and their sources
}

export default function FeedBoardSidebar({
  onConfigChange,
  availableSources,
  availableEntities,
}: FeedBoardSidebarProps) {
  const [boards, setBoards] = useState<string[]>(getAllBoards());
  const [selectedBoard, setSelectedBoard] = useState<string>('default');
  const [config, setConfig] = useState<BoardConfig>(() => getBoardConfig(selectedBoard));
  const [showEntityFilters, setShowEntityFilters] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Load config when board changes
  useEffect(() => {
    const newConfig = getBoardConfig(selectedBoard);
    setConfig(newConfig);
    onConfigChange(newConfig);
  }, [selectedBoard, onConfigChange]);

  // Notify parent when config changes
  useEffect(() => {
    saveBoardConfig(config);
    onConfigChange(config);
  }, [config, onConfigChange]);

  const toggleSource = (sourceName: string) => {
    setConfig(prev => {
      const newSources = new Set(prev.enabledSources);
      if (newSources.has(sourceName)) {
        newSources.delete(sourceName);
      } else {
        newSources.add(sourceName);
      }
      return {
        ...prev,
        enabledSources: newSources,
        updatedAt: new Date().toISOString(),
      };
    });
  };

  const toggleEntityBlock = (entityName: string, sourceName: string) => {
    setConfig(prev => {
      const newBlocked = new Map(prev.blockedEntities);
      const entityKey = entityName.toLowerCase();
      const existing = newBlocked.get(entityKey) || {
        entityId: entityKey,
        entityName: entityName,
        blockedSources: new Set<string>(),
      };

      const newBlockedSources = new Set(existing.blockedSources);
      if (newBlockedSources.has(sourceName)) {
        newBlockedSources.delete(sourceName);
        if (newBlockedSources.size === 0) {
          newBlocked.delete(entityKey);
        } else {
          newBlocked.set(entityKey, { ...existing, blockedSources: newBlockedSources });
        }
      } else {
        newBlockedSources.add(sourceName);
        newBlocked.set(entityKey, { ...existing, blockedSources: newBlockedSources });
      }

      return {
        ...prev,
        blockedEntities: newBlocked,
        updatedAt: new Date().toISOString(),
      };
    });
  };

  const enableAllSources = () => {
    setConfig(prev => ({
      ...prev,
      enabledSources: new Set(availableSources),
      updatedAt: new Date().toISOString(),
    }));
  };

  const disableAllSources = () => {
    setConfig(prev => ({
      ...prev,
      enabledSources: new Set(),
      updatedAt: new Date().toISOString(),
    }));
  };

  const isSourceEnabled = (sourceName: string) => {
    return config.enabledSources.size === 0 || config.enabledSources.has(sourceName);
  };

  if (isCollapsed) {
    return (
      <div className="w-12 bg-gray-900 border-r border-gray-800 h-full flex flex-col items-center py-4">
        <button
          onClick={() => setIsCollapsed(false)}
          className="p-2 text-gray-400 hover:text-white transition-colors"
          title="Expand sidebar"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    );
  }

  return (
    <div className="w-80 bg-gray-900 border-r border-gray-800 h-full flex flex-col">
      <div className="flex-1 overflow-y-auto p-4">
        {/* Header with collapse button */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-white">Boards</h2>
          <button
            onClick={() => setIsCollapsed(true)}
            className="p-1.5 text-gray-400 hover:text-white transition-colors"
            title="Collapse sidebar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>

        {/* Board Selector */}
        <div className="mb-6">
          <select
            value={selectedBoard}
            onChange={e => setSelectedBoard(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {boards.map(boardId => (
              <option key={boardId} value={boardId}>
                {boardId === 'default' ? 'Default Feed' : boardId}
              </option>
            ))}
          </select>
          <button
            onClick={() => {
              const newBoard = `board-${Date.now()}`;
              const newConfig = getBoardConfig(newBoard);
              newConfig.name = `Board ${boards.length}`;
              saveBoardConfig(newConfig);
              setBoards([...boards, newBoard]);
              setSelectedBoard(newBoard);
            }}
            className="mt-2 w-full px-3 py-1.5 text-sm text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded transition-colors"
          >
            + New Board
          </button>
        </div>

        {/* Source Filters */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-300">Sources</h3>
            <div className="flex gap-2">
              <button
                onClick={enableAllSources}
                className="text-xs text-gray-400 hover:text-white"
                title="Enable all"
              >
                All
              </button>
              <button
                onClick={disableAllSources}
                className="text-xs text-gray-400 hover:text-white"
                title="Disable all"
              >
                None
              </button>
            </div>
          </div>
          <div className="space-y-2">
            {availableSources.map(source => {
              const enabled = isSourceEnabled(source);
              return (
                <div
                  key={source}
                  className={`flex items-center justify-between p-2 rounded transition-colors ${
                    enabled
                      ? 'hover:bg-gray-800'
                      : 'opacity-50 hover:opacity-70'
                  }`}
                >
                  <div className="flex items-center flex-1">
                    <button
                      onClick={() => toggleSource(source)}
                      className="mr-2 p-1 text-gray-400 hover:text-white transition-colors"
                      title={enabled ? 'Hide feed' : 'Show feed'}
                    >
                      {enabled ? (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                        </svg>
                      )}
                    </button>
                    <span className={`text-sm ${enabled ? 'text-gray-300' : 'text-gray-500'}`}>
                      r/{source}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Entity Filters */}
        <div className="border-t border-gray-800 pt-4">
          <button
            onClick={() => setShowEntityFilters(!showEntityFilters)}
            className="w-full flex items-center justify-between text-sm font-semibold text-gray-300 hover:text-white mb-3"
          >
            <span>Entity Filters</span>
            <svg
              className={`w-4 h-4 transition-transform ${showEntityFilters ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showEntityFilters && (
            <div className="space-y-4">
              {availableEntities.map(entity => (
                <div key={entity.id} className="bg-gray-800 rounded p-3">
                  <div className="font-medium text-sm text-white mb-2">{entity.name}</div>
                  <div className="space-y-1.5">
                    {entity.sources.map(source => {
                      const isBlocked =
                        config.blockedEntities
                          .get(entity.name.toLowerCase())
                          ?.blockedSources.has(source) || false;
                      return (
                        <label
                          key={source}
                          className="flex items-center justify-between cursor-pointer hover:bg-gray-700 px-2 py-1 rounded"
                        >
                          <div className="flex items-center flex-1">
                            <input
                              type="checkbox"
                              checked={!isBlocked}
                              onChange={() => toggleEntityBlock(entity.name, source)}
                              className="mr-2 w-3.5 h-3.5 rounded border-gray-600 bg-gray-700 text-red-600 focus:ring-red-500"
                            />
                            <span className="text-xs text-gray-400">r/{source}</span>
                          </div>
                          {isBlocked && (
                            <span className="text-xs text-red-400">Blocked</span>
                          )}
                        </label>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Management Console Link */}
      <div className="border-t border-gray-800 p-4">
        <a
          href="/feed-control"
          className="flex items-center justify-center w-full px-4 py-2 text-sm font-medium text-gray-300 bg-gray-800 hover:bg-gray-700 hover:text-white rounded transition-colors"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Manage Sources
        </a>
      </div>
    </div>
  );
}
