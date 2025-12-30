import React from 'react';
import { Article } from './types';
import { TrendingUp, PieChart as PieIcon, Activity } from 'lucide-react';

interface InsightsViewProps {
  articles: Article[];
}

export const InsightsView: React.FC<InsightsViewProps> = ({ articles }) => {
  
  const totalReads = articles.filter(a => a.read).length;
  const savedCount = articles.filter(a => a.saved).length;

  return (
    <div className="flex flex-col h-full bg-app-bg overflow-y-auto">
      <div className="p-8 pb-4">
        <h1 className="text-2xl font-bold text-app-text mb-2">Content Insights</h1>
        <p className="text-app-muted text-sm">Analysis of your reading habits and content sources.</p>
      </div>

      <div className="p-8 pt-0 grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-6xl">
        
        {/* Key Metrics */}
        <div className="col-span-1 lg:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-app-surface p-6 rounded-xl border border-app-border shadow-sm flex items-center justify-between">
             <div>
               <p className="text-xs font-semibold text-app-muted uppercase">Total Items</p>
               <p className="text-3xl font-bold text-app-text">{articles.length}</p>
             </div>
             <div className="p-3 bg-app-accent/20 rounded-full text-app-accent">
               <Activity className="w-6 h-6" />
             </div>
          </div>
          <div className="bg-app-surface p-6 rounded-xl border border-app-border shadow-sm flex items-center justify-between">
             <div>
               <p className="text-xs font-semibold text-app-muted uppercase">Read Ratio</p>
               <p className="text-3xl font-bold text-app-text">
                 {articles.length > 0 ? Math.round((totalReads / articles.length) * 100) : 0}%
               </p>
             </div>
             <div className="p-3 bg-app-accent/20 rounded-full text-app-accent">
               <TrendingUp className="w-6 h-6" />
             </div>
          </div>
          <div className="bg-app-surface p-6 rounded-xl border border-app-border shadow-sm flex items-center justify-between">
             <div>
               <p className="text-xs font-semibold text-app-muted uppercase">Saved for Later</p>
               <p className="text-3xl font-bold text-app-text">{savedCount}</p>
             </div>
             <div className="p-3 bg-app-accent/20 rounded-full text-app-accent">
               <PieIcon className="w-6 h-6" />
             </div>
          </div>
        </div>

        {/* Placeholder for charts - can be extended with recharts later */}
        <div className="bg-app-surface p-6 rounded-xl border border-app-border shadow-sm">
          <h3 className="text-lg font-semibold text-app-text mb-4">Source Breakdown</h3>
          <p className="text-app-muted text-sm">Chart visualization coming soon</p>
        </div>

      </div>
    </div>
  );
};





