import React, { useState, useMemo } from 'react';
import { Sidebar } from './components/Sidebar';
import { ArticleList } from './components/ArticleList';
import { ArticleReader } from './components/ArticleReader';
import { InsightsView } from './components/InsightsView';
import { MOCK_FEEDS, MOCK_ARTICLES, MOCK_BOARDS } from './data/mockData';
import { Article, ViewMode, LayoutMode, Board } from './types';
import { Menu } from 'lucide-react';

const App: React.FC = () => {
  const [activeView, setActiveView] = useState<ViewMode>('inbox');
  const [activeFeedId, setActiveFeedId] = useState<string | null>(null);
  const [activeArticleId, setActiveArticleId] = useState<string | null>(null);
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [activeBoardId, setActiveBoardId] = useState<string | null>(null);
  
  const [articles, setArticles] = useState<Article[]>(MOCK_ARTICLES);
  const [boards, setBoards] = useState<Board[]>(MOCK_BOARDS);
  const [layout, setLayout] = useState<LayoutMode>('list');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false); // For mobile

  // Computed Tags
  const tags = useMemo(() => {
    const counts: Record<string, number> = {};
    articles.forEach(a => {
      a.tags.forEach(t => {
        counts[t] = (counts[t] || 0) + 1;
      });
    });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => ({ name, count }));
  }, [articles]);

  // Filter logic
  const filteredArticles = useMemo(() => {
    let filtered = articles;

    if (activeView === 'inbox') {
      filtered = filtered.filter(a => !a.archived);
    } else if (activeView === 'later') {
      filtered = filtered.filter(a => a.saved && !a.archived);
    } else if (activeView === 'archive') {
      filtered = filtered.filter(a => a.archived);
    } else if (activeView === 'feed' && activeFeedId) {
      filtered = filtered.filter(a => a.sourceId === activeFeedId && !a.archived);
    } else if (activeView === 'tag' && activeTag) {
      filtered = filtered.filter(a => a.tags.includes(activeTag) && !a.archived);
    } else if (activeView === 'board' && activeBoardId) {
       const board = boards.find(b => b.id === activeBoardId);
       if (board) {
         filtered = filtered.filter(a => board.articleIds.includes(a.id));
       } else {
         filtered = [];
       }
    }

    // Sort by date desc
    return filtered.sort((a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime());
  }, [articles, activeView, activeFeedId, activeTag, activeBoardId, boards]);

  const activeArticle = useMemo(() => 
    articles.find(a => a.id === activeArticleId) || null
  , [articles, activeArticleId]);

  // Handlers
  const handleToggleSave = (id: string) => {
    setArticles(prev => prev.map(a => a.id === id ? { ...a, saved: !a.saved } : a));
  };

  const handleArchive = (id: string) => {
    setArticles(prev => prev.map(a => a.id === id ? { ...a, archived: !a.archived } : a));
    if (activeArticleId === id) setActiveArticleId(null);
  };

  const handleUpdateArticle = (id: string, updates: Partial<Article>) => {
    setArticles(prev => prev.map(a => a.id === id ? { ...a, ...updates } : a));
  };

  const handlePinToBoard = (articleId: string, boardId: string) => {
    setBoards(prev => prev.map(b => {
      if (b.id === boardId) {
        // Toggle pin
        const exists = b.articleIds.includes(articleId);
        return {
          ...b,
          articleIds: exists 
            ? b.articleIds.filter(id => id !== articleId)
            : [...b.articleIds, articleId]
        };
      }
      return b;
    }));
  };

  const handleSelectArticle = (article: Article) => {
    setActiveArticleId(article.id);
    // Mark as read
    if (!article.read) {
      setArticles(prev => prev.map(a => a.id === article.id ? { ...a, read: true } : a));
    }
  };

  const getPageTitle = () => {
    if (activeView === 'feed' && activeFeedId) {
      return MOCK_FEEDS.find(f => f.id === activeFeedId)?.name || 'Feed';
    }
    if (activeView === 'tag' && activeTag) {
      return `#${activeTag}`;
    }
    if (activeView === 'board' && activeBoardId) {
      return boards.find(b => b.id === activeBoardId)?.name || 'Board';
    }
    return activeView;
  };

  // Nav Handlers
  const resetSelection = () => {
     setActiveFeedId(null);
     setActiveTag(null);
     setActiveBoardId(null);
     setIsSidebarOpen(false);
     setActiveArticleId(null);
  };

  const handleFeedSelect = (id: string | null) => {
    resetSelection();
    setActiveFeedId(id);
    setActiveView('feed');
  };

  const handleTagSelect = (tag: string) => {
    resetSelection();
    setActiveTag(tag);
    setActiveView('tag');
  };

  const handleBoardSelect = (id: string) => {
    resetSelection();
    setActiveBoardId(id);
    setActiveView('board');
    setLayout('grid'); // Auto-switch to grid for boards
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden text-slate-900 font-sans">
      
      {/* Mobile Menu Button */}
      <div className="md:hidden absolute top-4 left-4 z-30">
        {!isSidebarOpen && !activeArticleId && (
          <button onClick={() => setIsSidebarOpen(true)} className="p-2 bg-white shadow-sm rounded-lg border border-slate-200">
             <Menu className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-40 w-64 transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0
        ${isSidebarOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'}
      `}>
        <Sidebar 
          feeds={MOCK_FEEDS} 
          boards={boards}
          activeView={activeView}
          activeFeedId={activeFeedId}
          activeTag={activeTag}
          activeBoardId={activeBoardId}
          tags={tags}
          onViewChange={(view) => {
            resetSelection();
            setActiveView(view);
          }}
          onFeedSelect={handleFeedSelect}
          onTagSelect={handleTagSelect}
          onBoardSelect={handleBoardSelect}
        />
        {isSidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/20 z-[-1] md:hidden"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}
      </div>

      {/* Main Content Area */}
      {activeView === 'analytics' ? (
        <div className="flex-1 overflow-hidden">
           <InsightsView articles={articles} />
        </div>
      ) : (
        <>
          {/* List/Grid Pane */}
          <div className={`
            flex-shrink-0 bg-white md:border-r border-slate-200 h-full transition-all duration-300
            ${activeArticleId ? 'hidden md:flex md:w-80 lg:w-96' : 'flex w-full'}
          `}>
            <ArticleList 
              articles={filteredArticles} 
              activeArticleId={activeArticleId}
              onSelectArticle={handleSelectArticle}
              viewTitle={getPageTitle()}
              layout={layout}
              onToggleLayout={() => setLayout(l => l === 'list' ? 'grid' : 'list')}
            />
          </div>

          {/* Reader Pane */}
          <div className={`
            flex-1 h-full bg-white relative
            ${!activeArticleId ? 'hidden md:flex' : 'flex fixed inset-0 z-50 md:static'}
          `}>
            <ArticleReader 
              article={activeArticle} 
              boards={boards}
              onBack={() => setActiveArticleId(null)}
              onToggleSave={handleToggleSave}
              onArchive={handleArchive}
              onPinToBoard={handlePinToBoard}
              onUpdateArticle={handleUpdateArticle}
            />
          </div>
        </>
      )}
    </div>
  );
};

export default App;