import React from 'react';
import { Article, LayoutMode } from '../types';
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
    <div className={`flex flex-col h-full bg-white border-r border-slate-200 ${className}`}>
      {/* Header */}
      <div className="h-16 px-4 border-b border-slate-100 flex items-center justify-between flex-shrink-0">
        <h2 className="font-bold text-slate-800 text-lg capitalize truncate max-w-[150px]">{viewTitle}</h2>
        <div className="flex items-center gap-2">
           <span className="text-xs text-slate-400 font-medium hidden sm:inline">{articles.length} items</span>
           <button 
             onClick={onToggleLayout}
             className="p-1.5 hover:bg-slate-100 rounded text-slate-500 transition-colors"
             title={layout === 'list' ? 'Switch to Grid' : 'Switch to List'}
           >
             {layout === 'list' ? <LayoutGrid className="w-4 h-4" /> : <List className="w-4 h-4" />}
           </button>
        </div>
      </div>

      {/* List / Grid Content */}
      <div className="flex-1 overflow-y-auto bg-slate-50/50">
        {articles.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-400">
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
                    ? 'break-inside-avoid bg-white rounded-xl overflow-hidden border border-slate-200 hover:shadow-md mb-4' 
                    : `p-4 border-b border-slate-50 hover:bg-slate-50 ${activeArticleId === article.id ? 'bg-indigo-50/50 border-indigo-100' : ''} ${!article.read ? 'bg-white' : 'bg-slate-50/30'}`
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
                     {/* Overlay Stats */}
                     <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3 pt-6 text-white opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="flex items-center gap-2 text-[10px] font-medium">
                          {article.imageWidth && article.imageHeight && (
                            <span className="bg-black/40 px-1.5 py-0.5 rounded">{article.imageWidth}x{article.imageHeight}</span>
                          )}
                        </div>
                     </div>
                  </div>
                )}

                {/* Content Container */}
                <div className={`${layout === 'grid' ? 'p-3' : ''}`}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      {!article.read && layout === 'list' && (
                        <span className="w-2 h-2 rounded-full bg-indigo-500 flex-shrink-0" />
                      )}
                      <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide truncate max-w-[150px]">
                        {article.author}
                      </span>
                    </div>
                    {layout === 'list' && (
                      <span className="text-xs text-slate-400 flex-shrink-0">
                        {formatDate(article.publishedAt)}
                      </span>
                    )}
                  </div>
                  
                  <h3 className={`text-sm font-semibold mb-1.5 leading-snug ${
                    article.read ? 'text-slate-600' : 'text-slate-900'
                  }`}>
                    {article.title}
                  </h3>
                  
                  {layout === 'list' && (
                    <p className="text-xs text-slate-500 line-clamp-2 mb-2">
                      {article.content.replace(/<[^>]*>?/gm, '')}
                    </p>
                  )}

                  <div className="flex items-center gap-2 flex-wrap">
                    {article.type === 'twitter' && (
                      <span className="px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 text-[10px] font-medium border border-blue-100">Thread</span>
                    )}
                    {article.type === 'booru' && (
                      <span className="px-1.5 py-0.5 rounded bg-pink-50 text-pink-600 text-[10px] font-medium border border-pink-100">Booru</span>
                    )}
                    {article.saved && (
                      <Bookmark className="w-3 h-3 text-orange-400 fill-orange-400" />
                    )}
                    {/* Show limited tags in grid to save space */}
                    {article.tags.slice(0, layout === 'grid' ? 2 : 4).map(tag => (
                      <span key={tag} className="text-[10px] text-slate-400 bg-slate-100 px-1.5 rounded truncate max-w-[100px]">#{tag}</span>
                    ))}
                    {layout === 'grid' && article.tags.length > 2 && (
                       <span className="text-[10px] text-slate-300">+{article.tags.length - 2}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};