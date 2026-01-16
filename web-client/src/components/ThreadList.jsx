import React, { useState } from 'react';
import useSWR, { mutate } from 'swr';
import { Link } from 'react-router-dom';

const fetcher = (url) => fetch(url).then((res) => res.json());

const TrackForm = () => {
  const [board, setBoard] = useState('g');
  const [threadId, setThreadId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ board, thread_id: parseInt(threadId), subject: `Tracking /${board}/${threadId}` }),
      });
      if (!response.ok) {
        throw new Error('Failed to queue tracking job.');
      }
      mutate('/api/threads'); // Refresh the thread list
      setThreadId('');
      alert('Thread queued for tracking!');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-gray-800 p-4 rounded-lg shadow-md mb-8">
      <h2 className="text-xl font-semibold mb-3 text-white">Track New Thread</h2>
      <div className="flex space-x-2">
        <input
          type="text"
          placeholder="Board (e.g., g)"
          value={board}
          onChange={(e) => setBoard(e.target.value)}
          className="p-2 border border-gray-600 rounded bg-gray-700 text-white w-20"
          required
        />
        <input
          type="number"
          placeholder="Thread ID (e.g., 943980267)"
          value={threadId}
          onChange={(e) => setThreadId(e.target.value)}
          className="flex-grow p-2 border border-gray-600 rounded bg-gray-700 text-white"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className={`p-2 rounded font-semibold transition-colors ${loading ? 'bg-teal-700 cursor-not-allowed' : 'bg-teal-500 hover:bg-teal-600'}`}
        >
          {loading ? 'Queueing...' : 'Track'}
        </button>
      </div>
      {error && <p className="text-red-400 mt-2 text-sm">{error}</p>}
    </form>
  );
};

const ThreadCard = ({ thread }) => {
  const date = new Date(thread.last_modified * 1000).toLocaleString();
  return (
    <Link to={`/thread/${thread.board}/${thread.thread_id}`} className="block bg-gray-800 p-4 rounded-lg hover:bg-gray-700 transition-colors cursor-pointer shadow-md">
      <div className="flex justify-between items-center mb-1">
        <h3 className="text-lg font-semibold text-white truncate">{thread.subject || `No. ${thread.thread_id}`}</h3>
        <span className="text-sm bg-teal-800 px-2 py-0.5 rounded text-teal-200">/${thread.board}/</span>
      </div>
      <p className="text-gray-400 text-sm mb-2">Posts: {thread.post_count}</p>
      <p className="text-xs text-gray-500">Last updated: {date}</p>
    </Link>
  );
};

const ThreadList = () => {
  const { data, error, isLoading } = useSWR('/api/threads', fetcher);

  return (
    <div>
      <TrackForm />
      <h2 className="text-2xl font-bold mb-4 text-white">Archived Threads</h2>
      {error && <p className="text-red-400">Failed to load threads: {error.message}</p>}
      {isLoading && <p className="text-gray-400">Loading...</p>}
      
      <div className="space-y-4">
        {data && data.length === 0 && (
          <p className="text-gray-400">No threads tracked yet. Use the form above to start tracking one.</p>
        )}
        {data && data.map((thread) => (
          <ThreadCard key={`${thread.board}-${thread.thread_id}`} thread={thread} />
        ))}
      </div>
    </div>
  );
};

export default ThreadList;
