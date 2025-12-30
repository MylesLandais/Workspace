import React, { useState } from 'react';
import { ArticleList } from './ArticleList';
import { ArticleReader } from './ArticleReader';
import { InsightsView } from './InsightsView';
import { Article, ViewMode, LayoutMode } from './types';

export default function ReaderView() {
  const [articles] = useState<Article[]>([]); // TODO: Load from GraphQL
  const [activeArticleId, setActiveArticleId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('inbox');
  const [layout, setLayout] = useState<LayoutMode>('list');

  const activeArticle = articles.find(a => a.id === activeArticleId) || null;

  const handleSelectArticle = (article: Article) => {
    setActiveArticleId(article.id);
  };

  const handleToggleSave = (id: string) => {
    // TODO: Implement GraphQL mutation
    console.log('Toggle save:', id);
  };

  const handleArchive = (id: string) => {
    // TODO: Implement GraphQL mutation
    console.log('Archive:', id);
  };

  const handlePinToBoard = (articleId: string, boardId: string) => {
    // TODO: Implement GraphQL mutation
    console.log('Pin to board:', articleId, boardId);
  };

  const handleUpdateArticle = (articleId: string, updates: Partial<Article>) => {
    // TODO: Implement GraphQL mutation
    console.log('Update article:', articleId, updates);
  };

  if (viewMode === 'analytics') {
    return <InsightsView articles={articles} />;
  }

  return (
    <div className="flex h-screen bg-app-bg">
      <div className="w-80 flex-shrink-0">
        <ArticleList
          articles={articles}
          activeArticleId={activeArticleId}
          onSelectArticle={handleSelectArticle}
          viewTitle={viewMode}
          layout={layout}
          onToggleLayout={() => setLayout(layout === 'list' ? 'grid' : 'list')}
        />
      </div>
      <div className="flex-1">
        <ArticleReader
          article={activeArticle}
          boards={[]}
          onToggleSave={handleToggleSave}
          onArchive={handleArchive}
          onPinToBoard={handlePinToBoard}
          onUpdateArticle={handleUpdateArticle}
        />
      </div>
    </div>
  );
}





