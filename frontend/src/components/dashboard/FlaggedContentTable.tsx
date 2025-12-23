import React from 'react';

interface FlaggedContentItem {
  id: string;
  imageUrl: string;
  clusterId: string;
  count: number;
  communities: string[];
  firstSeen: string;
}

interface FlaggedContentTableProps {
  data: FlaggedContentItem[];
}

export default function FlaggedContentTable({ data }: FlaggedContentTableProps) {
  const handleExportCSV = () => {
    const headers = ['IMAGE', 'CLUSTER ID', 'COUNT', 'COMMUNITIES', 'FIRST SEEN'];
    const rows = data.map((item) => [
      item.imageUrl,
      item.clusterId,
      item.count.toString(),
      item.communities.join(' '),
      item.firstSeen,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'flagged-content.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-theme-bg-secondary border border-theme-border-primary rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-theme-text-primary">Flagged Content</h3>
        <button
          onClick={handleExportCSV}
          className="px-4 py-2 bg-theme-bg-primary hover:bg-theme-bg-primary/80 border border-theme-border-primary rounded-lg text-theme-text-primary text-sm font-medium transition-colors"
        >
          EXPORT CSV
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-theme-border-primary">
              <th className="text-left p-4 text-xs font-semibold text-theme-text-secondary uppercase tracking-wider">
                IMAGE
              </th>
              <th className="text-left p-4 text-xs font-semibold text-theme-text-secondary uppercase tracking-wider">
                CLUSTER ID
              </th>
              <th className="text-left p-4 text-xs font-semibold text-theme-text-secondary uppercase tracking-wider">
                COUNT
              </th>
              <th className="text-left p-4 text-xs font-semibold text-theme-text-secondary uppercase tracking-wider">
                COMMUNITIES
              </th>
              <th className="text-left p-4 text-xs font-semibold text-theme-text-secondary uppercase tracking-wider">
                FIRST SEEN
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-theme-border-primary">
            {data.map((item) => (
              <tr key={item.id} className="hover:bg-theme-bg-primary transition-colors">
                <td className="p-4">
                  <img
                    src={item.imageUrl}
                    alt={`Cluster ${item.clusterId}`}
                    className="w-16 h-16 object-cover rounded"
                  />
                </td>
                <td className="p-4">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-theme-text-primary font-mono">{item.clusterId}</span>
                    <a
                      href={`/cluster/${item.clusterId}`}
                      className="text-theme-accent-primary hover:text-theme-accent-primary/80"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                        />
                      </svg>
                    </a>
                  </div>
                </td>
                <td className="p-4">
                  <span className="text-sm text-theme-text-primary font-semibold">{item.count}</span>
                </td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-1">
                    {item.communities.map((community, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 text-xs bg-theme-bg-primary border border-theme-border-primary rounded text-theme-text-secondary"
                      >
                        {community}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="p-4">
                  <span className="text-sm text-theme-text-secondary">{item.firstSeen}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

