"use client";

import React, { useState } from "react";
import { useNeo4jRedditPosts } from "@/hooks/useNeo4jReddit";
import { RedditPostCard } from "./RedditPostCard";
import type { RedditPost, RedditImage } from "@/lib/types/reddit";

interface UnixpornWidgetProps {
  /** Number of posts to display */
  limit?: number;
  /** Layout variant */
  variant?: "grid" | "list" | "masonry";
  /** Number of columns for grid layout */
  columns?: 1 | 2 | 3 | 4;
  /** Show NSFW content with blur */
  showNSFW?: boolean;
  /** Optional class name */
  className?: string;
  /** Callback when an image is clicked */
  onImageClick?: (post: RedditPost, imageIndex: number) => void;
}

/**
 * UnixpornWidget
 *
 * A widget that displays posts from r/unixporn fetched from the Neo4j database.
 * Uses the internal GraphQL API to fetch data.
 *
 * @example
 * <UnixpornWidget limit={12} variant="grid" columns={3} />
 */
export function UnixpornWidget({
  limit = 12,
  variant = "grid",
  columns = 3,
  showNSFW = true,
  className = "",
  onImageClick,
}: UnixpornWidgetProps) {
  const { posts, loading, error, refetch } = useNeo4jRedditPosts(
    "unixporn",
    limit,
  );
  const [selectedPost, setSelectedPost] = useState<RedditPost | null>(null);

  const handleImageClick = (post: RedditPost, index: number) => {
    if (onImageClick) {
      onImageClick(post, index);
    } else {
      setSelectedPost(post);
    }
  };

  // Convert post image to RedditImage array for RedditPostCard
  const getImagesForPost = (post: RedditPost): RedditImage[] => {
    if (!post.is_image || !post.image_url) return [];
    return [{ url: post.image_url, image_path: null }];
  };

  if (loading) {
    return (
      <div className={`unixporn-widget unixporn-widget--loading ${className}`}>
        <div className="unixporn-widget__header">
          <h2 className="unixporn-widget__title">r/unixporn</h2>
          <span className="unixporn-widget__subtitle">Loading posts...</span>
        </div>
        <div
          className={`unixporn-widget__grid unixporn-widget__grid--${columns}`}
        >
          {Array.from({ length: limit }).map((_, i) => (
            <div key={i} className="unixporn-widget__skeleton" />
          ))}
        </div>
        <style jsx>{skeletonStyles}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`unixporn-widget unixporn-widget--error ${className}`}>
        <div className="unixporn-widget__header">
          <h2 className="unixporn-widget__title">r/unixporn</h2>
        </div>
        <div className="unixporn-widget__error">
          <p>Failed to load posts</p>
          <p className="unixporn-widget__error-message">{error.message}</p>
          <button onClick={refetch} className="unixporn-widget__retry-btn">
            Try Again
          </button>
        </div>
        <style jsx>{errorStyles}</style>
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <div className={`unixporn-widget unixporn-widget--empty ${className}`}>
        <div className="unixporn-widget__header">
          <h2 className="unixporn-widget__title">r/unixporn</h2>
        </div>
        <div className="unixporn-widget__empty">
          <p>No posts found in the database</p>
          <p className="unixporn-widget__empty-hint">
            Run the Reddit data ingestion script to populate Neo4j
          </p>
        </div>
        <style jsx>{emptyStyles}</style>
      </div>
    );
  }

  const gridClass =
    variant === "grid"
      ? `unixporn-widget__grid unixporn-widget__grid--${columns}`
      : variant === "list"
        ? "unixporn-widget__list"
        : "unixporn-widget__masonry";

  return (
    <div className={`unixporn-widget ${className}`}>
      <div className="unixporn-widget__header">
        <h2 className="unixporn-widget__title">
          <a
            href="https://reddit.com/r/unixporn"
            target="_blank"
            rel="noopener noreferrer"
          >
            r/unixporn
          </a>
        </h2>
        <span className="unixporn-widget__count">{posts.length} posts</span>
        <button
          onClick={refetch}
          className="unixporn-widget__refresh-btn"
          title="Refresh posts"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M23 4v6h-6M1 20v-6h6" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
        </button>
      </div>

      <div className={gridClass}>
        {posts.map((post) => (
          <RedditPostCard
            key={post.id}
            post={post}
            images={getImagesForPost(post)}
            variant={variant === "list" ? "compact" : "expanded"}
            showNSFWBlur={!showNSFW}
            onImageClick={(image, index) => handleImageClick(post, index)}
          />
        ))}
      </div>

      {/* Simple lightbox modal */}
      {selectedPost && selectedPost.is_image && selectedPost.image_url && (
        <div
          className="unixporn-widget__lightbox"
          onClick={() => setSelectedPost(null)}
        >
          <div
            className="unixporn-widget__lightbox-content"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="unixporn-widget__lightbox-close"
              onClick={() => setSelectedPost(null)}
            >
              &times;
            </button>
            <img
              src={selectedPost.image_url}
              alt={selectedPost.title}
              className="unixporn-widget__lightbox-image"
            />
            <div className="unixporn-widget__lightbox-info">
              <h3>{selectedPost.title}</h3>
              <p>
                by u/{selectedPost.author} in r/{selectedPost.subreddit}
              </p>
              <p>
                {selectedPost.score} points &middot; {selectedPost.num_comments}{" "}
                comments
              </p>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .unixporn-widget {
          --widget-bg: #0a0a0a;
          --widget-border: #1a1a1a;
          --widget-text: #fafafa;
          --widget-text-muted: #888;
          --widget-accent: #ff4500;
        }

        .unixporn-widget__header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid var(--widget-border);
        }

        .unixporn-widget__title {
          margin: 0;
          font-size: 20px;
          font-weight: 600;
        }

        .unixporn-widget__title a {
          color: var(--widget-text);
          text-decoration: none;
          transition: color 0.2s;
        }

        .unixporn-widget__title a:hover {
          color: var(--widget-accent);
        }

        .unixporn-widget__count {
          color: var(--widget-text-muted);
          font-size: 14px;
        }

        .unixporn-widget__refresh-btn {
          margin-left: auto;
          background: transparent;
          border: 1px solid var(--widget-border);
          border-radius: 6px;
          padding: 6px 8px;
          color: var(--widget-text-muted);
          cursor: pointer;
          transition: all 0.2s;
        }

        .unixporn-widget__refresh-btn:hover {
          background: var(--widget-border);
          color: var(--widget-text);
        }

        .unixporn-widget__grid {
          display: grid;
          gap: 16px;
        }

        .unixporn-widget__grid--1 {
          grid-template-columns: 1fr;
        }

        .unixporn-widget__grid--2 {
          grid-template-columns: repeat(2, 1fr);
        }

        .unixporn-widget__grid--3 {
          grid-template-columns: repeat(3, 1fr);
        }

        .unixporn-widget__grid--4 {
          grid-template-columns: repeat(4, 1fr);
        }

        .unixporn-widget__list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .unixporn-widget__masonry {
          column-count: 3;
          column-gap: 16px;
        }

        .unixporn-widget__masonry > :global(*) {
          break-inside: avoid;
          margin-bottom: 16px;
        }

        /* Lightbox */
        .unixporn-widget__lightbox {
          position: fixed;
          inset: 0;
          z-index: 1000;
          background: rgba(0, 0, 0, 0.9);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 24px;
        }

        .unixporn-widget__lightbox-content {
          position: relative;
          max-width: 90vw;
          max-height: 90vh;
          display: flex;
          flex-direction: column;
        }

        .unixporn-widget__lightbox-close {
          position: absolute;
          top: -40px;
          right: 0;
          background: transparent;
          border: none;
          color: white;
          font-size: 32px;
          cursor: pointer;
          padding: 0;
          line-height: 1;
        }

        .unixporn-widget__lightbox-image {
          max-width: 100%;
          max-height: calc(90vh - 100px);
          object-fit: contain;
          border-radius: 8px;
        }

        .unixporn-widget__lightbox-info {
          margin-top: 16px;
          color: white;
        }

        .unixporn-widget__lightbox-info h3 {
          margin: 0 0 8px;
          font-size: 16px;
        }

        .unixporn-widget__lightbox-info p {
          margin: 0 0 4px;
          font-size: 14px;
          color: #aaa;
        }

        @media (max-width: 768px) {
          .unixporn-widget__grid--3,
          .unixporn-widget__grid--4 {
            grid-template-columns: repeat(2, 1fr);
          }

          .unixporn-widget__masonry {
            column-count: 2;
          }
        }

        @media (max-width: 480px) {
          .unixporn-widget__grid--2,
          .unixporn-widget__grid--3,
          .unixporn-widget__grid--4 {
            grid-template-columns: 1fr;
          }

          .unixporn-widget__masonry {
            column-count: 1;
          }
        }
      `}</style>
    </div>
  );
}

const skeletonStyles = `
  .unixporn-widget__skeleton {
    background: linear-gradient(90deg, #1a1a1a 25%, #2a2a2a 50%, #1a1a1a 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 12px;
    min-height: 200px;
  }

  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
`;

const errorStyles = `
  .unixporn-widget__error {
    text-align: center;
    padding: 48px 24px;
    background: #1a1a1a;
    border-radius: 12px;
  }

  .unixporn-widget__error p {
    margin: 0 0 8px;
    color: #fafafa;
  }

  .unixporn-widget__error-message {
    color: #888 !important;
    font-size: 14px;
  }

  .unixporn-widget__retry-btn {
    margin-top: 16px;
    padding: 8px 16px;
    background: #ff4500;
    border: none;
    border-radius: 6px;
    color: white;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
  }

  .unixporn-widget__retry-btn:hover {
    background: #ff5722;
  }
`;

const emptyStyles = `
  .unixporn-widget__empty {
    text-align: center;
    padding: 48px 24px;
    background: #1a1a1a;
    border-radius: 12px;
  }

  .unixporn-widget__empty p {
    margin: 0;
    color: #fafafa;
  }

  .unixporn-widget__empty-hint {
    margin-top: 8px !important;
    color: #888 !important;
    font-size: 14px;
  }
`;

export default UnixpornWidget;
