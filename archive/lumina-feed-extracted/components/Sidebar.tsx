import React from 'react';
import { FilterState, SavedBoard, Theme, AppView } from '../types';
import { User, Globe, Hash, Plus, LayoutGrid, Radio, CheckCircle2, Bookmark, Trash2, ArrowRight, Moon, Sparkles, Settings, Eye, EyeOff } from 'lucide-react';

interface SidebarProps {
  filters: FilterState;
  setFilters: React.Dispatch<React.SetStateAction<FilterState>>;
  isMobileOpen: boolean;
  savedBoards: SavedBoard[];
  onSelectBoard: (board: SavedBoard) => void;
  onDeleteBoard: (id: string) => void;
  theme: Theme;
  setTheme: (theme: Theme) => void;
  onViewChange: (view: AppView) => void;
  currentView: AppView;
}

const PERSON_PRESETS = [
  'Taylor Swift', 'Selena Gomez', 'Zendaya', 'Timothée Chalamet', 'Dua Lipa'
];

const SOURCE_PRESETS = [
  'Instagram', 'Reddit', 'TikTok', 'Twitter/X', 'Pinterest'
];

export const Sidebar: React.FC<SidebarProps> = ({ 
  filters, 
  setFilters, 
  isMobileOpen,
  savedBoards,
  onSelectBoard,
  onDeleteBoard,
  theme,
  setTheme,
  onViewChange,
  currentView
}) => {
  
  const togglePerson = (person: string) => {
    onViewChange('feed'); // Ensure we are on feed view when filtering
    setFilters(prev => {
      const exists = prev.persons.includes(person);
      return {
        ...prev,
        persons: exists ? prev.persons.filter(p => p !== person) : [...prev.persons, person]
      };
    });
  };

  const toggleSource = (source: string) => {
    onViewChange('feed');
    setFilters(prev => {
      const exists = prev.sources.includes(source);
      return {
        ...prev,
        sources: exists ? prev.sources.filter(s => s !== source) : [...prev.sources, source]
      };
    });
  };

  return (
    <aside className={`
      fixed inset-y-0 left-0 z-40 w-64 bg-app-bg border-r border-app-border transform transition-transform duration-300 ease-in-out
      ${isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
    `}>
      <div className="h-full overflow-y-auto no-scrollbar p-6 flex flex-col">
        
        {/* Logo Area */}
        <div 
          className="flex items-center gap-3 mb-10 cursor-pointer"
          onClick={() => onViewChange('feed')}
        >
          <div className="w-8 h-8 bg-app-text rounded flex items-center justify-center shadow-lg">
            <LayoutGrid className="w-5 h-5 text-app-bg" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-app-text">Lumina</h1>
        </div>

        {/* Navigation Groups */}
        <div className="space-y-8 flex-1">
          
          {/* Admin Link */}
          <div>
            <div className="flex items-center justify-between mb-2 text-xs font-semibold text-app-muted uppercase tracking-wider">
              <span>Admin</span>
            </div>
             <button
                onClick={() => onViewChange('admin')}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-200
                  ${currentView === 'admin' 
                    ? 'bg-app-accent text-white shadow-md' 
                    : 'text-app-muted hover:text-app-text hover:bg-app-surface-hover'
                  }
                `}
              >
                <Settings className="w-4 h-4" />
                <span>Manage Entities</span>
              </button>
          </div>

          {/* Saved Boards Section */}
          {savedBoards.length > 0 && (
            <div className="animate-in slide-in-from-left-2 duration-300">
              <div className="flex items-center justify-between mb-4 text-xs font-semibold text-app-accent uppercase tracking-wider">
                <span>My Boards</span>
                <Bookmark className="w-3 h-3" />
              </div>
              <ul className="space-y-1">
                {savedBoards.map(board => (
                  <li key={board.id} className="group relative">
                    <button
                      onClick={() => { onSelectBoard(board); onViewChange('feed'); }}
                      className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-app-muted hover:text-app-text hover:bg-app-surface transition-all"
                    >
                      <span className="truncate">{board.name}</span>
                      <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                    <button 
                      onClick={(e) => { e.stopPropagation(); onDeleteBoard(board.id); }}
                      className="absolute right-1 top-1/2 -translate-y-1/2 p-1.5 text-app-muted hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Tracking Section */}
          <div>
            <div className="flex items-center justify-between mb-4 text-xs font-semibold text-app-muted uppercase tracking-wider">
              <span>Following Persons</span>
              <Plus className="w-3 h-3 cursor-pointer hover:text-app-text" />
            </div>
            <ul className="space-y-1">
              {PERSON_PRESETS.map(person => {
                const isActive = filters.persons.includes(person) && currentView === 'feed';
                return (
                  <li key={person}>
                    <button
                      onClick={() => togglePerson(person)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all duration-200 group
                        ${isActive 
                          ? 'bg-app-surface text-app-text shadow-sm border border-app-border' 
                          : 'text-app-muted/60 hover:text-app-muted hover:bg-app-surface-hover/50'
                        }
                      `}
                    >
                      <div className={`flex items-center gap-3 transition-all ${!isActive ? 'opacity-80' : ''}`}>
                        <User className="w-4 h-4" />
                        <span className={!isActive ? 'line-through decoration-app-muted/50 decoration-2' : ''}>{person}</span>
                      </div>
                      {isActive ? (
                        <Eye className="w-4 h-4 text-app-accent" />
                      ) : (
                        <EyeOff className="w-4 h-4 text-app-muted/40 group-hover:text-app-muted/70 transition-colors" />
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>

          {/* Sources Section */}
          <div>
            <div className="flex items-center justify-between mb-4 text-xs font-semibold text-app-muted uppercase tracking-wider">
              <span>Sources</span>
              <Globe className="w-3 h-3" />
            </div>
            <ul className="space-y-1">
              {SOURCE_PRESETS.map(source => {
                const isActive = filters.sources.includes(source) && currentView === 'feed';
                return (
                  <li key={source}>
                    <button
                      onClick={() => toggleSource(source)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all duration-200
                        ${isActive 
                          ? 'bg-app-surface text-app-text shadow-sm border border-app-border' 
                          : 'text-app-muted hover:text-app-text hover:bg-app-surface-hover'
                        }
                      `}
                    >
                      <div className="flex items-center gap-3">
                        <Hash className="w-4 h-4" />
                        <span>{source}</span>
                      </div>
                      {isActive && <Radio className="w-2 h-2 text-app-accent fill-current" />}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>

        </div>

        {/* Footer & Theme Switcher */}
        <div className="pt-6 border-t border-app-border space-y-4">
          
          <div className="bg-app-surface rounded-lg p-1 flex">
            <button
              onClick={() => setTheme('default')}
              className={`flex-1 flex items-center justify-center gap-2 py-1.5 rounded-md text-xs font-medium transition-all
                ${theme === 'default' 
                  ? 'bg-app-border text-white shadow-sm' 
                  : 'text-app-muted hover:text-app-text'
                }
              `}
            >
              <Moon className="w-3 h-3" />
              <span>Midnight</span>
            </button>
            <button
              onClick={() => setTheme('kanagawa')}
              className={`flex-1 flex items-center justify-center gap-2 py-1.5 rounded-md text-xs font-medium transition-all
                ${theme === 'kanagawa' 
                  ? 'bg-[#98BB6C] text-[#181616] shadow-sm' 
                  : 'text-app-muted hover:text-app-text'
                }
              `}
            >
              <Sparkles className="w-3 h-3" />
              <span>Dragon</span>
            </button>
          </div>

          <div className="text-xs text-app-muted">
            <p>© 2024 Lumina Feed</p>
            <p className="mt-1 opacity-60">Powered by Gemini AI</p>
          </div>
        </div>

      </div>
    </aside>
  );
};