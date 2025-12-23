import { useState, useEffect } from 'react';
import { loadAllSubredditData, type SourcePreview } from '../../lib/mock-data/loader';

export interface Source {
  id: string;
  name: string;
  subredditName?: string;
  sourceType: 'reddit' | 'youtube' | 'twitter';
  youtubeHandle?: string;
  entityId?: string;
  entityName?: string;
  group: string;
  tags: string[];
  isPaused: boolean;
  lastSynced: string | null;
  mediaCount: number;
  health: 'green' | 'yellow' | 'red';
}

interface SourcesBoardViewProps {
  sources: Source[];
  selectedGroup: string;
  sourcesFilter: string;
  onTogglePause: (sourceId: string) => void;
  onDelete: (sourceId: string) => void;
}

interface SourceCard extends Source {
  previewImage?: string;
  previewPosts?: number;
}

const PLATFORM_COLORS: Record<string, string> = {
  reddit: 'bg-orange-600',
  youtube: 'bg-red-600',
  twitter: 'bg-blue-500',
};

function getHealthColor(health: string): string {
  switch (health) {
    case 'green': return 'bg-green-500';
    case 'yellow': return 'bg-yellow-500';
    case 'red': return 'bg-red-500';
      default: return 'bg-theme-text-secondary';
  }
}

function formatTimeAgo(timestamp: string | null): string {
  if (!timestamp) return 'Never';
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.floor(diffMs / 86400000)}d ago`;
}

export default function SourcesBoardView({
  sources,
  selectedGroup,
  sourcesFilter,
  onTogglePause,
  onDelete,
}: SourcesBoardViewProps) {
  const [sourceCards, setSourceCards] = useState<SourceCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewData, setPreviewData] = useState<Map<string, SourcePreview>>(new Map());

  useEffect(() => {
    async function loadPreviewData() {
      setLoading(true);
      const data = await loadAllSubredditData();
      setPreviewData(data);
      setLoading(false);
    }
    loadPreviewData();
  }, []);

  useEffect(() => {
    const filtered = sources.filter((source) => {
      if (selectedGroup !== 'all' && source.group !== selectedGroup) return false;
      if (sourcesFilter) {
        const filterLower = sourcesFilter.toLowerCase();
        const matchesName = source.name.toLowerCase().includes(filterLower);
        const matchesSubreddit = source.subredditName?.toLowerCase().includes(filterLower);
        const matchesYoutube = source.youtubeHandle?.toLowerCase().includes(filterLower);
        const matchesEntity = source.entityName?.toLowerCase().includes(filterLower);
        if (!matchesName && !matchesSubreddit && !matchesYoutube && !matchesEntity) return false;
      }
      return true;
    });

    const cards: SourceCard[] = filtered.map((source) => {
      const preview = source.subredditName ? previewData.get(source.subredditName) : undefined;
      return {
        ...source,
        previewImage: preview?.previewImage,
        previewPosts: preview?.totalPosts,
      };
    });

    setSourceCards(cards);
  }, [sources, selectedGroup, sourcesFilter, previewData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-theme-accent-primary"></div>
      </div>
    );
  }

  return (
    <div className="py-6">
      <div className="columns-1 sm:columns-2 md:columns-3 lg:columns-4 xl:columns-5 gap-4">
        {sourceCards.map((source) => (
          <div
            key={source.id}
            className="group mb-4 break-inside-avoid bg-theme-bg-secondary rounded-lg overflow-hidden cursor-pointer hover:bg-theme-bg-primary transition-all duration-200 hover:scale-[1.02]"
          >
            <div className="relative">
              {source.previewImage ? (
                <>
                  <img
                    src={source.previewImage}
                    alt={source.name}
                    loading="lazy"
                    className="w-full h-auto object-cover"
                  />
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors duration-200" />
                </>
              ) : (
                <div className="w-full aspect-square bg-gradient-to-br from-theme-bg-primary to-theme-bg-secondary flex items-center justify-center">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl font-semibold ${
                    source.sourceType === 'reddit' ? 'bg-orange-600' :
                    source.sourceType === 'youtube' ? 'bg-red-600' :
                    'bg-theme-bg-secondary'
                  }`}>
                    {source.sourceType === 'reddit' ? 'r/' : 
                     source.sourceType === 'youtube' ? 'YT' : 
                     source.sourceType === 'twitter' ? '@' : '?'}
                  </div>
                </div>
              )}
              
              <div className="absolute top-2 right-2 flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${getHealthColor(source.health)}`} />
                  <span className={`px-2 py-1 rounded text-xs font-semibold text-white ${PLATFORM_COLORS[source.sourceType] || 'bg-theme-bg-secondary'}`}>
                  {source.sourceType === 'reddit' ? 'r/' : 
                   source.sourceType === 'youtube' ? 'YT' : 
                   source.sourceType === 'twitter' ? '@' : '?'}
                </span>
              </div>

              <div className="absolute bottom-0 left-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-gradient-to-t from-black/80 to-transparent">
                <div className="text-white">
                  <h3 className="font-semibold text-sm mb-1 line-clamp-1">
                    {source.sourceType === 'reddit' ? `r/${source.name}` :
                     source.sourceType === 'youtube' ? source.youtubeHandle || source.name :
                     source.name}
                  </h3>
                  {source.entityName && (
                    <p className="text-xs text-blue-300 mb-1">{source.entityName}</p>
                  )}
                  <div className="flex items-center gap-3 text-xs text-theme-text-secondary mt-2">
                    <span>{source.mediaCount.toLocaleString()} media</span>
                    <span>•</span>
                    <span>{formatTimeAgo(source.lastSynced)}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-3 bg-theme-bg-secondary">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-theme-text-secondary">{source.group}</span>
                  <div className="flex flex-wrap gap-1">
                    {source.tags.slice(0, 2).map((tag) => (
                      <span
                        key={tag}
                        className="px-1.5 py-0.5 text-xs rounded bg-theme-bg-primary text-theme-text-secondary border border-theme-border-primary"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onTogglePause(source.id);
                  }}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                    source.isPaused ? 'bg-theme-bg-secondary' : 'bg-theme-accent-primary'
                  }`}
                >
                  <span
                    className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                      source.isPaused ? 'translate-x-1' : 'translate-x-5'
                    }`}
                  />
                </button>
              </div>
              
              <div className="flex items-center justify-between">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('Are you sure you want to remove this source?')) {
                      onDelete(source.id);
                    }
                  }}
                  className="p-1 text-theme-text-secondary hover:text-theme-accent-alert transition-colors"
                  title="Delete"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {sourceCards.length === 0 && (
        <div className="text-center py-12 text-theme-text-secondary">
          <p>No sources found matching your filters.</p>
        </div>
      )}
    </div>
  );
}

