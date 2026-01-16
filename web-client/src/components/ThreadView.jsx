import React from 'react';
import useSWR from 'swr';
import { useParams, Link } from 'react-router-dom';

const fetcher = (url) => fetch(url).then((res) => res.json());

const PostContent = ({ htmlContent, localImageUrl }) => {
  const sanitizedHtml = htmlContent.replace(/>&gt;/g, '>>&gt;').replace(/>&gt;&gt;/g, '>>');
  
  const createMarkup = (html) => ({ __html: html });
  
  // Custom renderer logic to handle greentext, quotes, and links
  // We use dangerouslySetInnerHTML as the backend has pre-sanitized the HTML
  const content = (
    <div
      className="post-message text-sm text-gray-300 break-words"
      dangerouslySetInnerHTML={createMarkup(sanitizedHtml)}
    />
  );
  
  return (
    <>
      {content}
      {localImageUrl && (
        <a href={localImageUrl} target="_blank" rel="noopener noreferrer" className="mt-2 block max-w-xs">
          <img 
            src={localImageUrl} 
            alt="Image" 
            className="rounded-lg shadow-lg border border-gray-600 hover:opacity-80 transition-opacity"
            style={{ maxHeight: '150px', width: 'auto' }}
          />
          <p className="file-info mt-1">Click to view full image</p>
        </a>
      )}
    </>
  );
};

const PostCard = ({ post, board }) => {
  const localImageUrl = post.local_image_url || null;
  
  // In a real application, we would check for image/video extension and render accordingly.
  // For now, we assume local_image_url is the path to the downloaded file.
  
  return (
    <div id={`p${post.post_no}`} className="bg-gray-900 p-3 rounded-lg shadow-inner border-l-4 border-teal-500 mb-4">
      <header className="flex justify-between items-center text-xs text-gray-500 mb-2">
        <span className="font-mono text-teal-400">No.{post.post_no}</span>
        <span className="ml-4">{new Date(post.created_at).toLocaleString()}</span>
      </header>
      
      {post.subject && (
        <h4 className="text-sm font-bold text-white mb-2">{post.subject}</h4>
      )}
      
      <PostContent 
        htmlContent={post.com || post.comment} 
        localImageUrl={localImageUrl}
      />
    </div>
  );
};

const ThreadView = () => {
  const { board, threadId } = useParams();
  const { data, error, isLoading } = useSWR(`/api/thread/${board}/${threadId}`, fetcher, {
    refreshInterval: 10000, // Refresh every 10 seconds to catch new posts
  });

  if (isLoading) return <p className="text-gray-400">Loading thread...</p>;
  if (error) return <p className="text-red-400">Error: {error.message}. Thread may not be archived yet.</p>;

  const op = data?.posts?.[0] || {};
  const replies = data?.posts?.slice(1) || [];

  return (
    <div className="max-w-4xl mx-auto">
      <Link to="/" className="text-teal-400 hover:text-teal-300 text-sm mb-4 block">&lt; Back to List</Link>
      <h1 className="text-2xl font-bold text-white mb-6">
        {data.title || `/${board}/${threadId}`}
      </h1>
      
      {/* OP Post */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-3 text-white border-b border-gray-700 pb-2">Original Post</h2>
        <PostCard post={op} board={board} />
      </div>
      
      {/* Replies */}
      <div>
        <h2 className="text-xl font-semibold mb-3 text-white border-b border-gray-700 pb-2">Replies ({replies.length})</h2>
        {replies.map((post) => (
          <PostCard key={post.post_no} post={post} board={board} />
        ))}
        {replies.length === 0 && <p className="text-gray-500">No replies yet. Worker is monitoring for updates...</p>}
      </div>
    </div>
  );
};

export default ThreadView;
