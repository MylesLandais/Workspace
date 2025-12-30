import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface SourceData {
  name: string;
  count: number;
}

interface TopSourcesProps {
  data: SourceData[];
}

export default function TopSources({ data }: TopSourcesProps) {
  const sortedData = [...data].sort((a, b) => b.count - a.count).slice(0, 8);

  return (
    <div className="bg-theme-bg-secondary border border-theme-border-primary rounded-xl p-6">
      <h3 className="text-lg font-semibold text-theme-text-primary mb-6">Top Sources</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={sortedData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--theme-border-primary)" />
          <XAxis type="number" stroke="var(--theme-text-secondary)" style={{ fontSize: '12px' }} />
          <YAxis
            dataKey="name"
            type="category"
            stroke="var(--theme-text-secondary)"
            style={{ fontSize: '12px' }}
            width={70}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--theme-bg-secondary)',
              border: '1px solid var(--theme-border-primary)',
              borderRadius: '8px',
              color: 'var(--theme-text-primary)',
            }}
          />
          <Bar
            dataKey="count"
            fill="var(--theme-accent-primary)"
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

