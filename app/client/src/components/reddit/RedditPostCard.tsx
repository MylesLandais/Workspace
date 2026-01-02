/* eslint-disable @next/next/no-img-element */
'use client';

import React, { useState } from 'react';
import type { RedditPost, RedditImage } from '@/lib/types/reddit';

interface RedditPostCardProps {
  post: RedditPost;
  images?: RedditImage[];
  variant?: 'compact' | 'expanded' | 'minimal';
  showNSFWBlur?: boolean;
  onImageClick?: (image: RedditImage, index: number) => void;
  className?: string;
}

/**
 * RedditPostCard
 * 
 * A premium embeddable Reddit post component following Bunny's
 * dark, editorial aesthetic. Supports single images, galleries,
 * and text posts.
 * 
 * @example
 * <RedditPostCard 
 *   post={post} 
 *   images={images}
 *   variant="expanded"
 * />
 */
export function RedditPostCard({
  post,
  images = [],
  variant = 'expanded',
  showNSFWBlur = true,
  onImageClick,
  className = '',
}: RedditPostCardProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isNSFWRevealed, setIsNSFWRevealed] = useState(false);
  const [imageError, setImageError] = useState(false);

  const hasMultipleImages = images.length > 1;
  const hasImage = post.is_image && (images.length > 0 || post.image_url);
  const shouldBlur = post.over_18 && showNSFWBlur && !isNSFWRevealed;

  const formatTimeAgo = (isoDate: string): string => {
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 30) return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    if (diffMins > 0) return `${diffMins}m ago`;
    return 'just now';
  };

  const formatScore = (score: number): string => {
    if (score >= 10000) return `${(score / 1000).toFixed(1)}k`;
    if (score >= 1000) return `${(score / 1000).toFixed(1)}k`;
    return score.toString();
  };

  const getCurrentImageUrl = (): string | null => {
    if (images.length > 0) {
      return images[currentImageIndex]?.url || null;
    }
    return post.image_url;
  };

  const handlePrevImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev > 0 ? prev - 1 : images.length - 1));
  };

  const handleNextImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev < images.length - 1 ? prev + 1 : 0));
  };

  const handleImageClick = () => {
    if (onImageClick && images[currentImageIndex]) {
      onImageClick(images[currentImageIndex], currentImageIndex);
    }
  };

  const redditUrl = post.permalink 
    ? `https://reddit.com${post.permalink}`
    : `https://reddit.com/r/${post.subreddit}/comments/${post.id}`;

  return (
    <article 
      className={`
        reddit-post-card
        reddit-post-card--${variant}
        ${className}
      `}
      data-nsfw={post.over_18}
      data-has-image={hasImage}
    >
      {/* Header: Subreddit + Author + Time */}
      <header className="reddit-post-card__header">
        <div className="reddit-post-card__source">
          <a 
            href={`https://reddit.com/r/${post.subreddit}`}
            target="_blank"
            rel="noopener noreferrer"
            className="reddit-post-card__subreddit"
          >
            <span className="reddit-post-card__subreddit-prefix">r/</span>
            {post.subreddit}
          </a>
          {post.author && (
            <>
              <span className="reddit-post-card__separator">•</span>
              <a 
                href={`https://reddit.com/u/${post.author}`}
                target="_blank"
                rel="noopener noreferrer"
                className="reddit-post-card__author"
              >
                u/{post.author}
              </a>
            </>
          )}
        </div>
        <time 
          className="reddit-post-card__time"
          dateTime={post.created_utc}
          title={new Date(post.created_utc).toLocaleString()}
        >
          {formatTimeAgo(post.created_utc)}
        </time>
      </header>

      {/* Title */}
      <h3 className="reddit-post-card__title">
        <a 
          href={redditUrl}
          target="_blank"
          rel="noopener noreferrer"
        >
          {post.title}
          {post.over_18 && (
            <span className="reddit-post-card__nsfw-badge">NSFW</span>
          )}
        </a>
      </h3>

      {/* Image / Gallery */}
      {hasImage && !imageError && (
        <div 
          className={`
            reddit-post-card__media
            ${shouldBlur ? 'reddit-post-card__media--blurred' : ''}
          `}
        >
          {shouldBlur && (
            <button
              className="reddit-post-card__nsfw-reveal"
              onClick={() => setIsNSFWRevealed(true)}
              aria-label="Reveal NSFW content"
            >
              <span className="reddit-post-card__nsfw-icon">👁</span>
              <span>Click to reveal</span>
            </button>
          )}
          
          <img
            src={getCurrentImageUrl() || ''}
            alt={post.title}
            className="reddit-post-card__image"
            onClick={handleImageClick}
            onError={() => setImageError(true)}
            loading="lazy"
          />

          {/* Gallery Navigation */}
          {hasMultipleImages && !shouldBlur && (
            <>
              <button
                className="reddit-post-card__nav reddit-post-card__nav--prev"
                onClick={handlePrevImage}
                aria-label="Previous image"
              >
                ‹
              </button>
              <button
                className="reddit-post-card__nav reddit-post-card__nav--next"
                onClick={handleNextImage}
                aria-label="Next image"
              >
                ›
              </button>
              <div className="reddit-post-card__gallery-indicator">
                {images.map((_, idx) => (
                  <span
                    key={idx}
                    className={`
                      reddit-post-card__gallery-dot
                      ${idx === currentImageIndex ? 'reddit-post-card__gallery-dot--active' : ''}
                    `}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Self Text (if text post and expanded) */}
      {variant === 'expanded' && post.selftext && (
        <div className="reddit-post-card__body">
          <p>{post.selftext.slice(0, 280)}{post.selftext.length > 280 ? '...' : ''}</p>
        </div>
      )}

      {/* Footer: Stats */}
      <footer className="reddit-post-card__footer">
        <div className="reddit-post-card__stats">
          <span className="reddit-post-card__stat reddit-post-card__stat--score">
            <svg className="reddit-post-card__stat-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8-8-8z" transform="rotate(-90 12 12)"/>
            </svg>
            {formatScore(post.score)}
          </span>
          <span className="reddit-post-card__stat reddit-post-card__stat--comments">
            <svg className="reddit-post-card__stat-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M21 6h-2v9H6v2c0 .55.45 1 1 1h11l4 4V7c0-.55-.45-1-1-1zm-4 6V3c0-.55-.45-1-1-1H3c-.55 0-1 .45-1 1v14l4-4h10c.55 0 1-.45 1-1z"/>
            </svg>
            {post.num_comments}
          </span>
          <span 
            className="reddit-post-card__stat reddit-post-card__stat--ratio"
            title={`${Math.round(post.upvote_ratio * 100)}% upvoted`}
          >
            {Math.round(post.upvote_ratio * 100)}%
          </span>
        </div>

        <a 
          href={redditUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="reddit-post-card__link"
        >
          View on Reddit
          <svg className="reddit-post-card__link-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 19H5V5h7V3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/>
          </svg>
        </a>
      </footer>

      <style jsx>{`
        .reddit-post-card {
          --card-bg: #0a0a0a;
          --card-border: #1a1a1a;
          --card-hover-border: #2a2a2a;
          --text-primary: #fafafa;
          --text-secondary: #888;
          --text-muted: #555;
          --accent: #ff4500;
          --accent-hover: #ff5722;
          --nsfw-badge: #d32f2f;
          --upvote: #ff8b60;
          
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: 12px;
          overflow: hidden;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        .reddit-post-card:hover {
          border-color: var(--card-hover-border);
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }

        /* Compact variant */
        .reddit-post-card--compact {
          display: grid;
          grid-template-columns: 120px 1fr;
          gap: 0;
        }

        .reddit-post-card--compact .reddit-post-card__media {
          grid-row: 1 / -1;
          aspect-ratio: 1;
          height: 100%;
        }

        .reddit-post-card--compact .reddit-post-card__header,
        .reddit-post-card--compact .reddit-post-card__title,
        .reddit-post-card--compact .reddit-post-card__footer {
          padding-left: 12px;
        }

        /* Minimal variant */
        .reddit-post-card--minimal .reddit-post-card__media {
          display: none;
        }

        /* Header */
        .reddit-post-card__header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px 8px;
        }

        .reddit-post-card__source {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
        }

        .reddit-post-card__subreddit {
          color: var(--text-primary);
          text-decoration: none;
          font-weight: 600;
          transition: color 0.15s ease;
        }

        .reddit-post-card__subreddit:hover {
          color: var(--accent);
        }

        .reddit-post-card__subreddit-prefix {
          color: var(--text-muted);
          font-weight: 400;
        }

        .reddit-post-card__separator {
          color: var(--text-muted);
        }

        .reddit-post-card__author {
          color: var(--text-secondary);
          text-decoration: none;
          font-size: 12px;
          transition: color 0.15s ease;
        }

        .reddit-post-card__author:hover {
          color: var(--text-primary);
        }

        .reddit-post-card__time {
          color: var(--text-muted);
          font-size: 12px;
        }

        /* Title */
        .reddit-post-card__title {
          margin: 0;
          padding: 0 16px 12px;
          font-size: 15px;
          font-weight: 500;
          line-height: 1.4;
        }

        .reddit-post-card__title a {
          color: var(--text-primary);
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          gap: 8px;
        }

        .reddit-post-card__title a:hover {
          color: var(--accent);
        }

        .reddit-post-card__nsfw-badge {
          background: var(--nsfw-badge);
          color: white;
          font-size: 10px;
          font-weight: 700;
          padding: 2px 6px;
          border-radius: 4px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        /* Media */
        .reddit-post-card__media {
          position: relative;
          width: 100%;
          aspect-ratio: 4/3;
          background: #111;
          overflow: hidden;
        }

        .reddit-post-card__media--blurred .reddit-post-card__image {
          filter: blur(24px) brightness(0.6);
        }

        .reddit-post-card__image {
          width: 100%;
          height: 100%;
          object-fit: cover;
          cursor: pointer;
          transition: transform 0.3s ease;
        }

        .reddit-post-card__image:hover {
          transform: scale(1.02);
        }

        .reddit-post-card__nsfw-reveal {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          z-index: 10;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 16px 24px;
          background: rgba(0, 0, 0, 0.7);
          backdrop-filter: blur(4px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: var(--text-primary);
          font-size: 13px;
          cursor: pointer;
          transition: background 0.2s ease;
        }

        .reddit-post-card__nsfw-reveal:hover {
          background: rgba(0, 0, 0, 0.85);
        }

        .reddit-post-card__nsfw-icon {
          font-size: 24px;
        }

        /* Gallery Navigation */
        .reddit-post-card__nav {
          position: absolute;
          top: 50%;
          transform: translateY(-50%);
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(0, 0, 0, 0.6);
          backdrop-filter: blur(4px);
          border: none;
          border-radius: 50%;
          color: white;
          font-size: 24px;
          cursor: pointer;
          opacity: 0;
          transition: opacity 0.2s ease, background 0.2s ease;
          z-index: 5;
        }

        .reddit-post-card__media:hover .reddit-post-card__nav {
          opacity: 1;
        }

        .reddit-post-card__nav:hover {
          background: rgba(0, 0, 0, 0.8);
        }

        .reddit-post-card__nav--prev {
          left: 12px;
        }

        .reddit-post-card__nav--next {
          right: 12px;
        }

        .reddit-post-card__gallery-indicator {
          position: absolute;
          bottom: 12px;
          left: 50%;
          transform: translateX(-50%);
          display: flex;
          gap: 6px;
          z-index: 5;
        }

        .reddit-post-card__gallery-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.4);
          transition: background 0.2s ease, transform 0.2s ease;
        }

        .reddit-post-card__gallery-dot--active {
          background: white;
          transform: scale(1.3);
        }

        /* Body (self text) */
        .reddit-post-card__body {
          padding: 0 16px 12px;
          font-size: 14px;
          line-height: 1.5;
          color: var(--text-secondary);
        }

        .reddit-post-card__body p {
          margin: 0;
        }

        /* Footer */
        .reddit-post-card__footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border-top: 1px solid var(--card-border);
        }

        .reddit-post-card__stats {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .reddit-post-card__stat {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 13px;
          color: var(--text-secondary);
        }

        .reddit-post-card__stat--score {
          color: var(--upvote);
          font-weight: 600;
        }

        .reddit-post-card__stat-icon {
          width: 16px;
          height: 16px;
        }

        .reddit-post-card__link {
          display: flex;
          align-items: center;
          gap: 4px;
          color: var(--text-muted);
          font-size: 12px;
          text-decoration: none;
          transition: color 0.15s ease;
        }

        .reddit-post-card__link:hover {
          color: var(--accent);
        }

        .reddit-post-card__link-icon {
          width: 14px;
          height: 14px;
        }

        /* Firefox-specific fixes */
        @supports (-moz-appearance: none) {
          .reddit-post-card__media {
            /* Firefox aspect-ratio fallback */
            min-height: 200px;
          }
          
          .reddit-post-card__nav {
            /* Ensure visibility on Firefox */
            opacity: 0.8;
          }
        }
      `}</style>
    </article>
  );
}

export default RedditPostCard;
