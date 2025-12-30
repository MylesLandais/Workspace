"use client";

import { useState } from "react";
import { FeedItem as FeedItemType, MediaType } from "@/lib/types/feed";
import { Heart, Play, Share2 } from "lucide-react";

interface FeedItemProps {
  item: FeedItemType;
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

export function FeedItem({ item, onClick }: FeedItemProps) {
  const [isHovering, setIsHovering] = useState(false);
  const [videoRef, setVideoRef] = useState<HTMLVideoElement | null>(null);

  const imageUrl =
    item.mediaUrl ||
    `https://picsum.photos/seed/${item.id}/${item.width}/${item.height}`;

  const isVideo = item.type === MediaType.VIDEO || item.type === MediaType.SHORT;

  const handleMouseEnter = () => {
    setIsHovering(true);
    if (isVideo && videoRef) {
      videoRef.play();
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
      className="break-inside-avoid mb-6 group relative bg-app-surface rounded-xl overflow-hidden hover:shadow-[0_0_20px_rgba(0,0,0,0.3)] transition-all duration-300 border border-app-border hover:border-app-muted/50 cursor-pointer"
      onClick={() => onClick?.(item)}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Media Layer */}
      <div className={`relative w-full overflow-hidden ${item.aspectRatio}`}>
        {/* Video Media */}
        {isVideo && (
          <video
            ref={setVideoRef}
            src={imageUrl}
            className="absolute inset-0 w-full h-full object-cover"
            muted
            loop
            playsInline
            preload="metadata"
          />
        )}

        {/* Image Media (fallback for videos or static images) */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imageUrl}
          alt={item.caption}
          className={`w-full h-full object-cover transform transition-transform duration-700 group-hover:scale-105 opacity-90 group-hover:opacity-100 ${
            isVideo && isHovering ? "opacity-0" : ""
          }`}
          loading="lazy"
        />

        {/* Type Indicators */}
        {item.type === MediaType.SHORT && !isHovering && (
          <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-md p-2 rounded-full border border-white/10">
            <Play className="w-3 h-3 text-white fill-white" />
          </div>
        )}
        {item.type === MediaType.GIF && (
          <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-md px-2 py-1 rounded text-[10px] font-bold tracking-wider border border-white/10">
            GIF
          </div>
        )}
        {item.type === MediaType.VIDEO && !isHovering && (
          <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-md p-2 rounded-full border border-white/10">
            <Play className="w-3 h-3 text-white fill-white" />
          </div>
        )}

        {/* Overlay Gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-app-bg/90 via-transparent to-transparent opacity-60 group-hover:opacity-90 transition-opacity duration-300" />
      </div>

      {/* Content Layer */}
      <div className="absolute bottom-0 left-0 right-0 p-4 translate-y-2 group-hover:translate-y-0 transition-transform duration-300">
        {/* Source Badge */}
        <div className="flex items-center gap-2 mb-2">
          <div className="flex items-center gap-1 bg-app-bg/40 backdrop-blur-md px-2 py-0.5 rounded-full text-xs text-app-text border border-white/5">
            {getSourceIcon(item.source)}
            <span>{item.source}</span>
          </div>
        </div>

        {/* Caption */}
        <p className="text-sm text-app-text font-medium line-clamp-2 mb-3 drop-shadow-md">
          {item.caption}
        </p>

        {/* Footer Metadata */}
        <div className="flex items-center justify-between text-app-muted text-xs border-t border-white/10 pt-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-75">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-app-accent flex items-center justify-center text-[8px] font-bold text-white uppercase">
              {item.author.name ? item.author.name[0] : "?"}
            </div>
            <span className="truncate max-w-[80px] hover:text-app-text cursor-pointer transition-colors">
              {item.author.handle}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 hover:text-app-accent transition-colors cursor-pointer">
              <Heart className="w-3.5 h-3.5" />
              <span>{formatNumber(item.likes)}</span>
            </div>
            <Share2 className="w-3.5 h-3.5 hover:text-app-text transition-colors cursor-pointer" />
          </div>
        </div>
      </div>
    </div>
  );
}
