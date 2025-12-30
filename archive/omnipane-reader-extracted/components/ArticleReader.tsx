import React, { useState, useEffect } from 'react';
import { Article, AIResponse, SauceResult, Board } from '../types';
import { generateArticleSummary, chatWithArticle } from '../services/geminiService';
import { findSauce } from '../services/sauceNaoService';
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
  const [isSearchingSauce, setIsSearchingSauce] = useState(false);
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

  const handleGenerateSummary = async () => {
    if (!article) return;
    setIsLoadingAI(true);
    try {
      const data = await generateArticleSummary(article.content, article.title);
      setAiData(prev => ({ ...prev, ...data }));
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingAI(false);
    }
  };

  const handleFindSauce = async () => {
    if (!article || !article.imageUrl) return;
    setIsSearchingSauce(true);
    try {
      const sauce = await findSauce(article.imageUrl);
      if (sauce) {
        onUpdateArticle(article.id, { sauce });
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSearchingSauce(false);
    }
  };

  const handleSendMessage = async () => {
    if (!article || !chatInput.trim()) return;
    const userMsg = chatInput;
    setChatHistory(prev => [...prev, { role: 'user', text: userMsg }]);
    setChatInput("");
    
    // Optimistic UI updates could go here
    const response = await chatWithArticle(article.content, userMsg);
    setChatHistory(prev => [...prev, { role: 'ai', text: response || "Error" }]);
  };

  if (!article) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-white text-slate-400 h-full">
        <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
          <FileText className="w-8 h-8 text-slate-300" />
        </div>
        <p>Select an article to start reading</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-white relative">
      {/* Mobile Back Button Overlay */}
      <div className="md:hidden absolute top-4 left-4 z-20">
        <button 
          onClick={onBack}
          className="p-2 bg-white/90 backdrop-blur shadow-sm rounded-full border border-slate-200"
        >
          <ArrowLeft className="w-5 h-5 text-slate-700" />
        </button>
      </div>

      {/* Toolbar */}
      <div className="h-16 px-6 border-b border-slate-100 flex items-center justify-between flex-shrink-0 bg-white/80 backdrop-blur sticky top-0 z-10">
        <div className="flex items-center gap-1 md:pl-0 pl-12 overflow-x-auto no-scrollbar">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider bg-slate-100 px-2 py-1 rounded whitespace-nowrap">
            {article.type}
          </span>
          {article.tags.slice(0, 3).map(tag => (
            <span key={tag} className="text-xs text-slate-400 px-2 whitespace-nowrap">#{tag}</span>
          ))}
          {article.tags.length > 3 && <span className="text-xs text-slate-300 px-1">+{article.tags.length - 3}</span>}
        </div>
        
        <div className="flex items-center gap-2">
           <button 
             onClick={() => setActiveTab(activeTab === 'read' ? 'chat' : 'read')}
             className={`p-2 rounded-full transition-colors ${activeTab === 'chat' ? 'bg-indigo-100 text-indigo-700' : 'hover:bg-slate-100 text-slate-600'}`}
             title="Ask AI"
           >
             <MessageSquare className="w-5 h-5" />
           </button>
           <button className="p-2 hover:bg-slate-100 rounded-full text-slate-600 hidden sm:block" title="Listen (TTS)">
             <Headphones className="w-5 h-5" />
           </button>
           <div className="w-px h-4 bg-slate-200 mx-1" />
           
           {/* Pin Board Menu */}
           <div className="relative">
             <button 
               onClick={() => setShowBoardMenu(!showBoardMenu)}
               className="p-2 hover:bg-slate-100 rounded-full text-slate-600"
               title="Pin to Board"
             >
               <Pin className="w-5 h-5" />
             </button>
             {showBoardMenu && (
               <div className="absolute top-full right-0 mt-2 w-48 bg-white rounded-lg shadow-xl border border-slate-100 py-1 z-30">
                 <div className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">Save to Board</div>
                 {boards.map(board => {
                   const isPinned = board.articleIds.includes(article.id);
                   return (
                     <button
                       key={board.id}
                       onClick={() => {
                         onPinToBoard(article.id, board.id);
                         setShowBoardMenu(false);
                       }}
                       className="w-full text-left px-4 py-2 text-sm hover:bg-slate-50 flex items-center justify-between"
                     >
                       <span>{board.name}</span>
                       {isPinned && <Check className="w-3 h-3 text-indigo-500" />}
                     </button>
                   );
                 })}
                 {boards.length === 0 && <div className="px-4 py-2 text-sm text-slate-400 italic">No boards yet</div>}
               </div>
             )}
           </div>

           <button 
             onClick={() => onToggleSave(article.id)}
             className={`p-2 rounded-full transition-colors ${article.saved ? 'text-orange-500 bg-orange-50' : 'hover:bg-slate-100 text-slate-600'}`}
           >
             <Bookmark className={`w-5 h-5 ${article.saved ? 'fill-current' : ''}`} />
           </button>
           <button 
             onClick={() => onArchive(article.id)}
             className="p-2 hover:bg-slate-100 rounded-full text-slate-600"
           >
             <Archive className="w-5 h-5" />
           </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto relative">
        <div className="max-w-3xl mx-auto px-6 py-10">
          
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4 leading-tight">
            {article.title}
          </h1>
          
          <div className="flex items-center gap-2 text-slate-500 mb-6 pb-6 border-b border-slate-100">
             <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-xs font-bold text-slate-600">
               {article.author.charAt(0)}
             </div>
             <div className="flex flex-col">
               <span className="font-medium text-sm text-slate-900">{article.author}</span>
               <div className="flex items-center text-xs text-slate-400 gap-2">
                 <span>{new Date(article.publishedAt).toLocaleDateString()}</span>
                 <span>•</span>
                 <a href={article.url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline flex items-center gap-1">
                   Original Source <ExternalLink className="w-3 h-3" />
                 </a>
               </div>
             </div>
          </div>

          {/* Image & Sauce Section */}
          {article.imageUrl && (
            <div className="mb-8">
              <div className="relative rounded-xl overflow-hidden bg-slate-100 border border-slate-200 group">
                <img src={article.imageUrl} alt={article.title} className="w-full h-auto" />
                
                {/* Find Sauce Overlay Button */}
                {!article.sauce && (
                  <div className="absolute bottom-4 right-4">
                    <button 
                      onClick={handleFindSauce}
                      disabled={isSearchingSauce}
                      className="flex items-center gap-2 bg-black/70 hover:bg-black/80 text-white px-4 py-2 rounded-lg backdrop-blur-sm text-sm font-medium transition-all"
                    >
                      {isSearchingSauce ? (
                        <Sparkles className="w-4 h-4 animate-spin" />
                      ) : (
                        <Search className="w-4 h-4" />
                      )}
                      {isSearchingSauce ? 'Searching Index...' : 'Find Sauce'}
                    </button>
                  </div>
                )}
              </div>

              {/* Sauce Results */}
              {article.sauce && (
                <div className="mt-3 bg-emerald-50 border border-emerald-100 rounded-lg p-3 flex items-start gap-3 animate-in fade-in slide-in-from-top-2">
                   <div className="bg-emerald-100 p-2 rounded-lg text-emerald-600">
                     <CheckCircle2 className="w-5 h-5" />
                   </div>
                   <div className="flex-1">
                     <div className="flex items-center justify-between mb-1">
                       <h4 className="font-semibold text-emerald-900 text-sm">Sauce Found: {article.sauce.artistName}</h4>
                       <span className="text-xs font-bold bg-emerald-200 text-emerald-800 px-2 py-0.5 rounded-full">
                         {article.sauce.similarity}% Match
                       </span>
                     </div>
                     <p className="text-xs text-emerald-700 mb-2">Original source identified via SauceNAO.</p>
                     <div className="flex items-center gap-2">
                        <a href={article.sauce.sourceUrl} target="_blank" rel="noreferrer" className="text-xs bg-white border border-emerald-200 text-emerald-700 px-2 py-1 rounded hover:bg-emerald-50">
                          View Pixiv/Twitter
                        </a>
                        {article.sauce.extUrl && (
                          <a href={article.sauce.extUrl} target="_blank" rel="noreferrer" className="text-xs bg-white border border-emerald-200 text-emerald-700 px-2 py-1 rounded hover:bg-emerald-50">
                            View Danbooru
                          </a>
                        )}
                     </div>
                   </div>
                </div>
              )}

              {/* Image Metadata Tags */}
              {(article.imageWidth || article.imageHeight) && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {article.imageWidth && article.imageHeight && (
                     <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded border border-slate-200 font-mono">
                       {article.imageWidth}x{article.imageHeight}
                     </span>
                  )}
                  {article.tags.map(tag => (
                    <span key={tag} className="text-xs bg-slate-50 text-slate-500 px-2 py-1 rounded border border-slate-100 hover:border-indigo-200 hover:text-indigo-600 cursor-pointer">
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* AI Summary Section */}
          <div className="mb-8">
            {!aiData?.summary && !isLoadingAI && (
              <button 
                onClick={handleGenerateSummary}
                className="flex items-center gap-2 text-sm font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 px-4 py-2 rounded-lg transition-colors w-full justify-center"
              >
                <Sparkles className="w-4 h-4" />
                Generate AI Summary & Key Takeaways
              </button>
            )}

            {isLoadingAI && (
               <div className="bg-slate-50 rounded-xl p-6 border border-slate-100 animate-pulse">
                 <div className="h-4 bg-slate-200 rounded w-3/4 mb-3"></div>
                 <div className="h-4 bg-slate-200 rounded w-1/2"></div>
               </div>
            )}

            {aiData && (
              <div className="bg-gradient-to-br from-indigo-50 to-white rounded-xl p-6 border border-indigo-100 shadow-sm relative overflow-hidden group">
                 <div className="absolute top-0 right-0 p-4 opacity-10">
                   <Sparkles className="w-24 h-24 text-indigo-600" />
                 </div>
                 
                 <h3 className="font-bold text-indigo-900 mb-2 flex items-center gap-2">
                   <Sparkles className="w-4 h-4 text-indigo-600" />
                   AI Executive Summary
                 </h3>
                 <p className="text-slate-700 leading-relaxed text-sm mb-4">
                   {aiData.summary}
                 </p>
                 
                 {aiData.keyTakeaways && (
                   <div className="space-y-2">
                     <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Key Takeaways</h4>
                     <ul className="space-y-1.5">
                       {aiData.keyTakeaways.map((point, i) => (
                         <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                           <span className="text-indigo-500 mt-1">•</span>
                           {point}
                         </li>
                       ))}
                     </ul>
                   </div>
                 )}
              </div>
            )}
          </div>

          {/* Article Body */}
          <div 
            className="prose prose-slate prose-lg max-w-none prose-headings:font-bold prose-a:text-indigo-600 prose-img:rounded-xl"
            dangerouslySetInnerHTML={{ __html: article.content }}
          />
        </div>
      </div>

      {/* Chat Overlay Pane */}
      {activeTab === 'chat' && (
        <div className="absolute top-16 right-0 bottom-0 w-full md:w-96 bg-white border-l border-slate-200 shadow-2xl flex flex-col z-20 animate-in slide-in-from-right duration-300">
           <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
             <h3 className="font-semibold text-slate-700 flex items-center gap-2">
               <Sparkles className="w-4 h-4 text-indigo-500" />
               Chat with this article
             </h3>
             <button onClick={() => setActiveTab('read')} className="text-slate-400 hover:text-slate-600">
               <X className="w-4 h-4" />
             </button>
           </div>
           
           <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/30">
             {chatHistory.length === 0 && (
               <div className="text-center text-sm text-slate-500 mt-10">
                 Ask anything about this article. <br/> "What is the main argument?"
               </div>
             )}
             {chatHistory.map((msg, idx) => (
               <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                 <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm shadow-sm ${
                   msg.role === 'user' 
                     ? 'bg-indigo-600 text-white rounded-br-none' 
                     : 'bg-white text-slate-700 border border-slate-200 rounded-bl-none'
                 }`}>
                   {msg.text}
                 </div>
               </div>
             ))}
           </div>

           <div className="p-4 bg-white border-t border-slate-200">
             <div className="relative">
               <input 
                 type="text" 
                 value={chatInput}
                 onChange={(e) => setChatInput(e.target.value)}
                 onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                 placeholder="Ask a question..."
                 className="w-full pl-4 pr-10 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm"
               />
               <button 
                 onClick={handleSendMessage}
                 disabled={!chatInput.trim()}
                 className="absolute right-2 top-2 p-1.5 bg-indigo-600 text-white rounded-lg disabled:opacity-50 disabled:bg-slate-300 transition-colors"
               >
                 <Send className="w-4 h-4" />
               </button>
             </div>
           </div>
        </div>
      )}
    </div>
  );
};

// Helper component for Sauce Result icon
function CheckCircle2({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="12" cy="12" r="10"/>
      <path d="m9 12 2 2 4-4"/>
    </svg>
  );
}