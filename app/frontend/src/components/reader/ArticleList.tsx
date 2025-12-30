import React from 'react';
import { Article, LayoutMode } from './types';
import { CheckCircle2, Bookmark, LayoutGrid, List } from 'lucide-react';

interface ArticleListProps {
  articles: Article[];
  activeArticleId: string | null;
  onSelectArticle: (article: Article) => void;
  viewTitle: string;
  layout: LayoutMode;
  onToggleLayout: () => void;
  className?: string;
}

export const ArticleList: React.FC<ArticleListProps> = ({ 
  articles, 
  activeArticleId, 
  onSelectArticle,
  viewTitle,
  layout,
  onToggleLayout,
  className = ""
}) => {
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 3600 * 24));
    
    if (days === 0) return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={`flex flex-col h-full bg-app-bg border-r border-app-border ${className}`}>
      {/* Header */}
      <div className="h-16 px-4 border-b border-app-border flex items-center justify-between flex-shrink-0">
        <h2 className="font-bold text-app-text text-lg capitalize truncate max-w-[150px]">{viewTitle}</h2>
        <div className="flex items-center gap-2">
           <span className="text-xs text-app-muted font-medium hidden sm:inline">{articles.length} items</span>
           <button 
             onClick={onToggleLayout}
             className="p-1.5 hover:bg-app-surface rounded text-app-muted transition-colors"
             title={layout === 'list' ? 'Switch to Grid' : 'Switch to List'}
           >
             {layout === 'list' ? <LayoutGrid className="w-4 h-4" /> : <List className="w-4 h-4" />}
           </button>
        </div>
      </div>

      {/* List / Grid Content */}
      <div className="flex-1 overflow-y-auto bg-app-surface/30">
        {articles.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-app-muted">
            <CheckCircle2 className="w-8 h-8 mb-2 opacity-50" />
            <p className="text-sm">No items here</p>
          </div>
        ) : (
          <div className={`
             ${layout === 'grid' ? 'p-4 columns-2 gap-4 space-y-4' : ''}
          `}>
            {articles.map(article => (
              <div
                key={article.id}
                onClick={() => onSelectArticle(article)}
                className={`
                  cursor-pointer transition-colors group
                  ${layout === 'grid' 
                    ? 'break-inside-avoid bg-app-surface rounded-xl overflow-hidden border border-app-border hover:shadow-md mb-4' 
                    : `p-4 border-b border-app-border hover:bg-app-surface ${activeArticleId === article.id ? 'bg-app-accent/20 border-app-accent/50' : ''} ${!article.read ? 'bg-app-bg' : 'bg-app-surface/30'}`
                  }
                `}
              >
                {/* Image Preview for Grid Mode */}
                {layout === 'grid' && article.imageUrl && (
                  <div className="relative w-full">
                     <img 
                       src={article.imageUrl} 
                       alt={article.title}
                       className="w-full h-auto object-cover display-block"
                       loading="lazy"
                     />
                  </div>
                )}

                {/* Content Container */}
                <div className={`${layout === 'grid' ? 'p-3' : ''}`}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      {!article.read && layout === 'list' && (
                        <div className="w-2 h-2 bg-app-accent rounded-full" />
                      )}
                      <span className="text-xs text-app-muted">{formatDate(article.publishedAt)}</span>
                    </div>
                    {article.saved && (
                      <Bookmark className="w-4 h-4 text-app-accent fill-current" />
                    )}
                  </div>
                  <h3 className={`font-medium ${layout === 'grid' ? 'text-sm line-clamp-2' : 'text-base'} mb-1`}>
                    {article.title}
                  </h3>
                  {layout === 'list' && (
                    <p className="text-xs text-app-muted line-clamp-2">{article.author}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};





