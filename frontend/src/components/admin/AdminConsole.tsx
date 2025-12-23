import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { ApolloProvider } from '@apollo/client';
import { apolloClient, isMock } from '../../lib/graphql/client';
import { CREATORS_QUERY } from '../../lib/graphql/queries';
import { CREATE_CREATOR, ADD_HANDLE, VERIFY_HANDLE, UPDATE_HANDLE_STATUS } from '../../lib/graphql/mutations';

interface Creator {
  id: string;
  slug: string;
  name: string;
  displayName: string;
  bio?: string;
  avatarUrl?: string;
  verified: boolean;
  handles: Handle[];
  // Enhanced metadata
  birthDate?: string;
  birthPlace?: string;
  nationality?: string;
  height?: string;
  occupation?: string[];
  employer?: string[];
  education?: string[];
  totalFollowers?: number;
  dataSources?: string[];
}

interface Handle {
  id: string;
  platform: 'reddit' | 'youtube' | 'twitter' | 'instagram' | 'tiktok' | 'vsco';
  username: string;
  handle: string;
  url: string;
  verified: boolean;
  status: 'active' | 'suspended' | 'abandoned';
  mediaCount: number;
  lastSynced: string | null;
  health: 'green' | 'yellow' | 'red';
}

// Mock data with enriched metadata
const MOCK_CREATORS: Creator[] = [
  {
    id: 'sjokz',
    slug: 'sjokz',
    name: 'Eefje Depoortere',
    displayName: 'Sjokz',
    bio: 'Belgian television presenter, reporter, and esports player who has hosted the League of Legends European Championship',
    verified: true,
    birthDate: '1987-06-16',
    birthPlace: 'Bruges, Belgium',
    nationality: 'Belgian',
    height: '1.73 m (5\'8")',
    occupation: ['Television presenter', 'Reporter', 'Esports player'],
    employer: ['Riot Games', 'Electronic Sports League'],
    education: ['Ghent University'],
    totalFollowers: 1324700,
    dataSources: ['wikipedia', 'instagram', 'youtube'],
    handles: [
      {
        id: 'sjokz-reddit',
        platform: 'reddit',
        username: 'Sjokz',
        handle: 'r/Sjokz',
        url: 'https://reddit.com/r/Sjokz',
        verified: true,
        status: 'active',
        mediaCount: 1247,
        lastSynced: '2025-12-22T10:15:00Z',
        health: 'green',
      },
      {
        id: 'sjokz-youtube',
        platform: 'youtube',
        username: 'sjokz',
        handle: '@sjokz',
        url: 'https://youtube.com/@sjokz',
        verified: true,
        status: 'active',
        mediaCount: 3421,
        lastSynced: '2025-12-22T10:14:00Z',
        health: 'green',
      },
    ],
  },
  {
    id: 'brooke-monk',
    slug: 'brooke-monk',
    name: 'Brooke Monk',
    displayName: 'Brooke Monk',
    bio: 'Digital media creator who makes entertaining videos on beauty, fashion, lifestyle, and comedy',
    verified: true,
    birthDate: '2003-01-31',
    birthPlace: 'United States',
    nationality: 'American',
    height: '1.65 m (5\'5")',
    occupation: ['Content creator', 'Influencer', 'TikToker'],
    totalFollowers: 61700000,
    dataSources: ['wikipedia', 'instagram', 'youtube', 'tiktok'],
    handles: [
      {
        id: 'brooke-reddit-1',
        platform: 'reddit',
        username: 'BrookeMonkTheSecond',
        handle: 'r/BrookeMonkTheSecond',
        url: 'https://reddit.com/r/BrookeMonkTheSecond',
        verified: true,
        status: 'active',
        mediaCount: 8934,
        lastSynced: '2025-12-22T10:16:00Z',
        health: 'green',
      },
      {
        id: 'brooke-reddit-2',
        platform: 'reddit',
        username: 'BestOfBrookeMonk',
        handle: 'r/BestOfBrookeMonk',
        url: 'https://reddit.com/r/BestOfBrookeMonk',
        verified: true,
        status: 'active',
        mediaCount: 5678,
        lastSynced: '2025-12-22T10:10:00Z',
        health: 'green',
      },
      {
        id: 'brooke-reddit-3',
        platform: 'reddit',
        username: 'BrookeMonkNSFWHub',
        handle: 'r/BrookeMonkNSFWHub',
        url: 'https://reddit.com/r/BrookeMonkNSFWHub',
        verified: false,
        status: 'active',
        mediaCount: 318,
        lastSynced: '2025-12-22T10:19:00Z',
        health: 'green',
      },
      {
        id: 'brooke-youtube',
        platform: 'youtube',
        username: 'BrookeMonk',
        handle: '@BrookeMonk',
        url: 'https://youtube.com/c/BrookeMonk',
        verified: true,
        status: 'active',
        mediaCount: 12567,
        lastSynced: '2025-12-22T10:15:00Z',
        health: 'green',
      },
    ],
  },
  {
    id: 'ovilee',
    slug: 'ovilee',
    name: 'Ovilee May',
    displayName: 'Ovilee',
    bio: 'Esports host, content creator, and gaming personality',
    verified: true,
    birthDate: '1993-06-16',
    birthPlace: 'United States',
    nationality: 'American',
    occupation: ['Esports host', 'Content creator', 'Gaming personality'],
    totalFollowers: 850000,
    dataSources: ['instagram', 'youtube', 'twitter'],
    handles: [
      {
        id: 'ovilee-reddit',
        platform: 'reddit',
        username: 'OvileeWorship',
        handle: 'r/OvileeWorship',
        url: 'https://reddit.com/r/OvileeWorship',
        verified: true,
        status: 'active',
        mediaCount: 51,
        lastSynced: '2025-12-22T10:17:00Z',
        health: 'green',
      },
    ],
  },
  {
    id: 'howdy',
    slug: 'howdy',
    name: 'Howdy',
    displayName: 'Howdy',
    bio: 'Content creator and personality',
    verified: false,
    occupation: ['Content creator', 'Influencer'],
    totalFollowers: 500000,
    dataSources: ['reddit'],
    handles: [
      {
        id: 'howdy-reddit',
        platform: 'reddit',
        username: 'howdyhowdyyallhot',
        handle: 'r/howdyhowdyyallhot',
        url: 'https://reddit.com/r/howdyhowdyyallhot',
        verified: false,
        status: 'active',
        mediaCount: 220,
        lastSynced: '2025-12-22T10:20:00Z',
        health: 'green',
      },
    ],
  },
];

