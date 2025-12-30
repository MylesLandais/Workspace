import React from 'react';
import { 
  Inbox, 
  Clock, 
  Archive, 
  Rss, 
  Twitter, 
  Mail, 
  Youtube, 
  Plus,
  Settings,
  Hash,
  BarChart2,
  MessageSquare,
  Image as ImageIcon,
  Eye,
  Pin
} from 'lucide-react';
import { FeedSource, ViewMode, Board } from '../types';

interface SidebarProps {
  feeds: FeedSource[];
  boards: Board[];
  activeView: ViewMode;
  onViewChange: (view: ViewMode) => void;
  onFeedSelect: (feedId: string | null) => void;
  onTagSelect: (tag: string) => void;
  onBoardSelect: (boardId: string) => void;
  activeFeedId: string | null;
  activeTag: string | null;
  activeBoardId: string | null;
  tags: {name: string, count: number}[];
  className?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  feeds, 
  boards,
  activeView, 
  onViewChange, 
  onFeedSelect,
  onTagSelect,
  onBoardSelect,
  activeFeedId,
  activeTag,
  activeBoardId,
  tags,
  className = "" 
}) => {
  
  const getIconForType = (type: string) => {
    switch(type) {
      case 'twitter': return <Twitter className="w-4 h-4 text-blue-400" />;
      case 'newsletter': return <Mail className="w-4 h-4 text-orange-400" />;
      case 'youtube': return <Youtube className="w-4 h-4 text-red-500" />;
      case 'reddit': return <MessageSquare className="w-4 h-4 text-orange-600" />;
      case 'booru': return <ImageIcon className="w-4 h-4 text-pink-500" />;
      case 'monitor': return <Eye className="w-4 h-4 text-emerald-500" />;
      default: return <Rss className="w-4 h-4 text-slate-500" />;
    }
  };

  const NavItem = ({ 
    icon: Icon, 
    label, 
    isActive, 
    onClick,
    count
  }: { icon: any, label: string, isActive: boolean, onClick: () => void, count?: number }) => (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
        isActive 
          ? 'bg-indigo-50 text-indigo-700 font-medium' 
          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
      }`}
    >
      <div className="flex items-center gap-3">
        <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-600' : 'text-slate-500'}`} />
        <span>{label}</span>
      </div>
      {count !== undefined && count > 0 && (
        <span className={`text-xs px-2 py-0.5 rounded-full ${isActive ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-200 text-slate-600'}`}>
          {count}
        </span>
      )}
    </button>
  );

  return (
    <div className={`flex flex-col h-full bg-slate-50 border-r border-slate-200 ${className}`}>
      {/* App Header */}
      <div className="p-4 border-b border-slate-200/50">
        <div className="flex items-center gap-2 font-bold text-slate-800 text-lg">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white">
            <Inbox className="w-5 h-5" />
          </div>
          OmniPane
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Main Navigation */}
        <div className="p-3 space-y-1">
          <NavItem 
            icon={Inbox} 
            label="Inbox" 
            isActive={activeView === 'inbox'} 
            onClick={() => { onViewChange('inbox'); onFeedSelect(null); }}
            count={3} 
          />
          <NavItem 
            icon={Clock} 
            label="Read Later" 
            isActive={activeView === 'later'} 
            onClick={() => { onViewChange('later'); onFeedSelect(null); }}
            count={2}
          />
          <NavItem 
            icon={Archive} 
            label="Archive" 
            isActive={activeView === 'archive'} 
            onClick={() => { onViewChange('archive'); onFeedSelect(null); }}
          />
           <NavItem 
            icon={BarChart2} 
            label="Insights" 
            isActive={activeView === 'analytics'} 
            onClick={() => { onViewChange('analytics'); onFeedSelect(null); }}
          />
        </div>

        {/* Boards Section (Pinterest Style) */}
        <div className="px-4 pt-4 pb-2 flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider">
          <span>Boards</span>
          <button className="hover:text-indigo-600"><Plus className="w-3 h-3" /></button>
        </div>
        <div className="px-3 space-y-0.5 mb-2">
           {boards.map(board => (
             <button
              key={board.id}
              onClick={() => onBoardSelect(board.id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                activeBoardId === board.id && activeView === 'board'
                  ? 'bg-white shadow-sm border border-slate-200 text-slate-900' 
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
             >
               <div className="flex items-center gap-3">
                 <Pin className="w-3.5 h-3.5 text-slate-400" />
                 <span className="truncate">{board.name}</span>
               </div>
               <span className="text-xs text-slate-400">{board.articleIds.length}</span>
             </button>
           ))}
        </div>

        {/* Feeds Section */}
        <div className="px-4 pt-4 pb-2 flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider">
          <span>Sources</span>
          <button className="hover:text-indigo-600"><Plus className="w-3 h-3" /></button>
        </div>
        
        <div className="px-3 space-y-0.5 mb-4">
          {feeds.map(feed => (
            <button
              key={feed.id}
              onClick={() => { onViewChange('feed'); onFeedSelect(feed.id); }}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                activeFeedId === feed.id && activeView === 'feed'
                  ? 'bg-white shadow-sm border border-slate-200 text-slate-900' 
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <div className="flex items-center gap-3">
                {getIconForType(feed.type)}
                <span className="truncate max-w-[140px]">{feed.name}</span>
              </div>
              {feed.unreadCount > 0 && (
                <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
              )}
            </button>
          ))}
        </div>

        {/* Topics/Tags Section */}
        <div className="px-4 pt-2 pb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          <span>Topics</span>
        </div>
        <div className="px-3 space-y-0.5 pb-4">
          {tags.map(tag => (
            <button
              key={tag.name}
              onClick={() => onTagSelect(tag.name)}
              className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-sm transition-colors ${
                activeTag === tag.name && activeView === 'tag'
                  ? 'bg-indigo-50 text-indigo-700 font-medium'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <div className="flex items-center gap-3">
                <Hash className="w-3 h-3 text-slate-400" />
                <span className="truncate">{tag.name}</span>
              </div>
              <span className="text-xs text-slate-400">{tag.count}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="p-3 mt-auto border-t border-slate-200 flex-shrink-0">
        <NavItem icon={Settings} label="Settings" isActive={false} onClick={() => {}} />
      </div>
    </div>
  );
};