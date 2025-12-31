"use client";

import { useState, useRef, useEffect } from "react";
import { FeedItem as FeedItemType, MediaType } from "@/lib/types/feed";
import { Heart, Play, Share2 } from "lucide-react";

interface FeedItemProps {
  item: FeedItemType;
  columnWidth: number;
  x: number;
  y: number;
  onHeightMeasured: (id: string, height: number) => void;
  onClick?: (item: FeedItemType) => void;
}

function getSourceIcon(source: string) {
  const s = source?.toLowerCase() || "";
  if (s.includes("instagram")) return <span className="text-[10px]">IG</span>;
  if (s.includes("twitter") || s.includes("x"))
    return <span className="text-[10px]">X</span>;
  if (s.includes("reddit")) return <span className="text-[10px] font-bold">r/</span>;
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
  onClick
}: FeedItemProps) {
  const [isHovering, setIsHovering] = useState(false);
  const [videoRef, setVideoRef] = useState<HTMLVideoElement | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!cardRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect.height > 0) {
          onHeightMeasured(item.id, entry.target.getBoundingClientRect().height);
        }
      }
    });

    resizeObserver.observe(cardRef.current);

    // Initial measurement
    const initialHeight = cardRef.current.getBoundingClientRect().height;
    if (initialHeight > 0) {
      onHeightMeasured(item.id, initialHeight);
    }

    return () => resizeObserver.disconnect();
  }, [item.id, onHeightMeasured]);

  const imageUrl =
    item.mediaUrl ||
    `https://picsum.photos/seed/${item.id}/${item.width}/${item.height}`;

  const isVideo = item.type === MediaType.VIDEO || item.type === MediaType.SHORT;

  const handleMouseEnter = () => {
    setIsHovering(true);
    if (isVideo && videoRef) {
      videoRef.play().catch(() => { });
    }
  };

  const handleMouseLeave = () => {
    setIsHovering(false);
    if (isVideo && videoRef) {
      videoRef.pause();
      videoRef.currentTime = 0;
    }
  };

  return (
    <div
      ref={cardRef}
      className="absolute group bg-app-surface rounded-xl overflow-hidden hover:shadow-[0_0_30px_rgba(0,0,0,0.4)] transition-all duration-300 border border-app-border hover:border-app-muted/50 cursor-pointer"
      style={{
        left: x,
        top: y,
        width: columnWidth,
        transition: 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), left 0.4s cubic-bezier(0.16, 1, 0.3, 1), top 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        willChange: 'transform, left, top',
      }}
      onClick={() => onClick?.(item)}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="relative w-full overflow-hidden">
        {isVideo && (
          <video
            ref={setVideoRef}
            src={imageUrl}
            className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-300 ${isHovering ? 'opacity-100' : 'opacity-0'}`}
            muted
            loop
            playsInline
            preload="metadata"
          />
        )}

        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imageUrl}
          alt={item.caption}
          className={`w-full h-auto object-cover transform transition-all duration-700 group-hover:scale-105 opacity-90 group-hover:opacity-100 ${isVideo && isHovering ? "opacity-0" : ""
            }`}
          loading="lazy"
          onLoad={() => {
            if (cardRef.current) {
              onHeightMeasured(item.id, cardRef.current.getBoundingClientRect().height);
            }
          }}
        />

        {/* Overlay Gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-app-bg/90 via-transparent to-transparent opacity-60 group-hover:opacity-90 transition-opacity duration-300 pointer-events-none" />
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-4 translate-y-2 group-hover:translate-y-0 transition-transform duration-300">
        <div className="flex items-center gap-2 mb-2">
          <div className="flex items-center gap-1 bg-app-bg/40 backdrop-blur-md px-2 py-0.5 rounded-full text-[10px] uppercase font-bold text-app-text border border-white/5">
            {getSourceIcon(item.source)}
            <span>{item.source}</span>
          </div>
        </div>

        <p className="text-sm text-app-text font-medium line-clamp-2 mb-3 drop-shadow-md leading-relaxed">
          {item.caption}
        </p>

        <div className="flex items-center justify-between text-app-muted text-[10px] border-t border-white/10 pt-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-75">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-app-accent flex items-center justify-center text-[8px] font-bold text-white uppercase shadow-inner">
              {item.author.name ? item.author.name[0] : "?"}
            </div>
            <span className="truncate max-w-[80px] hover:text-app-text cursor-pointer transition-colors font-semibold">
              {item.author.handle}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 hover:text-app-accent transition-colors cursor-pointer">
              <Heart className="w-3 h-3" />
              <span>{formatNumber(item.likes)}</span>
            </div>
            <Share2 className="w-3 h-3 hover:text-app-text transition-colors cursor-pointer" />
          </div>
        </div>
      </div>
    </div>
  );
}
