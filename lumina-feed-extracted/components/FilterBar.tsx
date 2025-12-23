import React from 'react';
import { Search, X, SlidersHorizontal, Bell, BookmarkPlus } from 'lucide-react';
import { FilterState } from '../types';

interface FilterBarProps {
  filters: FilterState;
  setFilters: React.Dispatch<React.SetStateAction<FilterState>>;
  onMenuClick: () => void;
  onRefresh: () => void;
  onSaveBoard: () => void;
}

export const FilterBar: React.FC<FilterBarProps> = ({ filters, setFilters, onMenuClick, onRefresh, onSaveBoard }) => {
  
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onRefresh();
    }
  };

  const removeFilter = (type: 'person' | 'source', value: string) => {
    setFilters(prev => ({
      ...prev,
      persons: type === 'person' ? prev.persons.filter(p => p !== value) : prev.persons,
      sources: type === 'source' ? prev.sources.filter(s => s !== value) : prev.sources,
    }));
  };

  const hasActiveFilters = filters.persons.length > 0 || filters.sources.length > 0 || filters.searchQuery.length > 0;

  return (
    <div className="sticky top-0 z-30 bg-app-bg/80 backdrop-blur-xl border-b border-app-border transition-colors duration-300">
      <div className="px-6 py-4">
        <div className="flex flex-col gap-4">
          
          {/* Top Row: Mobile Menu + Search + Actions */}
          <div className="flex items-center gap-4">
            <button 
              onClick={onMenuClick}
              className="md:hidden p-2 text-app-muted hover:text-app-text"
            >
              <SlidersHorizontal className="w-5 h-5" />
            </button>

            <div className="flex-1 relative group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-app-muted group-focus-within:text-app-accent transition-colors" />
              <input 
                type="text"
                value={filters.searchQuery}
                onChange={(e) => setFilters(prev => ({ ...prev, searchQuery: e.target.value }))}
                onKeyDown={handleKeyDown}
                placeholder="Ask Lumina... (e.g., 'New minimalist architecture shots')"
                className="w-full bg-app-surface border border-app-border text-app-text text-sm rounded-full pl-10 pr-4 py-2.5 focus:outline-none focus:border-app-accent focus:ring-1 focus:ring-app-accent transition-all placeholder:text-app-muted/70"
              />
            </div>

            <div className="flex items-center gap-2 md:gap-3">
              {/* Save Board Button */}
              <button 
                onClick={onSaveBoard}
                disabled={!hasActiveFilters}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-full border transition-all
                  ${hasActiveFilters 
                    ? 'bg-app-surface border-app-border text-app-text hover:border-app-muted hover:bg-app-surface-hover cursor-pointer' 
                    : 'bg-transparent border-transparent text-app-muted/50 cursor-not-allowed'
                  }
                `}
                title="Save current filters as a Board"
              >
                <BookmarkPlus className="w-4 h-4" />
                <span className="hidden md:inline text-xs font-medium">Save View</span>
              </button>

              <div className="h-6 w-px bg-app-border hidden md:block" />

              <button className="p-2.5 rounded-full bg-app-surface text-app-muted hover:text-app-text hover:bg-app-surface-hover transition-colors relative">
                <Bell className="w-4 h-4" />
                <span className="absolute top-2 right-2.5 w-1.5 h-1.5 bg-pink-500 rounded-full animate-pulse"></span>
              </button>
              
              <div className="w-8 h-8 rounded-full bg-app-accent flex items-center justify-center text-xs font-bold border border-app-accent-hover text-white cursor-pointer hover:ring-2 hover:ring-app-accent/50 transition-all">
                YO
              </div>
            </div>
          </div>

          {/* Bottom Row: Active Filter Chips */}
          {(filters.persons.length > 0 || filters.sources.length > 0) && (
            <div className="flex flex-wrap gap-2 animate-in fade-in slide-in-from-top-2 duration-300">
              {filters.persons.map(person => (
                <div key={person} className="flex items-center gap-1 pl-3 pr-2 py-1 bg-app-accent-light border border-app-accent/30 text-app-accent text-xs rounded-full">
                  <span>{person}</span>
                  <button onClick={() => removeFilter('person', person)} className="p-0.5 hover:bg-app-accent/20 rounded-full">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
              {filters.sources.map(source => (
                <div key={source} className="flex items-center gap-1 pl-3 pr-2 py-1 bg-purple-500/10 border border-purple-500/30 text-purple-400 text-xs rounded-full">
                  <span>{source}</span>
                  <button onClick={() => removeFilter('source', source)} className="p-0.5 hover:bg-purple-500/20 rounded-full">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

        </div>
      </div>
    </div>
  );
};