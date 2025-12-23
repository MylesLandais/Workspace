import { useState, useEffect } from 'react';
import { useQuery, useLazyQuery, useMutation } from '@apollo/client';
import { ApolloProvider } from '@apollo/client';
import { apolloClient, isMock } from '../../lib/graphql/client';
import { SOURCES_QUERY, FEED_GROUPS_QUERY, SEARCH_SUBREDDITS_QUERY } from '../../lib/graphql/queries';
import { SUBSCRIBE_TO_SOURCE, TOGGLE_HANDLE_PAUSE, REMOVE_HANDLE } from '../../lib/graphql/mutations';
import SourcesBoardView from './SourcesBoardView';

interface Subreddit {
  name: string;
  displayName: string;
  subscriberCount: number;
  description: string;
  iconUrl?: string;
  isSubscribed: boolean;
}

interface Source {
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

// Mock search results
const MOCK_SEARCH_RESULTS: Subreddit[] = [
  {
    name: 'Sjokz',
    displayName: 'Sjokz',
    subscriberCount: 12500,
    description: 'Community for Sjokz content and discussions',
    isSubscribed: true,
  },
  {
    name: 'Overwatch',
    displayName: 'Overwatch',
    subscriberCount: 3200000,
    description: 'Overwatch news, discussion, and highlights',
    isSubscribed: false,
  },
  {
    name: 'FortNiteBR',
    displayName: 'Fortnite Battle Royale',
    subscriberCount: 2800000,
    description: 'Fortnite Battle Royale subreddit',
    isSubscribed: false,
  },
  {
    name: 'Minecraft',
    displayName: 'Minecraft',
    subscriberCount: 5200000,
    description: 'Minecraft community',
    isSubscribed: false,
  },
];

// Mock existing sources with entity relationships - updated with data from temp/mock_data
const MOCK_SOURCES: Source[] = [
  // Sjokz entity - Reddit and YouTube (from temp data: 25 posts)
  { id: '1', name: 'Sjokz', subredditName: 'Sjokz', sourceType: 'reddit', entityId: 'sjokz', entityName: 'Sjokz', group: 'Esports', tags: ['Esports', 'Personality'], isPaused: false, lastSynced: '2025-12-22T10:15:00Z', mediaCount: 25, health: 'green' },
  { id: '1-yt', name: 'Sjokz YouTube', youtubeHandle: '@sjokz', sourceType: 'youtube', entityId: 'sjokz', entityName: 'Sjokz', group: 'Esports', tags: ['Esports', 'Personality'], isPaused: false, lastSynced: '2025-12-22T10:14:00Z', mediaCount: 3421, health: 'green' },
  // Brooke Monk entity - Reddit and YouTube (from temp data: 31 posts)
  { id: 'brooke-1', name: 'BrookeMonkTheSecond', subredditName: 'BrookeMonkTheSecond', sourceType: 'reddit', entityId: 'brooke-monk', entityName: 'Brooke Monk', group: 'Personalities', tags: ['Personality', 'Content Creator'], isPaused: false, lastSynced: '2025-12-22T10:16:00Z', mediaCount: 31, health: 'green' },
  { id: 'brooke-2', name: 'BestOfBrookeMonk', subredditName: 'BestOfBrookeMonk', sourceType: 'reddit', entityId: 'brooke-monk', entityName: 'Brooke Monk', group: 'Personalities', tags: ['Personality', 'Content Creator'], isPaused: false, lastSynced: '2025-12-22T10:15:00Z', mediaCount: 10, health: 'green' },
  { id: 'brooke-3', name: 'BrookeMonkNSFWHub', subredditName: 'BrookeMonkNSFWHub', sourceType: 'reddit', entityId: 'brooke-monk', entityName: 'Brooke Monk', group: 'Personalities', tags: ['Personality', 'Content Creator'], isPaused: false, lastSynced: '2025-12-22T10:19:00Z', mediaCount: 318, health: 'green' },
  { id: 'brooke-yt', name: 'Brooke Monk YouTube', youtubeHandle: '@BrookeMonk', sourceType: 'youtube', entityId: 'brooke-monk', entityName: 'Brooke Monk', group: 'Personalities', tags: ['Personality', 'Content Creator'], isPaused: false, lastSynced: '2025-12-22T10:15:00Z', mediaCount: 12567, health: 'green' },
  // Ovilee entity - Reddit (from temp data: 51 posts)
  { id: 'ovilee-1', name: 'OvileeWorship', subredditName: 'OvileeWorship', sourceType: 'reddit', entityId: 'ovilee', entityName: 'Ovilee', group: 'Esports', tags: ['Esports', 'Personality'], isPaused: false, lastSynced: '2025-12-22T10:17:00Z', mediaCount: 51, health: 'green' },
  // Triangl (from temp data: 97 posts)
  { id: 'triangl-1', name: 'Triangl', subredditName: 'Triangl', sourceType: 'reddit', group: 'Fashion', tags: ['Fashion', 'Lifestyle'], isPaused: false, lastSynced: '2025-12-22T10:18:00Z', mediaCount: 97, health: 'green' },
  // howdyhowdyyallhot (from temp data: 220 images)
  { id: 'howdy-1', name: 'howdyhowdyyallhot', subredditName: 'howdyhowdyyallhot', sourceType: 'reddit', entityId: 'howdy', entityName: 'Howdy', group: 'Personalities', tags: ['Personality', 'Content Creator'], isPaused: false, lastSynced: '2025-12-22T10:20:00Z', mediaCount: 220, health: 'green' },
  // Other sources
  { id: '2', name: 'leagueoflegends', subredditName: 'leagueoflegends', sourceType: 'reddit', group: 'Gaming', tags: ['Gaming', 'MOBA'], isPaused: false, lastSynced: '2025-12-22T10:12:00Z', mediaCount: 8934, health: 'green' },
  { id: '3', name: 'VALORANT', subredditName: 'VALORANT', sourceType: 'reddit', group: 'Gaming', tags: ['Gaming', 'FPS'], isPaused: false, lastSynced: '2025-12-22T10:10:00Z', mediaCount: 5621, health: 'green' },
  { id: '4', name: 'GlobalOffensive', subredditName: 'GlobalOffensive', sourceType: 'reddit', group: 'Gaming', tags: ['Gaming', 'FPS'], isPaused: false, lastSynced: '2025-12-22T10:08:00Z', mediaCount: 7823, health: 'green' },
  { id: '5', name: 'programming', subredditName: 'programming', sourceType: 'reddit', group: 'Tech', tags: ['Tech', 'Programming'], isPaused: false, lastSynced: '2025-12-22T10:14:00Z', mediaCount: 1234, health: 'green' },
  { id: '6', name: 'webdev', subredditName: 'webdev', sourceType: 'reddit', group: 'Tech', tags: ['Tech', 'Web Development'], isPaused: false, lastSynced: '2025-12-22T10:13:00Z', mediaCount: 890, health: 'green' },
  { id: '7', name: 'graphic_design', subredditName: 'graphic_design', sourceType: 'reddit', group: 'Design', tags: ['Design', 'Graphics'], isPaused: false, lastSynced: '2025-12-22T10:07:00Z', mediaCount: 3456, health: 'green' },
  { id: '8', name: 'dankmemes', subredditName: 'dankmemes', sourceType: 'reddit', group: 'Memes', tags: ['Memes', 'Humor'], isPaused: false, lastSynced: '2025-12-22T10:06:00Z', mediaCount: 12345, health: 'green' },
];

type ViewMode = 'table' | 'board';

function FeedManagerViewContent() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Subreddit[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [sources, setSources] = useState<Source[]>(MOCK_SOURCES);
  const [selectedGroup, setSelectedGroup] = useState<string>('all');
  const [sourcesFilter, setSourcesFilter] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('board');

  const { data: sourcesData, refetch: refetchSources } = useQuery(SOURCES_QUERY, {
    variables: { groupId: selectedGroup === 'all' ? undefined : selectedGroup },
    skip: isMock,
    client: apolloClient,
  });

  const { data: groupsData } = useQuery(FEED_GROUPS_QUERY, {
    skip: isMock,
    client: apolloClient,
  });

  const [searchSubreddits, { loading: searchLoading }] = useLazyQuery(SEARCH_SUBREDDITS_QUERY, {
    client: apolloClient,
    onCompleted: (data) => {
      if (data?.searchSubreddits) {
        setSearchResults(data.searchSubreddits);
        setIsSearching(false);
      }
    },
  });

  const [subscribeToSource] = useMutation(SUBSCRIBE_TO_SOURCE, {
    client: apolloClient,
    onCompleted: () => {
      refetchSources();
    },
  });

  const [togglePause] = useMutation(TOGGLE_HANDLE_PAUSE, {
    client: apolloClient,
    onCompleted: () => {
      refetchSources();
    },
  });

  const [removeHandle] = useMutation(REMOVE_HANDLE, {
    client: apolloClient,
    onCompleted: () => {
      refetchSources();
    },
  });

  useEffect(() => {
    if (!isMock && sourcesData?.getSources) {
      setSources(sourcesData.getSources);
    }
  }, [sourcesData, isMock]);

  const handleSearch = async (query: string) => {
    if (query.length < 2) {
      setSearchResults([]);
      setShowSearch(false);
      return;
    }

    setIsSearching(true);
    setShowSearch(true);

    if (isMock) {
      setTimeout(() => {
        const filtered = MOCK_SEARCH_RESULTS.filter(
          (sub) =>
            sub.name.toLowerCase().includes(query.toLowerCase()) ||
            sub.displayName.toLowerCase().includes(query.toLowerCase())
        );
        setSearchResults(filtered);
        setIsSearching(false);
      }, 300);
    } else {
      searchSubreddits({ variables: { query } });
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    handleSearch(value);
  };

  const handleSubscribe = async (subreddit: Subreddit) => {
    if (isMock) {
      console.log('Subscribe to:', subreddit.name);
      return;
    }

    try {
      await subscribeToSource({
        variables: {
          subredditName: subreddit.name,
          groupId: selectedGroup === 'all' ? undefined : selectedGroup,
        },
      });
      setShowSearch(false);
      setSearchQuery('');
    } catch (error) {
      console.error('Failed to subscribe:', error);
    }
  };

  const handleTogglePause = async (sourceId: string) => {
    if (isMock) {
      console.log('Toggle pause:', sourceId);
      return;
    }

    try {
      await togglePause({ variables: { handleId: sourceId } });
    } catch (error) {
      console.error('Failed to toggle pause:', error);
    }
  };

  const handleDelete = async (sourceId: string) => {
    if (isMock) {
      console.log('Delete source:', sourceId);
      return;
    }

    if (confirm('Are you sure you want to remove this source?')) {
      try {
        await removeHandle({ variables: { handleId: sourceId } });
      } catch (error) {
        console.error('Failed to delete source:', error);
      }
    }
  };

  const filteredSources = sources.filter((source) => {
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

  const groups = isMock
    ? Array.from(new Set(sources.map(s => s.group)))
    : (groupsData?.getFeedGroups?.map((g: any) => g.name) || []);

  const formatTimeAgo = (timestamp: string | null) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffMs / 86400000)}d ago`;
  };

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'green': return 'bg-green-500';
      case 'yellow': return 'bg-yellow-500';
      case 'red': return 'bg-red-500';
      default: return 'bg-theme-text-secondary';
    }
  };

  return (
    <div className="min-h-screen bg-theme-bg-primary text-theme-text-primary">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Feed Manager</h1>
          <p className="text-theme-text-secondary">Discover and manage your content sources</p>
        </div>

        {/* Discovery Section */}
        <div className="mb-8">
          <div className="relative mb-4">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
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
              onChange={handleInputChange}
              placeholder="Search for subreddits to add..."
              className="w-full pl-12 pr-4 py-3 bg-theme-bg-secondary border border-theme-border-primary rounded-lg text-theme-text-primary placeholder-theme-text-secondary focus:outline-none focus:ring-2 focus:ring-theme-accent-primary focus:border-transparent"
            />
            {(isSearching || searchLoading) && (
              <div className="absolute inset-y-0 right-0 pr-4 flex items-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
              </div>
            )}
          </div>

          {/* Search Results */}
          {showSearch && (
            <div className="bg-theme-bg-secondary border border-theme-border-primary rounded-lg p-4 max-h-96 overflow-y-auto">
              {searchResults.length > 0 ? (
                <div className="space-y-3">
                  {searchResults.map((subreddit) => (
                    <div
                      key={subreddit.name}
                      className="bg-theme-bg-primary border border-theme-border-primary rounded-lg p-4 hover:border-theme-accent-primary transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <div className="w-10 h-10 rounded-full bg-theme-bg-secondary flex items-center justify-center text-sm font-semibold">
                              r/
                            </div>
                            <div>
                              <h3 className="font-semibold">r/{subreddit.displayName}</h3>
                              <p className="text-sm text-theme-text-secondary">
                                {subreddit.subscriberCount.toLocaleString()} members
                              </p>
                            </div>
                          </div>
                          {subreddit.description && (
                            <p className="text-sm text-theme-text-secondary">{subreddit.description}</p>
                          )}
                        </div>
                        <div className="ml-4">
                          {subreddit.isSubscribed ? (
                            <button
                              disabled
                              className="px-4 py-2 bg-theme-bg-secondary text-theme-text-secondary rounded-lg cursor-not-allowed flex items-center space-x-2"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M5 13l4 4L19 7"
                                />
                              </svg>
                              <span>Subscribed</span>
                            </button>
                          ) : (
                            <button
                              onClick={() => handleSubscribe(subreddit)}
                              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center space-x-2"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M12 4v16m8-8H4"
                                />
                              </svg>
                              <span>Add</span>
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-theme-text-secondary">
                  <p>No results found for "{searchQuery}"</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* My Sources Section */}
        <div className="border-t border-theme-border-primary pt-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold mb-1">My Sources</h2>
              <p className="text-sm text-theme-text-secondary">
                {filteredSources.length} source{filteredSources.length !== 1 ? 's' : ''}
              </p>
            </div>
            
            {/* View Toggle and Filters */}
            <div className="flex items-center space-x-2">
              {/* View Mode Toggle */}
              <div className="flex items-center bg-theme-bg-secondary border border-theme-border-primary rounded-lg p-1">
                <button
                  onClick={() => setViewMode('table')}
                  className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                    viewMode === 'table'
                      ? 'bg-theme-accent-primary text-theme-text-primary'
                      : 'text-theme-text-secondary hover:text-theme-text-primary'
                  }`}
                >
                  <svg className="w-4 h-4 inline-block mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Table
                </button>
                <button
                  onClick={() => setViewMode('board')}
                  className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                    viewMode === 'board'
                      ? 'bg-theme-accent-primary text-theme-text-primary'
                      : 'text-theme-text-secondary hover:text-theme-text-primary'
                  }`}
                >
                  <svg className="w-4 h-4 inline-block mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                  </svg>
                  Board
                </button>
              </div>
              
              <select
                value={selectedGroup}
                onChange={(e) => setSelectedGroup(e.target.value)}
                className="px-4 py-2 bg-theme-bg-secondary border border-theme-border-primary rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-accent-primary"
              >
                <option value="all">All Groups</option>
                {groups.map((group) => (
                  <option key={group} value={group}>{group}</option>
                ))}
              </select>
              <input
                type="text"
                value={sourcesFilter}
                onChange={(e) => setSourcesFilter(e.target.value)}
                placeholder="Filter sources..."
                className="px-4 py-2 bg-theme-bg-secondary border border-theme-border-primary rounded-lg text-theme-text-primary placeholder-theme-text-secondary focus:outline-none focus:ring-2 focus:ring-theme-accent-primary w-48"
              />
            </div>
          </div>

          {/* Sources View - Board or Table */}
          {viewMode === 'board' ? (
            <SourcesBoardView
              sources={filteredSources}
              selectedGroup={selectedGroup}
              sourcesFilter={sourcesFilter}
              onTogglePause={handleTogglePause}
              onDelete={handleDelete}
            />
          ) : (
            <div className="bg-theme-bg-secondary border border-theme-border-primary rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-theme-bg-primary border-b border-theme-border-primary">
                  <tr>
                    <th className="text-left p-4 text-xs font-semibold text-theme-text-secondary uppercase tracking-wider">
                      <input type="checkbox" className="rounded border-theme-border-primary bg-theme-bg-secondary" />
                    </th>
                    <th className="text-left p-4 text-xs font-semibold text-theme-text-secondary uppercase tracking-wider">Source</th>
                    <th className="text-left p-4 text-xs font-semibold text-theme-text-secondary uppercase tracking-wider">Group</th>
                    <th className="text-left p-4 text-xs font-semibold text-theme-text-secondary uppercase tracking-wider">Health</th>
                    <th className="text-left p-4 text-xs font-semibold text-theme-text-secondary uppercase tracking-wider">Last Sync</th>
                    <th className="text-left p-4 text-xs font-semibold text-theme-text-secondary uppercase tracking-wider">Media</th>
                    <th className="text-left p-4 text-xs font-semibold text-theme-text-secondary uppercase tracking-wider">Status</th>
                    <th className="text-left p-4 text-xs font-semibold text-theme-text-secondary uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-theme-border-primary">
                  {filteredSources.length > 0 ? (
                    filteredSources.map((source) => (
                      <tr key={source.id} className="hover:bg-theme-bg-primary transition-colors">
                        <td className="p-4">
                          <input type="checkbox" className="rounded border-theme-border-primary bg-theme-bg-secondary" />
                        </td>
                        <td className="p-4">
                          <div className="flex items-center space-x-3">
                            <div className={`w-8 h-8 rounded flex items-center justify-center text-xs font-semibold ${
                              source.sourceType === 'reddit' ? 'bg-red-600' :
                              source.sourceType === 'youtube' ? 'bg-red-500' :
                              'bg-theme-bg-secondary'
                            }`}>
                              {source.sourceType === 'reddit' ? 'r/' : 
                               source.sourceType === 'youtube' ? 'YT' : 
                               source.sourceType === 'twitter' ? '@' : '?'}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <span className="font-medium">
                                  {source.sourceType === 'reddit' ? `r/${source.name}` :
                                   source.sourceType === 'youtube' ? source.youtubeHandle || source.name :
                                   source.name}
                                </span>
                                {source.entityName && (
                                  <span className="px-2 py-0.5 text-xs rounded bg-blue-900/50 text-blue-300 border border-blue-700">
                                    {source.entityName}
                                  </span>
                                )}
                              </div>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {source.tags.map((tag) => (
                                  <span
                                    key={tag}
                                    className="px-2 py-0.5 text-xs rounded bg-theme-bg-primary text-theme-text-secondary border border-theme-border-primary"
                                  >
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="p-4 text-sm text-theme-text-secondary">
                          {source.group}
                        </td>
                        <td className="p-4">
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${getHealthColor(source.health)}`} />
                            <span className="text-xs text-theme-text-secondary capitalize">{source.health}</span>
                          </div>
                        </td>
                        <td className="p-4 text-sm text-theme-text-secondary">
                          {formatTimeAgo(source.lastSynced)}
                        </td>
                        <td className="p-4 text-sm text-theme-text-secondary">
                          {source.mediaCount.toLocaleString()}
                        </td>
                        <td className="p-4">
                          <button
                            onClick={() => handleTogglePause(source.id)}
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                              source.isPaused ? 'bg-theme-bg-secondary' : 'bg-theme-accent-primary'
                            }`}
                          >
                            <span
                              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                source.isPaused ? 'translate-x-1' : 'translate-x-6'
                              }`}
                            />
                          </button>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center space-x-2">
                            <button className="p-1 text-theme-text-secondary hover:text-theme-text-primary transition-colors" title="Edit">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                            </button>
                            <button className="p-1 text-theme-text-secondary hover:text-theme-text-primary transition-colors" title="Settings">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              </svg>
                            </button>
                            <button
                              onClick={() => handleDelete(source.id)}
                              className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                              title="Delete"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="p-8 text-center text-theme-text-secondary">
                        No sources found. Use the search above to add new sources.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function FeedManagerView() {
  if (isMock) {
    return <FeedManagerViewContent />;
  }

  return (
    <ApolloProvider client={apolloClient}>
      <FeedManagerViewContent />
    </ApolloProvider>
  );
}
