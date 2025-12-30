import React, { useState } from 'react';
import StatsCard from './StatsCard';
import AIInsights from './AIInsights';
import ActivityTimeline from './ActivityTimeline';
import TopSources from './TopSources';
import FlaggedContentTable from './FlaggedContentTable';

interface DashboardData {
  ingested: { value: number; change: string };
  clusters: { value: number; change: string };
  duplicateRate: { value: number; change: string };
  alerts: { value: number; change: string };
  activityTimeline: Array<{
    date: string;
    imagesIngested: number;
    duplicatesDetected: number;
  }>;
  topSources: Array<{ name: string; count: number }>;
  flaggedContent: Array<{
    id: string;
    imageUrl: string;
    clusterId: string;
    count: number;
    communities: string[];
    firstSeen: string;
  }>;
}

const MOCK_DASHBOARD_DATA: DashboardData = {
  ingested: { value: 36794, change: '↑ 12%' },
  clusters: { value: 14707, change: '• 2%' },
  duplicateRate: { value: 23.3, change: '↑ 4.5%' },
  alerts: { value: 12, change: '↓ 2' },
  activityTimeline: [
    { date: 'Nov 24', imagesIngested: 1200, duplicatesDetected: 280 },
    { date: 'Nov 27', imagesIngested: 1350, duplicatesDetected: 310 },
    { date: 'Nov 30', imagesIngested: 1100, duplicatesDetected: 260 },
    { date: 'Dec 3', imagesIngested: 1450, duplicatesDetected: 340 },
    { date: 'Dec 6', imagesIngested: 1300, duplicatesDetected: 300 },
    { date: 'Dec 9', imagesIngested: 1500, duplicatesDetected: 350 },
    { date: 'Dec 12', imagesIngested: 1400, duplicatesDetected: 320 },
    { date: 'Dec 15', imagesIngested: 1600, duplicatesDetected: 380 },
    { date: 'Dec 18', imagesIngested: 1550, duplicatesDetected: 360 },
    { date: 'Dec 21', imagesIngested: 1650, duplicatesDetected: 390 },
    { date: 'Dec 22', imagesIngested: 1700, duplicatesDetected: 400 },
  ],
  topSources: [
    { name: 'r/pics', count: 8500 },
    { name: 'r/videos', count: 7200 },
    { name: 'r/memes', count: 6800 },
    { name: 'r/news', count: 6200 },
    { name: 'r/gaming', count: 5800 },
    { name: 'r/funny', count: 5400 },
    { name: 'r/aww', count: 4900 },
    { name: 'r/todayilearned', count: 4500 },
  ],
  flaggedContent: [
    {
      id: '1',
      imageUrl: 'https://via.placeholder.com/64',
      clusterId: 'cls-7419op2g0',
      count: 166,
      communities: ['r/news', 'r/memes'],
      firstSeen: '11/23/2025',
    },
  ],
};

function getCurrentDateString(): string {
  const now = new Date();
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const months = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
  ];
  return `${days[now.getDay()]}, ${months[now.getMonth()]} ${now.getDate()}.`;
}

export default function DashboardView() {
  const [data] = useState<DashboardData>(MOCK_DASHBOARD_DATA);
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="min-h-screen bg-theme-bg-primary">
      <div className="p-6">
        <header className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-theme-text-primary mb-1">Dashboard</h1>
              <p className="text-sm text-theme-text-secondary">Overview of content patterns for {getCurrentDateString()}</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg
                    className="h-5 w-5 text-theme-text-secondary"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search..."
                  className="pl-10 pr-4 py-2 bg-theme-bg-secondary border border-theme-border-primary rounded-lg text-theme-text-primary placeholder-theme-text-secondary focus:outline-none focus:ring-2 focus:ring-theme-accent-primary"
                />
              </div>
              <button className="relative p-2 text-theme-text-secondary hover:text-theme-text-primary transition-colors">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                <span className="absolute top-0 right-0 w-2 h-2 bg-theme-accent-alert rounded-full"></span>
              </button>
              <div className="w-10 h-10 rounded-full bg-theme-accent-secondary flex items-center justify-center text-theme-text-primary font-semibold">
                AD
              </div>
            </div>
          </div>
        </header>

        <div className="space-y-6">
          <AIInsights />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatsCard
              title="Ingested"
              value={data.ingested.value.toLocaleString()}
              description="Last 30 days"
              change={data.ingested.change}
              changeType="increase"
              icon={
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              }
            />
            <StatsCard
              title="Clusters"
              value={data.clusters.value.toLocaleString()}
              description="Active groups"
              change={data.clusters.change}
              changeType="neutral"
              icon={
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                  />
                </svg>
              }
            />
            <StatsCard
              title="Dup. Rate"
              value={`${data.duplicateRate.value}%`}
              description="Flagged content"
              change={data.duplicateRate.change}
              changeType="increase"
              icon={
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
                  />
                </svg>
              }
            />
            <StatsCard
              title="Alerts"
              value={data.alerts.value}
              description="Pending review"
              change={data.alerts.change}
              changeType="decrease"
              icon={
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
              }
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ActivityTimeline data={data.activityTimeline} />
            <TopSources data={data.topSources} />
          </div>

          <FlaggedContentTable data={data.flaggedContent} />
        </div>
      </div>
    </div>
  );
}

