import { useState, useEffect, useMemo } from 'react';
import { ApolloProvider } from '@apollo/client';
import { apolloClient, isMock } from '../../lib/graphql/client';
import { loadAllMedia, SUBREDDITS, type TransformedMedia } from '../../lib/mock-data/loader';
import { deduplicateMedia, extractImageIdentifier, type Media } from '../../lib/utils/deduplicate';
import { getBoardConfig, isPostVisible, type BoardConfig } from '../../lib/feed-config/board-config';
import MediaLightbox from './MediaLightbox';
import FeedBoardSidebar from './FeedBoardSidebar';

const PLATFORM_COLORS: Record<string, string> = {
  reddit: 'bg-orange-600',
  youtube: 'bg-red-600',
  twitter: 'bg-blue-500',
  instagram: 'bg-pink-600',
  tiktok: 'bg-black',
  vsco: 'bg-gray-800',
};

function FeedViewContent() {
  const [posts, setPosts] = useState<Media[]>([]);
  const [selectedMedia, setSelectedMedia] = useState<Media | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const [loading, setLoading] = useState(true);
  const [boardConfig, setBoardConfig] = useState<BoardConfig>(() => {
    console.log('[FeedView] Initializing boardConfig...');
    if (typeof window === 'undefined') {
      return {
        id: 'default',
        name: 'Default Feed',
        enabledSources: new Set(),
        blockedEntities: new Map(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
    }
    return getBoardConfig();
  });

  // Load mock data on mount
  useEffect(() => {
    let cancelled = false;
    
    async function loadData() {
      setLoading(true);
      try {
        const allMedia = await loadAllMedia();
        if (cancelled) return;
        
        const mappedPosts: Media[] = allMedia.map((item) => ({
          id: item.id,
          title: item.title,
          imageUrl: item.imageUrl,
          sourceUrl: item.sourceUrl,
          publishDate: item.publishDate,
          score: item.score,
          subreddit: item.subreddit,
          author: item.author,
          platform: item.platform,
          handle: item.handle,
          mediaType: item.mediaType as 'video' | 'image' | 'text',
        }));
        
        const deduplicatedPosts = deduplicateMedia(mappedPosts);
        if (!cancelled) {
          setPosts(deduplicatedPosts);
        }
      } catch (error) {
        console.error('[FeedView] Failed to load data:', error);
        if (!cancelled) {
          setPosts([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    
    loadData();
    return () => { cancelled = true; };
  }, []);


  const handleMediaClick = (media: Media, index: number) => {
    setSelectedMedia(media);
    setSelectedIndex(index);
  };

  const handleNext = () => {
    if (selectedIndex < uniquePosts.length - 1) {
      const nextIndex = selectedIndex + 1;
      setSelectedMedia(uniquePosts[nextIndex]);
      setSelectedIndex(nextIndex);
    }
  };

  const handlePrevious = () => {
    if (selectedIndex > 0) {
      const prevIndex = selectedIndex - 1;
      setSelectedMedia(uniquePosts[prevIndex]);
      setSelectedIndex(prevIndex);
    }
  };

  const handleClose = () => {
    setSelectedMedia(null);
    setSelectedIndex(-1);
  };

  // Extract available sources and entities from posts for sidebar
  // Use SUBREDDITS list to ensure all available sources appear, even if they don't have posts loaded yet
  const { availableSources, availableEntities } = useMemo(() => {
    const sources = new Set<string>();
    const entitiesMap = new Map<string, Set<string>>(); // entityName -> Set<sourceNames>
    
    // Start with all available subreddits from the SUBREDDITS array
    if (isMock) {
      SUBREDDITS.forEach(subreddit => {
        sources.add(subreddit);
      });
    }
    
    // Also add sources from loaded posts (for non-mock mode or to discover entities)
    posts.forEach(post => {
      const sourceName = post.subreddit?.name || post.handle?.name;
      if (sourceName) {
        sources.add(sourceName);
        
        const creatorName = post.handle?.creatorName;
        if (creatorName) {
          if (!entitiesMap.has(creatorName)) {
            entitiesMap.set(creatorName, new Set());
          }
          entitiesMap.get(creatorName)!.add(sourceName);
        }
      }
    });
    
    // Add entity mappings for known entities (ensure all sources are linked to their creators)
    if (isMock) {
      // Brooke Monk entity
      const brookeMonkSources = ['BrookeMonkTheSecond', 'BestOfBrookeMonk', 'BrookeMonkNSFWHub'];
      const hasBrookeMonkSources = brookeMonkSources.some(src => sources.has(src));
      if (hasBrookeMonkSources) {
        if (!entitiesMap.has('Brooke Monk')) {
          entitiesMap.set('Brooke Monk', new Set());
        }
        brookeMonkSources.forEach(src => {
          if (sources.has(src)) {
            entitiesMap.get('Brooke Monk')!.add(src);
          }
        });
      }
      
      // Sjokz entity
      if (sources.has('Sjokz')) {
        if (!entitiesMap.has('Sjokz')) {
          entitiesMap.set('Sjokz', new Set());
        }
        entitiesMap.get('Sjokz')!.add('Sjokz');
      }
      
      // Ovilee entity
      if (sources.has('OvileeWorship')) {
        if (!entitiesMap.has('Ovilee')) {
          entitiesMap.set('Ovilee', new Set());
        }
        entitiesMap.get('Ovilee')!.add('OvileeWorship');
      }
      
      // Howdy entity
      if (sources.has('howdyhowdyyallhot')) {
        if (!entitiesMap.has('Howdy')) {
          entitiesMap.set('Howdy', new Set());
        }
        entitiesMap.get('Howdy')!.add('howdyhowdyyallhot');
      }
    }
    
    const entities = Array.from(entitiesMap.entries()).map(([name, sourceSet]) => ({
      id: name.toLowerCase(),
      name: name,
      sources: Array.from(sourceSet),
    }));
    
    return {
      availableSources: Array.from(sources).sort(),
      availableEntities: entities,
    };
  }, [posts, isMock]);

  // Final deduplication and filtering pass before rendering
  // Uses board configuration to filter by sources and blocked entities
  const uniquePosts = useMemo(() => {
    const seenIdentifiers = new Map<string, Media>();
    const validPosts: Media[] = [];
    
    posts.forEach((post) => {
      // Skip invalid posts (missing required fields)
      if (!post.imageUrl || !post.id || !post.title) {
        return;
      }
      
      // Apply board configuration filtering
      if (!isPostVisible(post, boardConfig)) {
        return; // Skip this post based on board config
      }
      
      // Extract image identifier (filename) to catch URL variations
      const imageId = extractImageIdentifier(post.imageUrl);
      
      if (!seenIdentifiers.has(imageId)) {
        seenIdentifiers.set(imageId, post);
        validPosts.push(post);
      }
    });
    
    return validPosts;
  }, [posts, boardConfig]);

  if (loading) {
    return (
      <div className="bg-theme-bg-primary min-h-screen py-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-theme-accent-primary"></div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-theme-bg-primary min-h-screen flex">
        <div className="sticky top-14 h-[calc(100vh-3.5rem)]">
          <FeedBoardSidebar
            onConfigChange={setBoardConfig}
            availableSources={availableSources}
            availableEntities={availableEntities}
          />
        </div>
        <div className="flex-1 py-6">
          {uniquePosts.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <p className="text-theme-text-secondary">
                {boardConfig.enabledSources.size === 0 
                  ? 'No sources enabled. Enable sources in the sidebar to see posts.' 
                  : 'No posts available'}
              </p>
            </div>
          ) : (
            <div className="columns-1 sm:columns-2 md:columns-3 lg:columns-4 xl:columns-5 gap-4 px-4">
              {uniquePosts.map((post, index) => (
                <div
                  key={`${post.imageUrl}-${post.id}`}
                  onClick={() => handleMediaClick(post, index)}
                  className="group mb-4 break-inside-avoid bg-theme-bg-secondary rounded-lg overflow-hidden cursor-pointer hover:bg-theme-bg-primary transition-all duration-200 hover:scale-[1.02]"
                >
                  <div className="relative">
                    <img
                      src={post.imageUrl}
                      alt={post.title}
                      loading="lazy"
                      className="w-full h-auto object-cover"
                    />
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors duration-200" />
                    <div className="absolute top-2 right-2">
                      <span className={`px-2 py-1 rounded text-xs font-semibold text-white ${PLATFORM_COLORS[post.platform] || 'bg-gray-700'}`}>
                        {post.platform === 'reddit' ? 'r/' : post.platform === 'youtube' ? 'YT' : post.platform === 'vsco' ? 'VS' : post.platform[0].toUpperCase()}
                      </span>
                    </div>
                    <div className="absolute bottom-0 left-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                      <div className="text-white">
                        <h3 className="font-semibold text-sm mb-2 line-clamp-2">{post.title}</h3>
                        <div className="flex items-center gap-3 text-xs text-gray-300">
                          <span className="font-medium">{post.handle.handle}</span>
                          {post.score !== undefined && (
                            <span className="flex items-center gap-1">
                              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M3.293 9.707a1 1 0 010-1.414l6-6a1 1 0 011.414 0l6 6a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L4.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                              </svg>
                              {post.score}
                            </span>
                          )}
                          {post.viewCount !== undefined && (
                            <span className="text-gray-400">{post.viewCount.toLocaleString()} views</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <MediaLightbox
        media={selectedMedia}
        isOpen={selectedMedia !== null}
        onClose={handleClose}
        onNext={handleNext}
        onPrevious={handlePrevious}
        hasNext={selectedIndex < uniquePosts.length - 1}
        hasPrevious={selectedIndex > 0}
      />
    </>
  );
}

export default function FeedView() {
  return (
    <ApolloProvider client={apolloClient}>
      <FeedViewContent />
    </ApolloProvider>
  );
}
