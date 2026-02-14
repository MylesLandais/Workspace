/* eslint-disable @next/next/no-img-element */
import { useState, useRef, useEffect, useId } from "react";
import { FeedItem as FeedItemType, MediaType } from "@/lib/types/feed";
import { Heart, Play, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { RedditPostCard } from "@/components/reddit";
import { startSpan, endSpan, addSpanEvent } from "@/lib/tracing/tracer";

function CloverIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 36 36"
      fill="currentColor"
      className={className}
    >
      <path d="M32.551 18.852c-2.093-1.848-6.686-3.264-10.178-3.84 3.492-.577 8.085-1.993 10.178-3.839 2.014-1.776 2.963-2.948 2.141-4.722-.566-1.219-2.854-1.333-4.166-2.491C29.214 2.802 29.083.783 27.7.285c-2.01-.726-3.336.114-5.347 1.889-2.094 1.847-3.698 5.899-4.353 8.98-.653-3.082-2.258-7.134-4.351-8.98C11.634.397 10.308-.441 8.297.285c-1.383.5-1.512 2.518-2.823 3.675S1.872 5.234 1.308 6.454c-.823 1.774.129 2.943 2.14 4.718 2.094 1.847 6.688 3.263 10.181 3.84-3.493.577-8.087 1.993-10.181 3.84-2.013 1.775-2.963 2.945-2.139 4.721.565 1.219 2.854 1.334 4.166 2.49 1.311 1.158 1.444 3.178 2.827 3.676 2.009.727 3.336-.115 5.348-1.889 1.651-1.457 2.997-4.288 3.814-6.933-.262 4.535.528 10.591 3.852 14.262 1.344 1.483 2.407.551 2.822.187.416-.365 1.605-1.414.186-2.822-3.91-3.883-5.266-7.917-5.628-11.14.827 2.498 2.107 5.077 3.657 6.446 2.012 1.775 3.339 2.615 5.351 1.889 1.382-.5 1.512-2.52 2.822-3.676 1.312-1.158 3.602-1.273 4.166-2.494.822-1.774-.13-2.944-2.141-4.717z" />
    </svg>
  );
}

interface FeedItemProps {
  item: FeedItemType;
  columnWidth: number;
  x: number;
  y: number;
  onHeightMeasured: (id: string, height: number) => void;
  onClick?: (item: FeedItemType) => void;
  isNew?: boolean;
  index?: number;
  isPlaceholder?: boolean;
}

function getSourceIcon(source: string) {
  const s = source?.toLowerCase() || "";
  if (s.includes("imageboard")) return <CloverIcon className="w-3 h-3" />;
  if (s.includes("instagram")) return <span className="text-[10px]">IG</span>;
  if (s.includes("twitter") || s.includes("x"))
    return <span className="text-[10px]">X</span>;
  if (s.includes("reddit"))
    return <span className="text-[10px] font-bold">r/</span>;
  if (s.includes("tiktok")) return <span className="text-[10px]">TT</span>;
  if (s.includes("pinterest")) return <span className="text-[10px]">P</span>;
  return <span className="text-[10px]">W</span>;
}

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

