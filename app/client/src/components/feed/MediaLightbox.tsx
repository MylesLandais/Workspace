"use client";

import { lazy, Suspense, useEffect, useState, useCallback } from "react";
import type { Slide } from "yet-another-react-lightbox";
import type { FeedItem as FeedItemType, MediaType } from "@/lib/types/feed";
import { useLightboxStore } from "@/lib/store/lightbox-store";
import { LightboxCommentsSidebar } from "./LightboxCommentsSidebar";
import Zoom from "yet-another-react-lightbox/plugins/zoom";
import Fullscreen from "yet-another-react-lightbox/plugins/fullscreen";
import Captions from "yet-another-react-lightbox/plugins/captions";
import Video from "yet-another-react-lightbox/plugins/video";
import Thumbnails from "yet-another-react-lightbox/plugins/thumbnails";

import "yet-another-react-lightbox/styles.css";
import "yet-another-react-lightbox/plugins/captions.css";
import "yet-another-react-lightbox/plugins/thumbnails.css";

const Lightbox = lazy(() => import("yet-another-react-lightbox"));

interface MediaLightboxProps {
  items?: FeedItemType[];
  currentIndex?: number;
  isOpen?: boolean;
  onClose?: () => void;
  onIndexChange?: (index: number) => void;
}

interface SlideWithMetadata extends Slide {
  feedItemId?: string;
  isReddit?: boolean;
}

function getFilename(url: string): string {
  const match = url.match(/\/([^/]+\.(jpg|jpeg|png|webm|gif|mp4))$/i);
  return match ? match[1] : "";
}

function feedItemToSlides(item: FeedItemType): SlideWithMetadata[] {
  const isVideo = item.type === "video" || item.type === "short";
  const isImageboard = item.source.toLowerCase().includes("imageboard");
  const metaInfo = isImageboard
    ? `/${(item.tags?.find(t => /^[a-z]$/.test(t)) || "b")}/ | ${item.tags?.find(t => /\d+ images/.test(t)) || ""}`
    : `by ${item.author.name || item.author.handle} | ${item.source} | ${item.likes} likes${item.tags?.length ? ` | ${item.tags.join(", ")}` : ""}`;

  // Handle multi-image galleries (imageboard threads, etc.)
  if (item.galleryUrls && item.galleryUrls.length > 1) {
    return item.galleryUrls.map((url, index) => ({
      type: "image",
      src: url,
      width: item.width,
      height: item.height,
      title: item.caption,
      description: `${index + 1} / ${item.galleryUrls!.length}${isImageboard ? ` | ${getFilename(url)}` : ""} | ${metaInfo}`,
      alt: `${item.caption} - Image ${index + 1}`,
      feedItemId: item.id,
      isReddit: item.source.toLowerCase() === "reddit" && !!item.redditData,
    }));
  }

  // Single media item
  if (isVideo && item.mediaUrl) {
    const filename = getFilename(item.mediaUrl);
    return [
      {
        type: "video",
        poster: item.thumbnailUrl || item.mediaUrl,
        width: item.width,
        height: item.height,
        sources: [{ src: item.mediaUrl, type: "video/mp4" }],
        title: item.caption,
        description: (isImageboard && filename ? `${filename} | ` : "") + (item.tags?.join(", ") || metaInfo),
        feedItemId: item.id,
        isReddit: item.source.toLowerCase() === "reddit" && !!item.redditData,
      },
    ];
  }

  const filename = getFilename(item.mediaUrl || "");
  return [
    {
      type: "image",
      src: item.mediaUrl || "",
      width: item.width,
      height: item.height,
      title: item.caption,
      description: (isImageboard && filename ? `${filename} | ` : "") + (item.tags?.join(", ") || metaInfo),
      alt: item.caption,
      feedItemId: item.id,
      isReddit: item.source.toLowerCase() === "reddit" && !!item.redditData,
    },
  ];
}

