import React, { useState, useEffect, useCallback } from 'react';
import { X, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';
import { FeedItem as FeedItemType } from '../../lib/bunny/types';

interface LightboxProps {
  item: FeedItemType;
  onClose: () => void;
}

export const Lightbox: React.FC<LightboxProps> = ({ item, onClose }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const images = item.galleryUrls && item.galleryUrls.length > 0 
    ? item.galleryUrls 
    : [item.mediaUrl || `https://picsum.photos/seed/${item.id}/${item.width}/${item.height}`];

  const handlePrev = useCallback(() => {
    setCurrentIndex(prev => prev === 0 ? images.length - 1 : prev - 1);
  }, [images.length]);

  const handleNext = useCallback(() => {
    setCurrentIndex(prev => prev === images.length - 1 ? 0 : prev + 1);
  }, [images.length]);

  const handleImageLoad = () => {
    setIsLoading(false);
  };

  const handleImageChange = () => {
    setIsLoading(true);
  };

  useEffect(() => {
    handleImageChange();
  }, [currentIndex]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowLeft') handlePrev();
      if (e.key === 'ArrowRight') handleNext();
    };

    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [onClose, handlePrev, handleNext]);

  const currentImage = images[currentIndex];

  return (
    <div 
      className="fixed inset-0 z-50 bg-black/95 backdrop-blur-sm flex items-center justify-center"
      onClick={onClose}
    >
      {/* Close Button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 z-10 p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors text-white"
        title="Close (Esc)"
      >
        <X className="w-6 h-6" />
      </button>

      {/* Navigation Buttons */}
      {images.length > 1 && (
        <>
          <button
            onClick={(e) => { e.stopPropagation(); handlePrev(); }}
            className="absolute left-4 top-1/2 -translate-y-1/2 z-10 p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors text-white"
            title="Previous (←)"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); handleNext(); }}
            className="absolute right-4 top-1/2 -translate-y-1/2 z-10 p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors text-white"
            title="Next (→)"
          >
            <ChevronRight className="w-6 h-6" />
          </button>
        </>
      )}

      {/* Image Counter */}
      {images.length > 1 && (
        <div className="absolute top-4 left-4 z-10 px-3 py-1 bg-black/50 backdrop-blur-md rounded-full text-white text-sm font-medium">
          {currentIndex + 1} / {images.length}
        </div>
      )}

      {/* Image Container */}
      <div 
        className="relative max-w-[90vw] max-h-[90vh] flex items-center justify-center"
        onClick={(e) => e.stopPropagation()}
      >
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-12 h-12 border-4 border-white/20 border-t-white rounded-full animate-spin" />
          </div>
        )}
        
        <img
          src={currentImage}
          alt={item.caption}
          onLoad={handleImageLoad}
          className={`max-w-full max-h-[90vh] object-contain transition-opacity duration-300 ${isLoading ? 'opacity-0' : 'opacity-100'}`}
        />
      </div>

      {/* Caption Overlay */}
      <div 
        className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/50 to-transparent p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="max-w-4xl mx-auto">
          <h3 className="text-white text-lg font-medium mb-2">{item.caption}</h3>
          <div className="flex items-center gap-4 text-white/70 text-sm">
            <span>By {item.author.name}</span>
            <span>•</span>
            <span>{new Date(item.timestamp).toLocaleDateString()}</span>
            {item.permalink && (
              <>
                <span>•</span>
                <a
                  href={item.permalink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 hover:text-white transition-colors"
                  onClick={(e) => e.stopPropagation()}
                >
                  <ExternalLink className="w-3 h-3" />
                  View Source
                </a>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