export function FeedItem({
  item,
  columnWidth,
  x,
  y,
  onHeightMeasured,
  onClick,
  isPlaceholder = false,
}: FeedItemProps) {
  const [videoRef, setVideoRef] = useState<HTMLVideoElement | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const componentId = useId();

  const isImageboard = item.source.toLowerCase().includes("imageboard");
  const hasGallery = item.galleryUrls && item.galleryUrls.length > 0;
  const shouldRotate = isImageboard && hasGallery;

  useEffect(() => {
    const span = startSpan(`feed.card.${componentId}`);
    addSpanEvent(span, "card.render", {
      itemId: item.id,
      source: item.source,
      type: item.type,
      isPlaceholder: isPlaceholder ? 1 : 0,
      hasGallery: hasGallery ? 1 : 0,
      columnWidth,
      x,
      y,
    });
    return () => endSpan(span);
  }, [componentId]);

  useEffect(() => {
    if (!cardRef.current) return;

    const resizeSpan = startSpan(`feed.card.${componentId}.resizeObserver`);
    let callbackCount = 0;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect.height > 0) {
          callbackCount++;
          const height = entry.target.getBoundingClientRect().height;
          onHeightMeasured(item.id, height);

          if (callbackCount <= 5) {
            addSpanEvent(resizeSpan, "resize_callback", {
              callbackNumber: callbackCount,
              height,
              width: entry.contentRect.width,
            });
          }
        }
      }
    });

    resizeObserver.observe(cardRef.current);

    const initialHeight = cardRef.current.getBoundingClientRect().height;
    if (initialHeight > 0) {
      onHeightMeasured(item.id, initialHeight);
      addSpanEvent(resizeSpan, "initial_height_measured", {
        height: initialHeight,
      });
    }

    return () => {
      addSpanEvent(resizeSpan, "resize_observer_cleanup", {
        totalCallbacks: callbackCount,
      });
      endSpan(resizeSpan);
      resizeObserver.disconnect();
    };
  }, [item.id, onHeightMeasured, componentId]);

  useEffect(() => {
    if (!shouldRotate || !isHovered) return;

    const rotationSpan = startSpan(`feed.card.${componentId}.galleryRotation`);
    let rotationCount = 0;

    const maxImages = Math.min(5, item.galleryUrls!.length);
    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % maxImages);
      rotationCount++;

      addSpanEvent(rotationSpan, "gallery_rotate", {
        rotationNumber: rotationCount,
        imageIndex: rotationCount % maxImages,
        imageUrl: item.galleryUrls![rotationCount % maxImages],
      });
    }, 2500);

    return () => {
      addSpanEvent(rotationSpan, "gallery_rotation_cleanup", {
        totalRotations: rotationCount,
      });
      endSpan(rotationSpan);
      clearInterval(interval);
    };
  }, [shouldRotate, item.galleryUrls, isHovered, componentId]);

  const isVideo =
    item.type === MediaType.VIDEO || item.type === MediaType.SHORT;
  const isReddit = item.source.toLowerCase() === "reddit" && !!item.redditData;

  const imageUrl =
    shouldRotate && item.galleryUrls
      ? item.galleryUrls[currentImageIndex]
      : item.presignedUrl || item.mediaUrl || "";

  return (
    <div
      ref={cardRef}
      className={cn(
        "absolute group rounded-3xl overflow-hidden",
        isPlaceholder
          ? "bg-white/5 animate-pulse border-white/5"
          : "bg-white/5 backdrop-blur-sm border border-white/5 hover:border-white/20 hover:bg-white/10 hover:shadow-[0_20px_40px_rgba(0,0,0,0.4)] cursor-pointer",
      )}
      style={{
        width: columnWidth,
        left: x,
        top: y,
      }}
      onClick={() => {
        const clickSpan = startSpan(`feed.card.${componentId}.click`);
        addSpanEvent(clickSpan, "card.clicked", {
          itemId: item.id,
          source: item.source,
          type: item.type,
          hasGallery: hasGallery ? 1 : 0,
        });
        endSpan(clickSpan);
        onClick?.(item);
      }}
      onMouseEnter={() => {
        setIsHovered(true);
        const hoverSpan = startSpan(`feed.card.${componentId}.hover`);
        addSpanEvent(hoverSpan, "card.hover_start", {
          itemId: item.id,
          isVideo: isVideo ? 1 : 0,
          shouldRotate: shouldRotate ? 1 : 0,
        });
        endSpan(hoverSpan);

        if (isVideo && videoRef) videoRef.play().catch(() => {});
      }}
      onMouseLeave={() => {
        setIsHovered(false);
        setCurrentImageIndex(0);
        const hoverEndSpan = startSpan(`feed.card.${componentId}.hoverEnd`);
        addSpanEvent(hoverEndSpan, "card.hover_end", {
          itemId: item.id,
          finalImageIndex: currentImageIndex,
        });
        endSpan(hoverEndSpan);

        if (isVideo && videoRef) {
          videoRef.pause();
          videoRef.currentTime = 0;
        }
      }}
    >
      {isReddit ? (
        <RedditPostCard
          post={item.redditData!}
          variant="compact"
          className="border-none bg-transparent hover:shadow-none"
        />
      ) : (
        <>
          <div
            className={cn(
              "relative w-full overflow-hidden isolate bg-black/40",
              // Remove Tailwind aspect classes to use robust style-based aspect ratio
              "aspect-auto",
            )}
            style={{
              aspectRatio: `${item.width} / ${item.height}`,
              // Robust Firefox fallback: padding-bottom hack combined with aspect-ratio
              // paddingBottom: `${(item.height / item.width) * 100}%`
              // Note: Object-cover works better with aspect-ratio in modern FF
            }}
          >
            {/* Type Badge */}
            <div className="absolute top-4 right-4 z-20 flex gap-2">
              {isVideo && (
                <div className="p-2 rounded-xl bg-black/40 backdrop-blur-md border border-white/10 text-white">
                  <Play className="w-3 h-3 fill-current" />
                </div>
              )}
              {item.source.toLowerCase().includes("booru") && (
                <div className="p-2 rounded-xl bg-app-accent/80 backdrop-blur-md border border-white/10 text-black">
                  <Sparkles className="w-3 h-3" />
                </div>
              )}
            </div>

            {isVideo && (
              <video
                key={`video-${item.id}`}
                ref={setVideoRef}
                src={item.mediaUrl}
                className={cn(
                  "absolute inset-0 w-full h-full object-cover transform will-change-transform",
                  "group-hover:scale-110 transition-transform duration-500 ease-out",
                )}
                muted
                loop
                playsInline
                preload="auto"
                onLoadedMetadata={() => {
                  const loadSpan = startSpan(
                    `feed.card.${componentId}.videoLoaded`,
                  );
                  if (cardRef.current) {
                    onHeightMeasured(
                      item.id,
                      cardRef.current.getBoundingClientRect().height,
                    );
                  }
                  addSpanEvent(loadSpan, "video.loaded_metadata", {
                    itemId: item.id,
                    mediaUrl: item.mediaUrl || "",
                    cardHeight:
                      cardRef.current?.getBoundingClientRect().height || 0,
                  });
                  endSpan(loadSpan);
                }}
                onError={(e) => {
                  const errorSpan = startSpan(
                    `feed.card.${componentId}.videoError`,
                  );
                  addSpanEvent(errorSpan, "video.error", {
                    itemId: item.id,
                    mediaUrl: item.mediaUrl || "",
                    error:
                      (e.target as HTMLVideoElement).error?.message ||
                      "Unknown video error",
                  });
                  endSpan(errorSpan);
                }}
              />
            )}

            {!isVideo && (
              <img
                key={`img-${item.id}-${currentImageIndex}`}
                src={imageUrl}
                alt={item.caption}
                className={cn(
                  "absolute inset-0 w-full h-full object-cover transform will-change-transform",
                  "group-hover:scale-110 transition-transform duration-500 ease-out",
                )}
                loading="eager"
                decoding="async"
                onLoad={(e) => {
                  const loadSpan = startSpan(
                    `feed.card.${componentId}.imageLoaded`,
                  );
                  const img = e.target as HTMLImageElement;

                  if (cardRef.current) {
                    onHeightMeasured(
                      item.id,
                      cardRef.current.getBoundingClientRect().height,
                    );
                  }

                  addSpanEvent(loadSpan, "image.loaded", {
                    itemId: item.id,
                    imageUrl: imageUrl.substring(0, 200),
                    currentImageIndex,
                    isGallery: !!item.galleryUrls ? 1 : 0,
                    naturalWidth: img.naturalWidth,
                    naturalHeight: img.naturalHeight,
                    aspectRatio: `${img.naturalWidth}/${img.naturalHeight}`,
                    loadingStrategy: "eager",
                    decodingStrategy: "async",
                  });
                  endSpan(loadSpan);
                }}
                onError={(e) => {
                  const errorSpan = startSpan(
                    `feed.card.${componentId}.imageError`,
                  );
                  addSpanEvent(errorSpan, "image.error", {
                    itemId: item.id,
                    imageUrl: imageUrl.substring(0, 200),
                    currentImageIndex,
                    error:
                      (e.target as HTMLImageElement).naturalWidth === 0
                        ? "Image failed to load (naturalWidth = 0)"
                        : "Unknown image error",
                  });
                  endSpan(errorSpan);
                }}
              />
            )}

            {/* Dynamic Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

            {/* Gallery rotation indicator for imageboard */}
            {shouldRotate && isHovered && (
              <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1 transition-opacity">
                {Array.from({
                  length: Math.min(5, item.galleryUrls!.length),
                }).map((_, i) => (
                  <div
                    key={i}
                    className={cn(
                      "w-1 h-1 rounded-full transition-colors",
                      i === currentImageIndex ? "bg-white" : "bg-white/40",
                    )}
                  />
                ))}
              </div>
            )}
          </div>

          <div className="p-5 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className={cn(
                    "w-6 h-6 rounded-lg flex items-center justify-center text-[10px] font-black border",
                    item.source.toLowerCase().includes("imageboard")
                      ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                      : "bg-white/10 text-white/50 border-white/5",
                  )}
                >
                  {getSourceIcon(item.source)}
                </div>
                <span className="text-[10px] font-bold tracking-widest uppercase text-white/40">
                  {item.source}
                </span>
              </div>

              <div className="flex items-center gap-3">
                {item.source.toLowerCase().includes("imageboard") ? (
                  <div className="flex items-center gap-1.5 text-white/40">
                    <span className="text-[10px] font-bold">
                      R: {formatNumber(item.replyCount || 0)} / I:{" "}
                      {formatNumber(item.imageCount || 0)}
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 text-white/40 hover:text-app-accent transition-colors">
                    <Heart className="w-3.5 h-3.5" />
                    <span className="text-[10px] font-bold">
                      {formatNumber(item.likes)}
                    </span>
                  </div>
                )}
              </div>
            </div>

            <p className="text-sm text-white/80 font-medium leading-relaxed line-clamp-2">
              {item.caption}
            </p>

            <div className="flex items-center gap-3 mt-1 pt-3 border-t border-white/5">
              {item.source.toLowerCase().includes("imageboard") ? (
                <div className="flex flex-col">
                  <span className="text-[11px] font-bold text-white/90 leading-none">
                    Anonymous
                  </span>
                  <span className="text-[9px] font-medium text-white/30 tracking-tight">
                    No ID
                  </span>
                </div>
              ) : (
                <>
                  <div className="w-6 h-6 rounded-full overflow-hidden ring-1 ring-white/10">
                    <img
                      src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${item.author.handle}`}
                      alt={item.author.handle}
                    />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[11px] font-bold text-white/90 leading-none">
                      {item.author.name || item.author.handle}
                    </span>
                    <span className="text-[9px] font-medium text-white/30 tracking-tight">
                      @{item.author.handle}
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
