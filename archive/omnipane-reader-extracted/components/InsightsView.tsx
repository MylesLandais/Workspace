import React from 'react';
import { 
  PieChart, Pie, Cell, 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Legend
} from 'recharts';
import { Article, SourceType } from '../types';
import { TrendingUp, PieChart as PieIcon, Activity } from 'lucide-react';

interface InsightsViewProps {
  articles: Article[];
}

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export const InsightsView: React.FC<InsightsViewProps> = ({ articles }) => {
  
  // Aggregate Source Data
  const sourceData = React.useMemo(() => {
    const counts: Record<string, number> = {};
    articles.forEach(a => {
      counts[a.type] = (counts[a.type] || 0) + 1;
    });
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [articles]);

  // Aggregate Tag Data
  const tagData = React.useMemo(() => {
    const counts: Record<string, number> = {};
    articles.forEach(a => {
      a.tags.forEach(tag => {
        counts[tag] = (counts[tag] || 0) + 1;
      });
    });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 7) // Top 7 tags
      .map(([name, count]) => ({ name, count }));
  }, [articles]);

  const totalReads = articles.filter(a => a.read).length;
  const savedCount = articles.filter(a => a.saved).length;

  return (
    <div className="flex flex-col h-full bg-slate-50 overflow-y-auto">
      <div className="p-8 pb-4">
        <h1 className="text-2xl font-bold text-slate-900 mb-2">Content Insights</h1>
        <p className="text-slate-500 text-sm">Analysis of your reading habits and content sources.</p>
      </div>

      <div className="p-8 pt-0 grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-6xl">
        
        {/* Key Metrics */}
        <div className="col-span-1 lg:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
             <div>
               <p className="text-xs font-semibold text-slate-400 uppercase">Total Items</p>
               <p className="text-3xl font-bold text-slate-800">{articles.length}</p>
             </div>
             <div className="p-3 bg-indigo-50 rounded-full text-indigo-600">
               <Activity className="w-6 h-6" />
             </div>
          </div>
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
             <div>
               <p className="text-xs font-semibold text-slate-400 uppercase">Read Ratio</p>
               <p className="text-3xl font-bold text-slate-800">{Math.round((totalReads / articles.length) * 100)}%</p>
             </div>
             <div className="p-3 bg-emerald-50 rounded-full text-emerald-600">
               <TrendingUp className="w-6 h-6" />
             </div>
          </div>
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
             <div>
               <p className="text-xs font-semibold text-slate-400 uppercase">Saved for Later</p>
               <p className="text-3xl font-bold text-slate-800">{savedCount}</p>
             </div>
             <div className="p-3 bg-orange-50 rounded-full text-orange-600">
               <PieIcon className="w-6 h-6" />
             </div>
          </div>
        </div>

        {/* Source Distribution */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm min-h-[400px]">
          <h3 className="text-lg font-semibold text-slate-800 mb-6 flex items-center gap-2">
            <PieIcon className="w-4 h-4 text-slate-400" />
            Source Breakdown
          </h3>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sourceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {sourceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                   contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                   itemStyle={{ color: '#1e293b' }}
                />
                <Legend verticalAlign="bottom" height={36} iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Topic Distribution */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm min-h-[400px]">
          <h3 className="text-lg font-semibold text-slate-800 mb-6 flex items-center gap-2">
            <Activity className="w-4 h-4 text-slate-400" />
            Top Topics
          </h3>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tagData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <XAxis type="number" hide />
                <YAxis 
                  dataKey="name" 
                  type="category" 
                  tick={{ fontSize: 12, fill: '#64748b' }} 
                  width={100}
                />
                <Tooltip 
                   cursor={{ fill: '#f1f5f9' }}
                   contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                />
                <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
};