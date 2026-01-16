/**
 * FeedItem - Single media item card
 *
 * Displays a media item with:
 * - Image with proper aspect ratio
 * - Title and metadata
 * - Platform badge
 * - Score/engagement metrics
 */

import React, { useState } from 'react';
import { Media, getImageUrl, getAspectRatio, MediaType, Platform } from '../hooks/useFeed';

interface FeedItemProps {
  item: Media;
  onClick?: () => void;
  showAspectRatio?: boolean;
  className?: string;
}

/**
 * Single feed item card
 *
 * @example
 * ```tsx
 * <FeedItem
 *   item={mediaItem}
 *   onClick={() => openLightbox(mediaItem)}
 * />
 * ```
 */
export function FeedItem({
  item,
  onClick,
  showAspectRatio = false,
  className = '',
}: FeedItemProps) {
  const [imageError, setImageError] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  const imgSrc = getImageUrl(item);
  const aspectRatio = showAspectRatio ? getAspectRatio(item, 1) : 1;

  const handleImageError = () => {
    setImageError(true);
  };

  const handleImageLoad = () => {
    setImageLoaded(true);
  };

  const isVideo = item.mediaType === 'VIDEO' || item.mimeType?.startsWith('video/');
  const isGif = item.mimeType === 'image/gif';

  return (
    <div
      className={`bg-gray-800 rounded-lg overflow-hidden hover:ring-2 hover:ring-teal-400 transition-all cursor-pointer ${className}`}
      onClick={onClick}
    >
      {/* Image container */}
      <div
        className="relative bg-gray-900"
        style={{ aspectRatio: showAspectRatio ? aspectRatio : 1 }}
      >
        {/* Loading skeleton */}
        {!imageLoaded && !imageError && (
          <div className="absolute inset-0 animate-pulse bg-gray-700" />
        )}

        {/* Image */}
        {!imageError ? (
          <img
            src={imgSrc}
            alt={item.title || 'Media item'}
            className={`w-full h-full object-cover transition-opacity ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            }`}
            loading="lazy"
            onError={handleImageError}
            onLoad={handleImageLoad}
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-gray-500">
            <span className="text-sm">Failed to load</span>
          </div>
        )}

        {/* Media type badge */}
        {(isVideo || isGif) && (
          <div className="absolute top-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
            {isGif ? 'GIF' : 'VIDEO'}
          </div>
        )}

        {/* Platform badge */}
        <div className="absolute bottom-2 left-2">
          <PlatformBadge platform={item.platform} />
        </div>
      </div>

      {/* Content */}
      <div className="p-3">
        {/* Title */}
        <h3 className="text-sm font-medium text-white line-clamp-2 min-h-[2.5rem]">
          {item.title || 'Untitled'}
        </h3>

        {/* Meta row */}
        <div className="flex items-center justify-between text-xs text-gray-400 mt-2">
          {/* Handle/source */}
          <span className="truncate max-w-[60%]">{item.handle.handle}</span>

          {/* Score */}
          {item.score !== undefined && item.score > 0 && (
            <span className="flex items-center gap-1">
              <span className="text-orange-400">+</span>
              {formatNumber(item.score)}
            </span>
          )}
        </div>

        {/* Timestamp */}
        <div className="text-xs text-gray-500 mt-1">
          {formatRelativeTime(item.publishDate)}
        </div>
      </div>
    </div>
  );
}

/**
 * Compact feed item for list views
 */
export function FeedItemCompact({
  item,
  onClick,
  className = '',
}: FeedItemProps) {
  const [imageError, setImageError] = useState(false);
  const imgSrc = getImageUrl(item);

  return (
    <div
      className={`flex gap-3 p-3 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors cursor-pointer ${className}`}
      onClick={onClick}
    >
      {/* Thumbnail */}
      <div className="flex-shrink-0 w-20 h-20 rounded overflow-hidden bg-gray-900">
        {!imageError ? (
          <img
            src={imgSrc}
            alt={item.title || 'Media item'}
            className="w-full h-full object-cover"
            loading="lazy"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-600 text-xs">
            No image
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <h3 className="text-sm font-medium text-white line-clamp-2">
          {item.title || 'Untitled'}
        </h3>
        <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
          <PlatformBadge platform={item.platform} size="sm" />
          <span>{item.handle.handle}</span>
          {item.score !== undefined && item.score > 0 && (
            <span className="text-orange-400">+{formatNumber(item.score)}</span>
          )}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {formatRelativeTime(item.publishDate)}
        </div>
      </div>
    </div>
  );
}

/**
 * Platform badge component
 */
function PlatformBadge({
  platform,
  size = 'md',
}: {
  platform: Platform;
  size?: 'sm' | 'md';
}) {
  const colors: Record<Platform, string> = {
    REDDIT: 'bg-orange-500',
    YOUTUBE: 'bg-red-500',
    TWITTER: 'bg-blue-400',
    INSTAGRAM: 'bg-pink-500',
    TIKTOK: 'bg-black',
    VSCO: 'bg-white text-black',
    RSS: 'bg-yellow-500',
    IMAGEBOARD: 'bg-green-600',
  };

  const labels: Record<Platform, string> = {
    REDDIT: 'Reddit',
    YOUTUBE: 'YT',
    TWITTER: 'X',
    INSTAGRAM: 'IG',
    TIKTOK: 'TT',
    VSCO: 'VSCO',
    RSS: 'RSS',
    IMAGEBOARD: 'IB',
  };

  const sizeClasses = size === 'sm' ? 'text-[10px] px-1 py-0.5' : 'text-xs px-1.5 py-0.5';

  return (
    <span
      className={`${colors[platform] || 'bg-gray-600'} text-white rounded ${sizeClasses} font-medium`}
    >
      {labels[platform] || platform}
    </span>
  );
}

/**
 * Format number with K/M suffix
 */
function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  const diffWeek = Math.floor(diffDay / 7);
  const diffMonth = Math.floor(diffDay / 30);
  const diffYear = Math.floor(diffDay / 365);

  if (diffSec < 60) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  if (diffWeek < 4) return `${diffWeek}w ago`;
  if (diffMonth < 12) return `${diffMonth}mo ago`;
  return `${diffYear}y ago`;
}

export default FeedItem;
