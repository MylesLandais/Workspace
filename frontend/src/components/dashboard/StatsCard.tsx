import React from 'react';

interface StatsCardProps {
  title: string;
  value: string | number;
  description: string;
  change?: string;
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon: React.ReactNode;
}

export default function StatsCard({
  title,
  value,
  description,
  change,
  changeType = 'neutral',
  icon,
}: StatsCardProps) {
  const changeColor =
    changeType === 'increase'
      ? 'text-theme-accent-primary'
      : changeType === 'decrease'
      ? 'text-theme-accent-alert'
      : 'text-theme-text-secondary';

  const changeIcon =
    changeType === 'increase' ? (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
      </svg>
    ) : changeType === 'decrease' ? (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
      </svg>
    ) : (
      <span className="text-xs">•</span>
    );

  return (
    <div className="bg-theme-bg-secondary border border-theme-border-primary rounded-xl p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <p className="text-sm text-theme-text-secondary mb-1">{title}</p>
          <p className="text-3xl font-bold text-theme-text-primary mb-1">{value}</p>
          <p className="text-xs text-theme-text-secondary">{description}</p>
        </div>
        <div className="text-theme-accent-primary">{icon}</div>
      </div>
      {change && (
        <div className={`flex items-center space-x-1 text-sm ${changeColor}`}>
          {changeIcon}
          <span>{change}</span>
        </div>
      )}
    </div>
  );
}