const PLATFORM_COLORS: Record<string, string> = {
  reddit: 'bg-orange-600',
  youtube: 'bg-red-600',
  twitter: 'bg-blue-500',
  instagram: 'bg-pink-600',
  tiktok: 'bg-black',
  vsco: 'bg-gray-800',
};

function AdminConsoleContent() {
  const [creators, setCreators] = useState<Creator[]>(MOCK_CREATORS);
  const [selectedCreator, setSelectedCreator] = useState<Creator | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddCreator, setShowAddCreator] = useState(false);
  const [showDiscovery, setShowDiscovery] = useState(false);
  const [discoveryUrl, setDiscoveryUrl] = useState('');
  const [newCreatorName, setNewCreatorName] = useState('');
  const [newCreatorDisplayName, setNewCreatorDisplayName] = useState('');
  const [newCreatorBio, setNewCreatorBio] = useState('');

  const { data: creatorsData, refetch: refetchCreators } = useQuery(CREATORS_QUERY, {
    variables: { query: searchQuery || undefined },
    skip: isMock,
    client: apolloClient,
  });

  const [createCreator] = useMutation(CREATE_CREATOR, {
    client: apolloClient,
    onCompleted: () => {
      refetchCreators();
      setShowAddCreator(false);
      setNewCreatorName('');
      setNewCreatorDisplayName('');
      setNewCreatorBio('');
    },
  });

  const [addHandle] = useMutation(ADD_HANDLE, {
    client: apolloClient,
    onCompleted: () => {
      refetchCreators();
    },
  });

  const [verifyHandle] = useMutation(VERIFY_HANDLE, {
    client: apolloClient,
    onCompleted: () => {
      refetchCreators();
    },
  });

  const [updateHandleStatus] = useMutation(UPDATE_HANDLE_STATUS, {
    client: apolloClient,
    onCompleted: () => {
      refetchCreators();
    },
  });

  useEffect(() => {
    if (!isMock && creatorsData?.creators) {
      setCreators(creatorsData.creators);
    }
  }, [creatorsData, isMock]);

  const filteredCreators = creators.filter((creator) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      creator.name.toLowerCase().includes(query) ||
      creator.displayName.toLowerCase().includes(query) ||
      creator.slug.toLowerCase().includes(query)
    );
  });

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

  const handleDiscoverHandles = () => {
    // TODO: Implement bio-crawler discovery
    console.log('Discovering handles from:', discoveryUrl);
    setShowDiscovery(false);
    setDiscoveryUrl('');
  };

  const handleCreateCreator = async () => {
    if (isMock) {
      console.log('Create creator:', newCreatorName, newCreatorDisplayName);
      setShowAddCreator(false);
      return;
    }

    try {
      await createCreator({
        variables: {
          name: newCreatorName,
          displayName: newCreatorDisplayName,
        },
      });
    } catch (error) {
      console.error('Failed to create creator:', error);
    }
  };

  const handleVerifyHandle = async (creatorId: string, handleId: string) => {
    if (isMock) {
      setCreators((prev) =>
        prev.map((creator) => {
          if (creator.id === creatorId) {
            return {
              ...creator,
              handles: creator.handles.map((h) =>
                h.id === handleId ? { ...h, verified: true } : h
              ),
            };
          }
          return creator;
        })
      );
      return;
    }

    try {
      await verifyHandle({ variables: { handleId } });
    } catch (error) {
      console.error('Failed to verify handle:', error);
    }
  };

  const handleUpdateHandleStatus = async (
    creatorId: string,
    handleId: string,
    status: 'active' | 'suspended' | 'abandoned'
  ) => {
    if (isMock) {
      setCreators((prev) =>
        prev.map((creator) => {
          if (creator.id === creatorId) {
            return {
              ...creator,
              handles: creator.handles.map((h) =>
                h.id === handleId ? { ...h, status } : h
              ),
            };
          }
          return creator;
        })
      );
      return;
    }

    try {
      await updateHandleStatus({
        variables: {
          handleId,
          status: status.toUpperCase(),
        },
      });
    } catch (error) {
      console.error('Failed to update handle status:', error);
    }
  };

  return (
    <div className="min-h-screen bg-theme-bg-primary text-theme-text-primary">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold mb-2">Admin Console</h1>
              <p className="text-theme-text-secondary">Manage creators, handles, and platform connections</p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowDiscovery(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span>Discover Handles</span>
              </button>
              <button
                onClick={() => setShowAddCreator(true)}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Add Creator</span>
              </button>
            </div>
          </div>

          {/* Search */}
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search creators..."
            className="w-full px-4 py-2 bg-theme-bg-secondary border border-theme-border-primary rounded-lg text-theme-text-primary placeholder-theme-text-secondary focus:outline-none focus:ring-2 focus:ring-theme-accent-primary"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Creators List */}
          <div className="lg:col-span-1">
            <div className="bg-theme-bg-secondary border border-theme-border-primary rounded-lg">
              <div className="p-4 border-b border-theme-border-primary">
                <h2 className="font-semibold">Creators ({filteredCreators.length})</h2>
              </div>
              <div className="divide-y divide-theme-border-primary max-h-[calc(100vh-300px)] overflow-y-auto">
                {filteredCreators.map((creator) => (
                  <button
                    key={creator.id}
                    onClick={() => setSelectedCreator(creator)}
                    className={`w-full text-left p-4 hover:bg-theme-bg-primary transition-colors ${
                      selectedCreator?.id === creator.id ? 'bg-theme-bg-primary' : ''
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      {creator.avatarUrl ? (
                        <img
                          src={creator.avatarUrl}
                          alt={creator.displayName}
                          className="w-10 h-10 rounded-full"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-theme-bg-secondary flex items-center justify-center text-sm font-semibold">
                          {creator.displayName[0]}
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{creator.displayName}</div>
                        <div className="text-sm text-theme-text-secondary truncate">{creator.name}</div>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className="text-xs text-theme-text-secondary">
                            {creator.handles.length} handle{creator.handles.length !== 1 ? 's' : ''}
                          </span>
                          {creator.verified && (
                            <span className="text-xs bg-blue-900 text-blue-300 px-1.5 py-0.5 rounded">
                              Verified
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Creator Details */}
          <div className="lg:col-span-2">
            {selectedCreator ? (
              <div className="space-y-6">
                {/* Creator Info */}
                <div className="bg-theme-bg-secondary border border-theme-border-primary rounded-lg p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-4">
                      {selectedCreator.avatarUrl ? (
                        <img
                          src={selectedCreator.avatarUrl}
                          alt={selectedCreator.displayName}
                          className="w-16 h-16 rounded-full"
                        />
                      ) : (
                        <div className="w-16 h-16 rounded-full bg-theme-bg-secondary flex items-center justify-center text-xl font-semibold">
                          {selectedCreator.displayName[0]}
                        </div>
                      )}
                      <div>
                        <h2 className="text-2xl font-bold">{selectedCreator.displayName}</h2>
                        <p className="text-theme-text-secondary">{selectedCreator.name}</p>
                        <p className="text-sm text-theme-text-secondary mt-1">/{selectedCreator.slug}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {selectedCreator.verified && (
                        <span className="px-3 py-1 bg-blue-900 text-blue-300 rounded text-sm">
                          Verified
                        </span>
                      )}
                      <button className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded text-sm transition-colors">
                        Edit
                      </button>
                    </div>
                  </div>
                  {selectedCreator.bio && (
                    <p className="text-theme-text-primary mb-4">{selectedCreator.bio}</p>
                  )}
                  
                  {/* Enhanced Metadata */}
                  <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-theme-border-primary">
                    {selectedCreator.birthDate && (
                      <div>
                        <span className="text-xs text-theme-text-secondary">Birth Date</span>
                        <p className="text-sm text-theme-text-primary">{new Date(selectedCreator.birthDate).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
                      </div>
                    )}
                    {selectedCreator.birthPlace && (
                      <div>
                        <span className="text-xs text-theme-text-secondary">Birth Place</span>
                        <p className="text-sm text-theme-text-primary">{selectedCreator.birthPlace}</p>
                      </div>
                    )}
                    {selectedCreator.nationality && (
                      <div>
                        <span className="text-xs text-theme-text-secondary">Nationality</span>
                        <p className="text-sm text-theme-text-primary">{selectedCreator.nationality}</p>
                      </div>
                    )}
                    {selectedCreator.height && (
                      <div>
                        <span className="text-xs text-theme-text-secondary">Height</span>
                        <p className="text-sm text-theme-text-primary">{selectedCreator.height}</p>
                      </div>
                    )}
                    {selectedCreator.totalFollowers && (
                      <div>
                        <span className="text-xs text-theme-text-secondary">Total Followers</span>
                        <p className="text-sm text-theme-text-primary">{selectedCreator.totalFollowers.toLocaleString()}</p>
                      </div>
                    )}
                    {selectedCreator.dataSources && selectedCreator.dataSources.length > 0 && (
                      <div>
                        <span className="text-xs text-theme-text-secondary">Data Sources</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {selectedCreator.dataSources.map((source) => (
                            <span key={source} className="px-2 py-0.5 bg-theme-bg-primary text-theme-text-secondary rounded text-xs">
                              {source}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Career Info */}
                  {(selectedCreator.occupation || selectedCreator.employer || selectedCreator.education) && (
                    <div className="mt-4 pt-4 border-t border-theme-border-primary space-y-3">
                      {selectedCreator.occupation && selectedCreator.occupation.length > 0 && (
                        <div>
                          <span className="text-xs text-theme-text-secondary">Occupation</span>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {selectedCreator.occupation.map((occ, idx) => (
                              <span key={idx} className="px-2 py-1 bg-blue-900/30 text-blue-300 rounded text-xs">
                                {occ}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {selectedCreator.employer && selectedCreator.employer.length > 0 && (
                        <div>
                          <span className="text-xs text-theme-text-secondary">Employer</span>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {selectedCreator.employer.map((emp, idx) => (
                              <span key={idx} className="px-2 py-1 bg-green-900/30 text-green-300 rounded text-xs">
                                {emp}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {selectedCreator.education && selectedCreator.education.length > 0 && (
                        <div>
                          <span className="text-xs text-theme-text-secondary">Education</span>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {selectedCreator.education.map((edu, idx) => (
                              <span key={idx} className="px-2 py-1 bg-purple-900/30 text-purple-300 rounded text-xs">
                                {edu}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Handles */}
                <div className="bg-theme-bg-secondary border border-theme-border-primary rounded-lg">
                  <div className="p-4 border-b border-theme-border-primary flex items-center justify-between">
                    <h3 className="font-semibold">Handles ({selectedCreator.handles.length})</h3>
                    <button className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors">
                      Add Handle
                    </button>
                  </div>
                  <div className="divide-y divide-gray-800">
                    {selectedCreator.handles.map((handle) => (
                      <div key={handle.id} className="p-4 hover:bg-theme-bg-primary transition-colors">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-4 flex-1">
                            <div
                              className={`w-10 h-10 rounded flex items-center justify-center text-white font-semibold ${PLATFORM_COLORS[handle.platform] || 'bg-gray-700'}`}
                            >
                              {handle.platform[0].toUpperCase()}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-1">
                                <span className="font-medium">{handle.handle}</span>
                                {handle.verified ? (
                                  <span className="px-2 py-0.5 bg-green-900 text-green-300 rounded text-xs">
                                    Verified
                                  </span>
                                ) : (
                                  <span className="px-2 py-0.5 bg-yellow-900 text-yellow-300 rounded text-xs">
                                    Unverified
                                  </span>
                                )}
                                <span
                                  className={`px-2 py-0.5 rounded text-xs ${
                                    handle.status === 'active'
                                      ? 'bg-green-900 text-green-300'
                                      : handle.status === 'suspended'
                                      ? 'bg-red-900 text-red-300'
                                      : 'bg-theme-bg-secondary text-theme-text-secondary'
                                  }`}
                                >
                                  {handle.status}
                                </span>
                              </div>
                              <a
                                href={handle.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-blue-400 hover:text-blue-300"
                              >
                                {handle.url}
                              </a>
                              <div className="flex items-center space-x-4 mt-2 text-sm text-theme-text-secondary">
                                <span>{handle.mediaCount.toLocaleString()} items</span>
                                <span>Last sync: {formatTimeAgo(handle.lastSynced)}</span>
                                <div className="flex items-center space-x-1">
                                  <div className={`w-2 h-2 rounded-full ${getHealthColor(handle.health)}`} />
                                  <span className="capitalize">{handle.health}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            {!handle.verified && (
                              <button
                                onClick={() => handleVerifyHandle(selectedCreator.id, handle.id)}
                                className="p-2 text-green-400 hover:bg-green-900/20 rounded transition-colors"
                                title="Verify Handle"
                              >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                              </button>
                            )}
                            <select
                              value={handle.status}
                              onChange={(e) =>
                                handleUpdateHandleStatus(
                                  selectedCreator.id,
                                  handle.id,
                                  e.target.value as 'active' | 'suspended' | 'abandoned'
                                )
                              }
                              className="px-2 py-1 bg-theme-bg-primary border border-theme-border-primary rounded text-sm focus:outline-none focus:ring-2 focus:ring-theme-accent-primary"
                            >
                              <option value="active">Active</option>
                              <option value="suspended">Suspended</option>
                              <option value="abandoned">Abandoned</option>
                            </select>
                            <button className="p-2 text-theme-text-secondary hover:text-theme-text-primary hover:bg-theme-bg-primary rounded transition-colors">
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-theme-bg-secondary border border-theme-border-primary rounded-lg p-12 text-center">
                <svg
                  className="w-16 h-16 text-theme-text-secondary mx-auto mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <p className="text-theme-text-secondary">Select a creator to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Discovery Modal */}
      {showDiscovery && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold">Discover Handles</h3>
              <button
                onClick={() => setShowDiscovery(false)}
                className="text-theme-text-secondary hover:text-theme-text-primary"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <p className="text-theme-text-secondary mb-4 text-sm">
              Enter a URL (e.g., YouTube About page) to automatically discover linked social media accounts.
            </p>
            <input
              type="url"
              value={discoveryUrl}
              onChange={(e) => setDiscoveryUrl(e.target.value)}
              placeholder="https://youtube.com/@sjokz/about"
              className="w-full px-4 py-2 bg-theme-bg-primary border border-theme-border-primary rounded-lg text-theme-text-primary placeholder-theme-text-secondary focus:outline-none focus:ring-2 focus:ring-theme-accent-primary mb-4"
            />
            <div className="flex items-center space-x-3">
              <button
                onClick={handleDiscoverHandles}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                Discover
              </button>
              <button
                onClick={() => setShowDiscovery(false)}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Creator Modal */}
      {showAddCreator && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold">Add Creator</h3>
              <button
                onClick={() => setShowAddCreator(false)}
                className="text-theme-text-secondary hover:text-theme-text-primary"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Display Name</label>
                <input
                  type="text"
                  value={newCreatorDisplayName}
                  onChange={(e) => setNewCreatorDisplayName(e.target.value)}
                  className="w-full px-4 py-2 bg-theme-bg-primary border border-theme-border-primary rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-accent-primary"
                  placeholder="Sjokz"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Real Name</label>
                <input
                  type="text"
                  value={newCreatorName}
                  onChange={(e) => setNewCreatorName(e.target.value)}
                  className="w-full px-4 py-2 bg-theme-bg-primary border border-theme-border-primary rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-accent-primary"
                  placeholder="Eefje Depoortere"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Bio</label>
                <textarea
                  value={newCreatorBio}
                  onChange={(e) => setNewCreatorBio(e.target.value)}
                  className="w-full px-4 py-2 bg-theme-bg-primary border border-theme-border-primary rounded-lg text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-accent-primary"
                  rows={3}
                  placeholder="Esports host and personality"
                />
              </div>
            </div>
            <div className="flex items-center space-x-3 mt-6">
              <button
                onClick={handleCreateCreator}
                className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                Create
              </button>
              <button
                onClick={() => setShowAddCreator(false)}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AdminConsole() {
  if (isMock) {
    return <AdminConsoleContent />;
  }

  return (
    <ApolloProvider client={apolloClient}>
      <AdminConsoleContent />
    </ApolloProvider>
  );
}

