import React, { useState, useEffect } from 'react';
import { Article, AIResponse, Board } from './types';
import { 
  Sparkles, 
  Bookmark, 
  Archive, 
  Share, 
  MessageSquare, 
  MoreHorizontal, 
  ArrowLeft,
  X,
  Send,
  Headphones,
  FileText,
  Search,
  ExternalLink,
  Pin,
  Check
} from 'lucide-react';

interface ArticleReaderProps {
  article: Article | null;
  boards: Board[];
  onBack?: () => void;
  onToggleSave: (id: string) => void;
  onArchive: (id: string) => void;
  onPinToBoard: (articleId: string, boardId: string) => void;
  onUpdateArticle: (articleId: string, updates: Partial<Article>) => void;
}

export const ArticleReader: React.FC<ArticleReaderProps> = ({ 
  article, 
  boards,
  onBack,
  onToggleSave,
  onArchive,
  onPinToBoard,
  onUpdateArticle
}) => {
  const [activeTab, setActiveTab] = useState<'read' | 'chat'>('read');
  const [aiData, setAiData] = useState<AIResponse | null>(null);
  const [isLoadingAI, setIsLoadingAI] = useState(false);
  const [showBoardMenu, setShowBoardMenu] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<{role: 'user' | 'ai', text: string}[]>([]);

  // Reset state when article changes
  useEffect(() => {
    setAiData(null);
    setActiveTab('read');
    setChatHistory([]);
    setShowBoardMenu(false);
    if (article?.summary) {
       setAiData({ summary: article.summary });
    }
  }, [article?.id]);

  if (!article) {
    return (
      <div className="flex items-center justify-center h-full text-app-muted">
        <p>Select an article to read</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-app-bg text-app-text">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-app-border">
        <div className="flex items-center gap-3">
          {onBack && (
            <button onClick={onBack} className="p-2 hover:bg-app-surface rounded-lg transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <h1 className="text-lg font-semibold truncate max-w-md">{article.title}</h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onToggleSave(article.id)}
            className={`p-2 rounded-lg transition-colors ${
              article.saved ? 'bg-app-accent text-white' : 'hover:bg-app-surface text-app-muted'
            }`}
          >
            <Bookmark className="w-5 h-5" />
          </button>
          <button
            onClick={() => onArchive(article.id)}
            className="p-2 hover:bg-app-surface rounded-lg transition-colors text-app-muted"
          >
            <Archive className="w-5 h-5" />
          </button>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 hover:bg-app-surface rounded-lg transition-colors text-app-muted"
          >
            <ExternalLink className="w-5 h-5" />
          </a>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'read' ? (
          <div className="max-w-3xl mx-auto space-y-6">
            {article.imageUrl && (
              <img 
                src={article.imageUrl} 
                alt={article.title}
                className="w-full rounded-lg"
              />
            )}
            <div 
              className="prose prose-invert max-w-none"
              dangerouslySetInnerHTML={{ __html: article.content }}
            />
            {aiData?.summary && (
              <div className="bg-app-surface border border-app-border rounded-lg p-4">
                <h3 className="font-semibold mb-2 flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  AI Summary
                </h3>
                <p className="text-sm text-app-muted">{aiData.summary}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="max-w-2xl mx-auto space-y-4">
            <div className="space-y-3">
              {chatHistory.map((msg, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg ${
                    msg.role === 'user' ? 'bg-app-accent/20 ml-auto max-w-[80%]' : 'bg-app-surface'
                  }`}
                >
                  <p className="text-sm">{msg.text}</p>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    // Handle send
                  }
                }}
                placeholder="Ask about this article..."
                className="flex-1 bg-app-surface border border-app-border rounded-lg px-4 py-2 focus:outline-none focus:border-app-accent"
              />
              <button className="p-2 bg-app-accent text-white rounded-lg">
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="border-t border-app-border p-4 flex gap-2">
        <button
          onClick={() => setActiveTab('read')}
          className={`flex-1 py-2 rounded-lg transition-colors ${
            activeTab === 'read' ? 'bg-app-accent text-white' : 'bg-app-surface text-app-muted hover:bg-app-surface-hover'
          }`}
        >
          <FileText className="w-4 h-4 inline mr-2" />
          Read
        </button>
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex-1 py-2 rounded-lg transition-colors ${
            activeTab === 'chat' ? 'bg-app-accent text-white' : 'bg-app-surface text-app-muted hover:bg-app-surface-hover'
          }`}
        >
          <MessageSquare className="w-4 h-4 inline mr-2" />
          Chat
        </button>
      </div>
    </div>
  );
};





