import React from 'react';
import useSWR from 'swr';

const GRAPHQL_API = import.meta.env.VITE_GRAPHQL_API || 'http://jupyter.dev.local:8001/graphql';

const fetcher = (query) =>
  fetch(GRAPHQL_API, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  })
    .then((res) => res.json())
    .then((json) => json.data);

const FEED_QUERY = `
  query {
    feedList {
      subreddit
      total_count
      posts {
        id
        title
        score
        num_comments
        url
        image_url
        is_image
        author
        created_utc
      }
    }
  }
`;

const PostCard = ({ post }) => {
  const date = new Date(Number(post.created_utc) * 1000).toLocaleString();
  return (
    <div className="p-3 bg-gray-800 rounded-md mb-2 shadow-sm border border-gray-700">
        <h5 className="text-sm font-medium text-white line-clamp-2 mb-1">
            <a href={post.url} target="_blank" rel="noopener noreferrer" className="hover:text-teal-400">
                {post.title}
            </a>
        </h5>
        <div className="flex justify-between text-xs text-gray-500">
            <span>u/{post.author || 'N/A'}</span>
            <span>👍 {post.score} 💬 {post.num_comments}</span>
        </div>
    </div>
  );
};

const RedditFeedWidget = () => {
  const { data, error, isLoading } = useSWR(FEED_QUERY, fetcher, { refreshInterval: 60000 });

  if (error) return (
    <div className="text-red-400 p-2 bg-gray-900 rounded-lg">
      <p className="font-bold">Failed to load feed</p>
      <p className="text-sm mt-1 text-red-300">
        Check GraphQL server at {GRAPHQL_API}
      </p>
    </div>
  );
  if (isLoading) return <div className="text-gray-400 p-2">Loading Reddit Feed...</div>;
  if (!data || !data.feedList) return <div className="text-gray-400 p-2">No feed data available.</div>;

  const feeds = data.feedList.filter(f => f.posts.length > 0);

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-teal-400 border-b border-gray-700 pb-2">Reddit Feed</h3>
      {feeds.map((group) => (
        <div key={group.subreddit}>
          <h4 className="text-md font-semibold text-white mb-2">r/{group.subreddit}</h4>
          <div className="space-y-2">
            {group.posts.slice(0, 5).map((post) => ( // Limit to 5 posts per subreddit in the widget
              <PostCard key={post.id} post={post} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default RedditFeedWidget;
