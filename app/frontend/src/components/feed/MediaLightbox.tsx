import React, { useEffect } from 'react';
import { type Media } from '../../lib/utils/deduplicate';

interface MediaLightboxProps {
  isOpen: boolean;
  media: Media | null;
  onClose: () => void;
  onNext?: () => void;
  onPrevious?: () => void;
  hasNext?: boolean;
  hasPrevious?: boolean;
}

export default function MediaLightbox({ isOpen, media, onClose, onNext, onPrevious, hasNext, hasPrevious }: MediaLightboxProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowRight' && hasNext && onNext) {
        onNext();
      } else if (e.key === 'ArrowLeft' && hasPrevious && onPrevious) {
        onPrevious();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, hasNext, hasPrevious, onNext, onPrevious, onClose]);

  if (!isOpen || !media) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-w-4xl max-h-[90vh] bg-theme-bg-secondary border border-theme-border-primary rounded-lg overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 bg-theme-bg-primary hover:bg-theme-bg-primary/80 rounded-lg text-theme-text-primary transition-colors"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        {onPrevious && hasPrevious && (
          <button
            onClick={onPrevious}
            className="absolute left-4 top-1/2 -translate-y-1/2 z-10 p-3 bg-theme-bg-primary hover:bg-theme-bg-primary/80 rounded-lg text-theme-text-primary transition-colors"
            aria-label="Previous"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        )}

        {onNext && hasNext && (
          <button
            onClick={onNext}
            className="absolute right-4 top-1/2 -translate-y-1/2 z-10 p-3 bg-theme-bg-primary hover:bg-theme-bg-primary/80 rounded-lg text-theme-text-primary transition-colors"
            aria-label="Next"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        )}

        <div className="p-6">
          <img
            src={media.imageUrl}
            alt={media.title}
            className="w-full h-auto max-h-[70vh] object-contain rounded-lg"
          />
          
          <div className="mt-4">
            <h2 className="text-xl font-bold text-theme-text-primary mb-2">{media.title}</h2>
            <div className="flex items-center space-x-4 text-sm text-theme-text-secondary">
              {media.subreddit && (
                <span>r/{media.subreddit.name}</span>
              )}
              {media.author && (
                <span>by {media.author.username}</span>
              )}
              {media.handle.creatorName && (
                <span className="text-theme-accent-tertiary">{media.handle.creatorName}</span>
              )}
              {media.score && (
                <span>{media.score.toLocaleString()} points</span>
              )}
            </div>
            <a
              href={media.sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-block px-4 py-2 bg-theme-accent-primary hover:bg-theme-accent-primary/90 text-theme-bg-primary rounded-lg font-medium transition-colors"
            >
              View Original
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