function MediaLightboxContent({
  items: propItems,
  currentIndex: propIndex,
  isOpen: propIsOpen,
  onClose: propOnClose,
}: MediaLightboxProps) {
  const store = useLightboxStore();

  // Support both store-connected and props-based usage
  const isOpen = propIsOpen !== undefined ? propIsOpen : store.isOpen;
  const slideIndex = propIndex !== undefined ? propIndex : store.slideIndex;
  const items = propItems !== undefined ? propItems : store.items;
  const onClose = propOnClose !== undefined ? propOnClose : store.closeLightbox;
  const redditThreadData = store.redditThreadData;
  const isLoadingThread = store.isLoadingThread;

  const [showComments, setShowComments] = useState(false);

  // Flatten all slides from all items (handles multi-image galleries)
  const slides = items.flatMap(feedItemToSlides);

  // Map slide index back to item to check for Reddit data
  const getItemFromSlideIndex = (sIndex: number) => {
    let slideCount = 0;
    for (const item of items) {
      const itemSlideCount =
        item.galleryUrls && item.galleryUrls.length > 1 ? item.galleryUrls.length : 1;
      if (sIndex < slideCount + itemSlideCount) {
        return item;
      }
      slideCount += itemSlideCount;
    }
    return items[0];
  };

  const currentItem = getItemFromSlideIndex(slideIndex);
  const currentRedditPost = currentItem?.redditData;
  const threadData = currentRedditPost ? redditThreadData[currentRedditPost.id] : null;
  const threadLoading = currentRedditPost ? isLoadingThread[currentRedditPost.id] : false;

  // Handle custom keyboard shortcuts (lightbox handles arrow keys internally)
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      } else if (e.key === "c" || e.key === "C") {
        if (currentRedditPost) {
          setShowComments((prev) => !prev);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, currentRedditPost, onClose]);

  // Prevent body scroll when lightbox is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
      setShowComments(false);
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/95">
      <Lightbox
        open={isOpen}
        close={onClose}
        slides={slides}
        index={slideIndex}
        on={{
          view: ({ index }) => store.setSlideIndex(index),
        }}
        plugins={[Zoom, Fullscreen, Captions, Video, Thumbnails]}
        zoom={{
          maxZoomPixelRatio: 3,
          zoomInMultiplier: 2,
          scrollToZoom: true,
          doubleClickMaxStops: 2,
        }}
        fullscreen={{
          auto: false,
        }}
        captions={{
          descriptionTextAlign: "start",
          descriptionMaxLines: 3,
        }}
        thumbnails={{
          position: "bottom",
          width: 100,
          height: 70,
          border: 0,
          borderRadius: 8,
          gap: 8,
          padding: 16,
          vignette: true,
        }}
        carousel={{
          finite: false,
          preload: 2,
        }}
        animation={{
          fade: 0,
          swipe: 0,
        }}
        render={{
          buttonPrev: () => null,
          buttonNext: () => null,
        }}
        controller={{
          closeOnBackdropClick: true,
          closeOnPullDown: true,
          closeOnPullUp: true,
        }}
      />

      {/* Comments Sidebar for Reddit Posts */}
      {currentRedditPost && showComments && threadData && (
        <div className="absolute inset-y-0 right-0 w-96 max-w-[40vw] bg-gradient-to-l from-black/90 to-black/60">
          <LightboxCommentsSidebar
            post={currentRedditPost}
            comments={threadData.comments || []}
            isLoading={threadLoading}
          />
        </div>
      )}

      {/* Keyboard Help Hint for Reddit Posts */}
      {currentRedditPost && (
        <div className="absolute bottom-4 left-4 text-xs text-white/40 pointer-events-none">
          <kbd className="px-2 py-1 rounded bg-white/5 border border-white/10 mr-2">C</kbd>
          <span>Comments</span>
        </div>
      )}
    </div>
  );
}

export function MediaLightbox(props: MediaLightboxProps) {
  return (
    <Suspense fallback={null}>
      <MediaLightboxContent {...props} />
    </Suspense>
  );
}
