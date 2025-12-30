import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface DataPoint {
  date: string;
  imagesIngested: number;
  duplicatesDetected: number;
}

interface ActivityTimelineProps {
  data: DataPoint[];
}

export default function ActivityTimeline({ data }: ActivityTimelineProps) {
  const [timeRange, setTimeRange] = useState<'30D' | '7D'>('30D');

  const filteredData = timeRange === '7D' ? data.slice(-7) : data;

  return (
    <div className="bg-theme-bg-secondary border border-theme-border-primary rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-theme-text-primary">Activity Timeline</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setTimeRange('30D')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              timeRange === '30D'
                ? 'bg-theme-accent-primary text-theme-bg-primary'
                : 'bg-theme-bg-primary text-theme-text-secondary hover:text-theme-text-primary'
            }`}
          >
            30D
          </button>
          <button
            onClick={() => setTimeRange('7D')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              timeRange === '7D'
                ? 'bg-theme-accent-primary text-theme-bg-primary'
                : 'bg-theme-bg-primary text-theme-text-secondary hover:text-theme-text-primary'
            }`}
          >
            7D
          </button>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={filteredData}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--theme-border-primary)" />
          <XAxis
            dataKey="date"
            stroke="var(--theme-text-secondary)"
            style={{ fontSize: '12px' }}
          />
          <YAxis stroke="var(--theme-text-secondary)" style={{ fontSize: '12px' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--theme-bg-secondary)',
              border: '1px solid var(--theme-border-primary)',
              borderRadius: '8px',
              color: 'var(--theme-text-primary)',
            }}
          />
          <Legend
            wrapperStyle={{ color: 'var(--theme-text-primary)' }}
            iconType="circle"
          />
          <Line
            type="monotone"
            dataKey="imagesIngested"
            stroke="var(--theme-accent-tertiary)"
            strokeWidth={2}
            dot={false}
            name="Images Ingested"
          />
          <Line
            type="monotone"
            dataKey="duplicatesDetected"
            stroke="var(--theme-accent-primary)"
            strokeWidth={2}
            dot={false}
            name="Duplicates Detected"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

