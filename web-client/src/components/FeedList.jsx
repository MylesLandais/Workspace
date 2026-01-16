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
    <div className="bg-gray-800 p-4 rounded-lg shadow-md hover:bg-gray-700 transition-colors border border-gray-700 flex flex-col h-full">
        <h4 className="text-md font-medium text-white mb-2 line-clamp-2">
            <a href={post.url} target="_blank" rel="noopener noreferrer" className="hover:text-teal-400">
                {post.title}
            </a>
        </h4>
        {post.is_image && post.image_url ? (
            <div className="mb-3 flex-grow">
                 <img src={post.image_url} alt={post.title} className="w-full h-48 object-cover rounded-md bg-gray-900" loading="lazy" />
            </div>
        ) : (
             <div className="mb-3 flex-grow flex items-center justify-center bg-gray-900 rounded-md h-48 text-gray-600">
                <span className="text-sm">No Image</span>
             </div>
        )}
        <div className="mt-auto">
            <div className="flex justify-between text-xs text-gray-400 mb-2">
                <span className="truncate max-w-[50%]">u/{post.author}</span>
                <span>{date}</span>
            </div>
            <div className="flex gap-4 text-sm text-gray-300 border-t border-gray-700 pt-2">
                <span title="Score">⬆️ {post.score}</span>
                <span title="Comments">💬 {post.num_comments}</span>
            </div>
        </div>
    </div>
  );
};

const FeedList = () => {
  const { data, error, isLoading } = useSWR(FEED_QUERY, fetcher);

  if (error) return (
    <div className="text-red-400 p-4 bg-gray-800 rounded-lg">
      <p className="font-bold">Failed to load feed</p>
      <p>{error.message || 'Unknown error'}</p>
      <p className="text-sm mt-2 text-red-300">
        Is the GraphQL server running? (Checked: {GRAPHQL_API})
      </p>
    </div>
  );
  if (isLoading) return <div className="text-gray-400 p-4">Loading feed...</div>;
  if (!data || !data.feedList) return <div className="text-gray-400 p-4">No data available</div>;

  return (
    <div className="space-y-8 pb-8">
      {data.feedList.map((group) => (
        <div key={group.subreddit} className="space-y-4">
          <div className="flex items-center gap-2 border-b border-gray-700 pb-2">
             <h2 className="text-2xl font-bold text-teal-400">r/{group.subreddit}</h2>
             <span className="bg-gray-700 text-gray-300 text-xs px-2 py-1 rounded-full">{group.total_count} posts</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {group.posts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default FeedList;
