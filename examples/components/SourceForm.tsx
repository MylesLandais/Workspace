/**
 * SourceForm - Add/edit source form
 *
 * Form for adding new sources or editing existing ones with:
 * - Platform-specific fields
 * - Subreddit search/autocomplete
 * - Validation
 */

import React, { useState, useEffect } from 'react';
import {
  useSources,
  useSubredditSearch,
  CreateSourceInput,
  Source,
  Platform,
  getPlatformLabel,
} from '../hooks/useSources';

interface SourceFormProps {
  source?: Source; // For editing
  onSuccess?: (source: Source) => void;
  onCancel?: () => void;
  defaultGroupId?: string;
  className?: string;
}

/**
 * Form for adding/editing sources
 *
 * @example
 * ```tsx
 * // Add new source
 * <SourceForm
 *   onSuccess={(source) => console.log('Added:', source)}
 *   onCancel={() => setShowForm(false)}
 * />
 *
 * // Edit existing source
 * <SourceForm
 *   source={existingSource}
 *   onSuccess={(source) => console.log('Updated:', source)}
 * />
 * ```
 */
export function SourceForm({
  source,
  onSuccess,
  onCancel,
  defaultGroupId,
  className = '',
}: SourceFormProps) {
  const { createSource } = useSources();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [platform, setPlatform] = useState<Platform>(
    source?.sourceType || 'REDDIT'
  );
  const [name, setName] = useState(source?.name || '');
  const [handle, setHandle] = useState('');
  const [url, setUrl] = useState(source?.url || '');
  const [description, setDescription] = useState(source?.description || '');

  // Subreddit search
  const [subredditQuery, setSubredditQuery] = useState('');
  const { results: subredditResults, isLoading: isSearching } =
    useSubredditSearch(subredditQuery);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Initialize handle based on source
  useEffect(() => {
    if (source) {
      switch (source.sourceType) {
        case 'REDDIT':
          setHandle(source.subredditName || '');
          break;
        case 'YOUTUBE':
          setHandle(source.youtubeHandle || '');
          break;
        case 'TWITTER':
          setHandle(source.twitterHandle || '');
          break;
        case 'INSTAGRAM':
          setHandle(source.instagramHandle || '');
          break;
        case 'TIKTOK':
          setHandle(source.tiktokHandle || '');
          break;
        case 'RSS':
          setHandle(source.rssUrl || '');
          break;
      }
    }
  }, [source]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const input: CreateSourceInput = {
        name: name || handle,
        sourceType: platform,
        description: description || undefined,
        groupId: defaultGroupId,
      };

      // Set platform-specific fields
      switch (platform) {
        case 'REDDIT':
          input.subredditName = handle.replace(/^r\//, '');
          break;
        case 'YOUTUBE':
          input.youtubeHandle = handle.replace(/^@/, '');
          break;
        case 'TWITTER':
          input.twitterHandle = handle.replace(/^@/, '');
          break;
        case 'INSTAGRAM':
          input.instagramHandle = handle.replace(/^@/, '');
          break;
        case 'TIKTOK':
          input.tiktokHandle = handle.replace(/^@/, '');
          break;
        case 'RSS':
          input.url = handle;
          break;
        default:
          input.url = url || handle;
      }

      const result = await createSource(input);
      onSuccess?.(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add source');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectSubreddit = (subreddit: { name: string; displayName: string }) => {
    setHandle(subreddit.name);
    setName(subreddit.displayName || `r/${subreddit.name}`);
    setSubredditQuery('');
    setShowSuggestions(false);
  };

  const getHandlePlaceholder = () => {
    switch (platform) {
      case 'REDDIT':
        return 'unixporn (without r/)';
      case 'YOUTUBE':
        return '@channel or channel handle';
      case 'TWITTER':
        return '@username';
      case 'INSTAGRAM':
        return '@username';
      case 'TIKTOK':
        return '@username';
      case 'RSS':
        return 'https://example.com/feed.xml';
      default:
        return 'Source identifier';
    }
  };

  const getHandleLabel = () => {
    switch (platform) {
      case 'REDDIT':
        return 'Subreddit';
      case 'YOUTUBE':
        return 'Channel';
      case 'TWITTER':
      case 'INSTAGRAM':
      case 'TIKTOK':
        return 'Username';
      case 'RSS':
        return 'Feed URL';
      default:
        return 'Handle';
    }
  };

  return (
    <form onSubmit={handleSubmit} className={`space-y-4 ${className}`}>
      {/* Platform selector */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">
          Platform
        </label>
        <select
          value={platform}
          onChange={(e) => {
            setPlatform(e.target.value as Platform);
            setHandle('');
            setName('');
          }}
          disabled={!!source}
          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-teal-400 disabled:opacity-50"
        >
          <option value="REDDIT">Reddit</option>
          <option value="YOUTUBE">YouTube</option>
          <option value="RSS">RSS Feed</option>
          <option value="TWITTER">Twitter/X</option>
          <option value="INSTAGRAM">Instagram</option>
          <option value="TIKTOK">TikTok</option>
          <option value="IMAGEBOARD">Imageboard</option>
        </select>
      </div>

      {/* Handle/identifier */}
      <div className="relative">
        <label className="block text-sm font-medium text-gray-300 mb-1">
          {getHandleLabel()}
        </label>

        {platform === 'REDDIT' ? (
          <>
            <div className="flex">
              <span className="inline-flex items-center px-3 rounded-l-lg border border-r-0 border-gray-700 bg-gray-900 text-gray-500">
                r/
              </span>
              <input
                type="text"
                value={handle}
                onChange={(e) => {
                  setHandle(e.target.value);
                  setSubredditQuery(e.target.value);
                  setShowSuggestions(true);
                }}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                placeholder={getHandlePlaceholder()}
                className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-r-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-teal-400"
                required
              />
            </div>

            {/* Subreddit suggestions */}
            {showSuggestions && subredditQuery.length >= 2 && (
              <div className="absolute z-10 mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg shadow-lg max-h-60 overflow-auto">
                {isSearching ? (
                  <div className="px-4 py-3 text-gray-400">Searching...</div>
                ) : subredditResults.length > 0 ? (
                  subredditResults.map((sub) => (
                    <button
                      key={sub.name}
                      type="button"
                      onClick={() => handleSelectSubreddit(sub)}
                      className="w-full px-4 py-2 text-left hover:bg-gray-700 flex items-center gap-3"
                    >
                      <div>
                        <div className="text-white font-medium">r/{sub.name}</div>
                        <div className="text-xs text-gray-400">
                          {sub.subscriberCount.toLocaleString()} subscribers
                        </div>
                      </div>
                      {sub.isSubscribed && (
                        <span className="ml-auto text-xs text-green-500">
                          Subscribed
                        </span>
                      )}
                    </button>
                  ))
                ) : (
                  <div className="px-4 py-3 text-gray-400">No results</div>
                )}
              </div>
            )}
          </>
        ) : (
          <input
            type={platform === 'RSS' ? 'url' : 'text'}
            value={handle}
            onChange={(e) => setHandle(e.target.value)}
            placeholder={getHandlePlaceholder()}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-teal-400"
            required
          />
        )}
      </div>

      {/* Display name */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">
          Display Name
          <span className="text-gray-500 font-normal"> (optional)</span>
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Custom display name"
          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-teal-400"
        />
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">
          Description
          <span className="text-gray-500 font-normal"> (optional)</span>
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Notes about this source"
          rows={2}
          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-teal-400 resize-none"
        />
      </div>

      {/* Error */}
      {error && (
        <div className="text-red-400 text-sm bg-red-900/20 px-3 py-2 rounded-lg">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3 justify-end">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-gray-400 hover:text-white"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={isSubmitting || !handle}
          className="px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Adding...' : source ? 'Save Changes' : 'Add Source'}
        </button>
      </div>
    </form>
  );
}

/**
 * Modal wrapper for SourceForm
 */
export function SourceFormModal({
  isOpen,
  onClose,
  onSuccess,
  source,
  defaultGroupId,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (source: Source) => void;
  source?: Source;
  defaultGroupId?: string;
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-bold text-white mb-4">
          {source ? 'Edit Source' : 'Add Source'}
        </h2>

        <SourceForm
          source={source}
          defaultGroupId={defaultGroupId}
          onSuccess={(s) => {
            onSuccess?.(s);
            onClose();
          }}
          onCancel={onClose}
        />
      </div>
    </div>
  );
}

export default SourceForm;
