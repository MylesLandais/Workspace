import { useState, useEffect } from 'react';

interface SourceFilter {
  id: string;
  name: string;
  subreddits: string[];
  enabled: boolean;
}

interface FeedSidebarProps {
  onFilterChange: (enabledSubreddits: Set<string>) => void;
}

// Define source groups (entities) - groups subreddits together
const SOURCE_GROUPS: SourceFilter[] = [
  {
    id: 'brooke-monk',
    name: 'Brooke Monk',
    subreddits: ['BrookeMonkTheSecond', 'BestOfBrookeMonk'],
    enabled: true,
  },
  {
    id: 'triangl',
    name: 'Triangl',
    subreddits: ['Triangl'],
    enabled: true,
  },
  {
    id: 'ovilee',
    name: 'Ovilee',
    subreddits: ['OvileeWorship'],
    enabled: true,
  },
  {
    id: 'sjokz',
    name: 'Sjokz',
    subreddits: ['Sjokz'],
    enabled: true,
  },
];

const STORAGE_KEY = 'feed-source-filters';

export default function FeedSidebar({ onFilterChange }: FeedSidebarProps) {
  // Load saved filter state from localStorage
  const [filters, setFilters] = useState<SourceFilter[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const savedFilters = JSON.parse(saved);
        // Merge with defaults, ensuring all sources are present
        return SOURCE_GROUPS.map(group => {
          const savedGroup = savedFilters.find((f: SourceFilter) => f.id === group.id);
          return savedGroup ? { ...group, enabled: savedGroup.enabled } : group;
        });
      }
    } catch (e) {
      console.warn('Failed to load saved filters:', e);
    }
    return SOURCE_GROUPS;
  });

  // Notify parent of filter changes (including initial state)
  useEffect(() => {
    const enabledSubreddits = new Set<string>();
    filters.forEach(filter => {
      if (filter.enabled) {
        filter.subreddits.forEach(subreddit => enabledSubreddits.add(subreddit));
      }
    });
    onFilterChange(enabledSubreddits);
    
    // Save to localStorage
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filters));
    } catch (e) {
      console.warn('Failed to save filters:', e);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]); // onFilterChange is stable, but we omit it to be safe

  const handleToggle = (id: string) => {
    setFilters(prevFilters =>
      prevFilters.map(filter =>
        filter.id === id ? { ...filter, enabled: !filter.enabled } : filter
      )
    );
  };

  return (
    <div className="w-64 bg-theme-bg-secondary border-r border-theme-border-primary p-4 h-full overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-theme-text-primary mb-2">Source Filters</h2>
        <p className="text-xs text-theme-text-secondary">Toggle sources to show/hide in feed</p>
      </div>

      <div className="space-y-3">
        {filters.map(filter => (
          <div key={filter.id} className="flex items-center justify-between">
            <div className="flex-1">
              <label
                htmlFor={`filter-${filter.id}`}
                className="text-sm font-medium text-theme-text-primary cursor-pointer flex items-center"
              >
                <input
                  id={`filter-${filter.id}`}
                  type="checkbox"
                  checked={filter.enabled}
                  onChange={() => handleToggle(filter.id)}
                  className="mr-3 w-4 h-4 rounded border-theme-border-primary bg-theme-bg-primary text-theme-accent-primary focus:ring-theme-accent-primary focus:ring-2"
                />
                <span>{filter.name}</span>
              </label>
              {filter.subreddits.length > 1 && (
                <div className="ml-7 mt-1">
                  <div className="text-xs text-theme-text-secondary">
                    {filter.subreddits.map(sub => `r/${sub}`).join(', ')}
                  </div>
                </div>
              )}
            </div>
            <div
              className={`ml-2 w-2 h-2 rounded-full ${
                filter.enabled ? 'bg-theme-accent-primary' : 'bg-theme-text-secondary'
              }`}
              title={filter.enabled ? 'Enabled' : 'Disabled'}
            />
          </div>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t border-theme-border-primary">
        <button
          onClick={() => setFilters(prev => prev.map(f => ({ ...f, enabled: true })))}
          className="w-full px-3 py-2 text-sm text-theme-text-secondary hover:text-theme-text-primary bg-theme-bg-primary hover:bg-theme-bg-primary/80 rounded transition-colors"
        >
          Enable All
        </button>
        <button
          onClick={() => setFilters(prev => prev.map(f => ({ ...f, enabled: false })))}
          className="w-full mt-2 px-3 py-2 text-sm text-theme-text-secondary hover:text-theme-text-primary bg-theme-bg-primary hover:bg-theme-bg-primary/80 rounded transition-colors"
        >
          Disable All
        </button>
      </div>
    </div>
  );
}

