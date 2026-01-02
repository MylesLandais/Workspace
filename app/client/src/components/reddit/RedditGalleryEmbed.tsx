/* eslint-disable @next/next/no-img-element */
'use client';

import React, { useState, useCallback } from 'react';
import type { RedditPost, RedditImage, RedditComment } from '@/lib/types/reddit';
import { RedditPostCard } from './RedditPostCard';

interface RedditGalleryEmbedProps {
  post: RedditPost;
  images: RedditImage[];
  comments?: RedditComment[];
  showComments?: boolean;
  maxComments?: number;
  className?: string;
}

/**
 * RedditGalleryEmbed
 * 
 * Full-featured Reddit post embed with gallery support and optional
 * comment preview. Designed for embedding rich Reddit content in
 * client applications.
 * 
 * Features:
 * - Full-screen lightbox gallery
 * - Keyboard navigation (← → ESC)
 * - Touch/swipe support
 * - Comment preview
 * - NSFW handling
 * 
 * @example
 * <RedditGalleryEmbed 
 *   post={postDetails.post}
 *   images={postDetails.images}
 *   comments={postDetails.comments}
 *   showComments
 *   maxComments={3}
 * />
 */
export function RedditGalleryEmbed({
  post,
  images,
  comments = [],
  showComments = false,
  maxComments = 3,
  className = '',
}: RedditGalleryEmbedProps) {
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxIndex, setLightboxIndex] = useState(0);

  const openLightbox = useCallback((image: RedditImage, index: number) => {
    setLightboxIndex(index);
    setLightboxOpen(true);
    document.body.style.overflow = 'hidden';
  }, []);

  const closeLightbox = useCallback(() => {
    setLightboxOpen(false);
    document.body.style.overflow = '';
  }, []);

  const navigateLightbox = useCallback((direction: 'prev' | 'next') => {
    setLightboxIndex((current) => {
      if (direction === 'prev') {
        return current > 0 ? current - 1 : images.length - 1;
      }
      return current < images.length - 1 ? current + 1 : 0;
    });
  }, [images.length]);

  // Keyboard navigation
  React.useEffect(() => {
    if (!lightboxOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          closeLightbox();
          break;
        case 'ArrowLeft':
          navigateLightbox('prev');
          break;
        case 'ArrowRight':
          navigateLightbox('next');
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [lightboxOpen, closeLightbox, navigateLightbox]);

  const formatTimeAgo = (isoDate: string): string => {
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 30) return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    if (diffDays > 0) return `${diffDays}d`;
    if (diffHours > 0) return `${diffHours}h`;
    if (diffMins > 0) return `${diffMins}m`;
    return 'now';
  };

  const displayComments = showComments 
    ? comments.slice(0, maxComments)
    : [];

  return (
    <div className={`reddit-gallery-embed ${className}`}>
      <RedditPostCard
        post={post}
        images={images}
        variant="expanded"
        onImageClick={openLightbox}
      />

      {/* Comment Preview */}
      {displayComments.length > 0 && (
        <div className="reddit-gallery-embed__comments">
          <h4 className="reddit-gallery-embed__comments-header">
            Top Comments
            {comments.length > maxComments && (
              <span className="reddit-gallery-embed__comments-more">
                +{comments.length - maxComments} more
              </span>
            )}
          </h4>
          <ul className="reddit-gallery-embed__comments-list">
            {displayComments.map((comment) => (
              <li key={comment.id} className="reddit-gallery-embed__comment">
                <div className="reddit-gallery-embed__comment-header">
                  <span className={`reddit-gallery-embed__comment-author ${comment.is_submitter ? 'reddit-gallery-embed__comment-author--op' : ''}`}>
                    {comment.author || '[deleted]'}
                    {comment.is_submitter && <span className="reddit-gallery-embed__op-badge">OP</span>}
                  </span>
                  <span className="reddit-gallery-embed__comment-meta">
                    {comment.score} pts • {formatTimeAgo(comment.created_utc)}
                  </span>
                </div>
                <p className="reddit-gallery-embed__comment-body">
                  {comment.body.slice(0, 200)}{comment.body.length > 200 ? '...' : ''}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Lightbox */}
      {lightboxOpen && images.length > 0 && (
        <div 
          className="reddit-gallery-embed__lightbox"
          onClick={closeLightbox}
        >
          <button 
            className="reddit-gallery-embed__lightbox-close"
            onClick={closeLightbox}
            aria-label="Close gallery"
          >
            ✕
          </button>

          <div 
            className="reddit-gallery-embed__lightbox-content"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={images[lightboxIndex]?.url}
              alt={`${post.title} - Image ${lightboxIndex + 1}`}
              className="reddit-gallery-embed__lightbox-image"
            />
          </div>

          {images.length > 1 && (
            <>
              <button
                className="reddit-gallery-embed__lightbox-nav reddit-gallery-embed__lightbox-nav--prev"
                onClick={(e) => {
                  e.stopPropagation();
                  navigateLightbox('prev');
                }}
                aria-label="Previous image"
              >
                ‹
              </button>
              <button
                className="reddit-gallery-embed__lightbox-nav reddit-gallery-embed__lightbox-nav--next"
                onClick={(e) => {
                  e.stopPropagation();
                  navigateLightbox('next');
                }}
                aria-label="Next image"
              >
                ›
              </button>
              <div className="reddit-gallery-embed__lightbox-counter">
                {lightboxIndex + 1} / {images.length}
              </div>
            </>
          )}
        </div>
      )}

      <style jsx>{`
        .reddit-gallery-embed {
          --card-bg: #0a0a0a;
          --card-border: #1a1a1a;
          --text-primary: #fafafa;
          --text-secondary: #888;
          --text-muted: #555;
          --accent: #ff4500;
          --op-badge: #0079d3;
        }

        /* Comments Section */
        .reddit-gallery-embed__comments {
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-top: none;
          border-radius: 0 0 12px 12px;
          margin-top: -1px;
          padding: 16px;
        }

        .reddit-gallery-embed__comments-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin: 0 0 12px;
          font-size: 13px;
          font-weight: 600;
          color: var(--text-secondary);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .reddit-gallery-embed__comments-more {
          font-weight: 400;
          color: var(--text-muted);
          text-transform: none;
        }

        .reddit-gallery-embed__comments-list {
          list-style: none;
          margin: 0;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .reddit-gallery-embed__comment {
          padding: 12px;
          background: rgba(255, 255, 255, 0.02);
          border-radius: 8px;
          border-left: 2px solid var(--card-border);
        }

        .reddit-gallery-embed__comment-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 6px;
        }

        .reddit-gallery-embed__comment-author {
          font-size: 13px;
          font-weight: 500;
          color: var(--text-primary);
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .reddit-gallery-embed__comment-author--op {
          color: var(--op-badge);
        }

        .reddit-gallery-embed__op-badge {
          background: var(--op-badge);
          color: white;
          font-size: 10px;
          font-weight: 700;
          padding: 1px 4px;
          border-radius: 3px;
        }

        .reddit-gallery-embed__comment-meta {
          font-size: 11px;
          color: var(--text-muted);
        }

        .reddit-gallery-embed__comment-body {
          margin: 0;
          font-size: 14px;
          line-height: 1.5;
          color: var(--text-secondary);
        }

        /* Lightbox */
        .reddit-gallery-embed__lightbox {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: 9999;
          background: rgba(0, 0, 0, 0.95);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: zoom-out;
        }

        .reddit-gallery-embed__lightbox-close {
          position: absolute;
          top: 20px;
          right: 20px;
          width: 44px;
          height: 44px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(255, 255, 255, 0.1);
          border: none;
          border-radius: 50%;
          color: white;
          font-size: 20px;
          cursor: pointer;
          transition: background 0.2s ease;
          z-index: 10;
        }

        .reddit-gallery-embed__lightbox-close:hover {
          background: rgba(255, 255, 255, 0.2);
        }

        .reddit-gallery-embed__lightbox-content {
          max-width: 90vw;
          max-height: 90vh;
          cursor: default;
        }

        .reddit-gallery-embed__lightbox-image {
          max-width: 100%;
          max-height: 90vh;
          object-fit: contain;
          border-radius: 4px;
        }

        .reddit-gallery-embed__lightbox-nav {
          position: absolute;
          top: 50%;
          transform: translateY(-50%);
          width: 56px;
          height: 56px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(255, 255, 255, 0.1);
          border: none;
          border-radius: 50%;
          color: white;
          font-size: 32px;
          cursor: pointer;
          transition: background 0.2s ease;
        }

        .reddit-gallery-embed__lightbox-nav:hover {
          background: rgba(255, 255, 255, 0.2);
        }

        .reddit-gallery-embed__lightbox-nav--prev {
          left: 20px;
        }

        .reddit-gallery-embed__lightbox-nav--next {
          right: 20px;
        }

        .reddit-gallery-embed__lightbox-counter {
          position: absolute;
          bottom: 20px;
          left: 50%;
          transform: translateX(-50%);
          background: rgba(0, 0, 0, 0.6);
          padding: 8px 16px;
          border-radius: 20px;
          color: white;
          font-size: 14px;
          font-weight: 500;
        }

        /* Firefox-specific fixes */
        @supports (-moz-appearance: none) {
          .reddit-gallery-embed__lightbox-image {
            /* Ensure proper sizing in Firefox */
            width: auto;
            height: auto;
          }
        }
      `}</style>
    </div>
  );
}

export default RedditGalleryEmbed;
