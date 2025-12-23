import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { FilterBar } from './components/FilterBar';
import { FeedItem } from './components/FeedItem';
import { EntityManager } from './components/EntityManager';
import { FilterState, INITIAL_FILTERS, FeedItem as FeedItemType, SavedBoard, Theme, AppView } from './types';
import { generateFeedItems } from './services/geminiService';
import { Loader2, RefreshCw } from 'lucide-react';
import { DEMO_BOARDS } from './services/fixtures';

export default function App() {
  const [filters, setFilters] = useState<FilterState>(INITIAL_FILTERS);
  const [feedItems, setFeedItems] = useState<FeedItemType[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [initialLoadDone, setInitialLoadDone] = useState(false);
  const [currentView, setCurrentView] = useState<AppView>('feed');
  
  // Theme State
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      return (localStorage.getItem('lumina_theme') as Theme) || 'default';
    } catch {
      return 'default';
    }
  });

  useEffect(() => {
    localStorage.setItem('lumina_theme', theme);
    const root = document.getElementById('root');
    if (root) {
      root.className = theme === 'kanagawa' ? 'theme-kanagawa' : '';
    }
    document.body.className = theme === 'kanagawa' ? 'theme-kanagawa' : '';
  }, [theme]);

  // Load saved boards
  const [savedBoards, setSavedBoards] = useState<SavedBoard[]>(() => {
    try {
      const saved = localStorage.getItem('lumina_saved_boards');
      if (saved) return JSON.parse(saved);
      
      // Use Seed Data from Fixtures if storage is empty
      return DEMO_BOARDS;
    } catch (e) {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem('lumina_saved_boards', JSON.stringify(savedBoards));
  }, [savedBoards]);

  const handleSaveBoard = () => {
    const defaultName = filters.persons.length > 0 ? filters.persons.join(' & ') : 'My Custom Feed';
    const name = window.prompt("Name this board:", defaultName);
    if (!name) return;
    
    const newBoard: SavedBoard = {
      id: Date.now().toString(),
      name,
      filters: { ...filters },
      createdAt: Date.now()
    };
    
    setSavedBoards(prev => [newBoard, ...prev]);
  };

  const handleDeleteBoard = (id: string) => {
    if (window.confirm("Are you sure you want to delete this board?")) {
      setSavedBoards(prev => prev.filter(b => b.id !== id));
    }
  };

  const handleSelectBoard = (board: SavedBoard) => {
    setFilters(board.filters);
    setIsMobileMenuOpen(false);
    setCurrentView('feed');
  };

  // Core logic to fetch feed items
  const refreshFeed = useCallback(async () => {
    if (currentView !== 'feed') return;

    setLoading(true);
    const minTimePromise = new Promise(resolve => setTimeout(resolve, 800));
    
    const [items] = await Promise.all([
      generateFeedItems(filters.searchQuery, filters.persons, filters.sources),
      minTimePromise
    ]);

    setFeedItems(prev => initialLoadDone ? [...items, ...prev].slice(0, 50) : items); 
    
    if (!initialLoadDone) {
        setFeedItems(items);
        setInitialLoadDone(true);
    } else {
        setFeedItems(items);
    }
    
    setLoading(false);
  }, [filters, initialLoadDone, currentView]);

  useEffect(() => {
    if (initialLoadDone && currentView === 'feed') {
        refreshFeed();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.persons, filters.sources]);

  useEffect(() => {
    // Only refresh on mount if we are in feed view (which is default)
    if (currentView === 'feed') refreshFeed();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className={`min-h-screen bg-app-bg text-app-text font-sans selection:bg-app-accent/30 selection:text-white transition-colors duration-300`}>
      
      <Sidebar 
        filters={filters} 
        setFilters={setFilters} 
        isMobileOpen={isMobileMenuOpen}
        savedBoards={savedBoards}
        onSelectBoard={handleSelectBoard}
        onDeleteBoard={handleDeleteBoard}
        theme={theme}
        setTheme={setTheme}
        onViewChange={setCurrentView}
        currentView={currentView}
      />
      
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 md:hidden backdrop-blur-sm"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      <main className="md:ml-64 min-h-screen flex flex-col transition-all duration-300">
        
        {currentView === 'feed' ? (
          <>
            <FilterBar 
              filters={filters} 
              setFilters={setFilters} 
              onMenuClick={() => setIsMobileMenuOpen(true)}
              onRefresh={refreshFeed}
              onSaveBoard={handleSaveBoard}
            />

            <div className="flex-1 p-6 relative">
              
              {loading && feedItems.length === 0 ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-app-muted gap-4">
                  <Loader2 className="w-10 h-10 animate-spin text-app-accent" />
                  <p className="text-sm font-medium animate-pulse">Curating your feed...</p>
                </div>
              ) : (
                <>
                  {feedItems.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 text-app-muted gap-4">
                      <div className="w-16 h-16 rounded-full bg-app-surface flex items-center justify-center mb-2">
                        <RefreshCw className="w-6 h-6" />
                      </div>
                      <p>No posts found. Try adjusting your filters.</p>
                      <button 
                        onClick={refreshFeed}
                        className="px-4 py-2 bg-app-accent hover:bg-app-accent-hover text-white rounded-full text-sm font-medium transition-colors"
                      >
                        Refresh Feed
                      </button>
                    </div>
                  ) : (
                    <div className="columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-6 space-y-6 mx-auto max-w-7xl">
                      {feedItems.map((item) => (
                        <FeedItem key={item.id} item={item} />
                      ))}
                    </div>
                  )}
                </>
              )}

              {loading && feedItems.length > 0 && (
                <div className="fixed bottom-8 right-8 z-50 bg-app-accent text-white px-4 py-3 rounded-full shadow-lg flex items-center gap-3 animate-bounce-in">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm font-semibold">Updating...</span>
                </div>
              )}
            </div>
          </>
        ) : (
          /* Admin View */
          <EntityManager onBack={() => setCurrentView('feed')} />
        )}

      </main>
    </div>
  );
}