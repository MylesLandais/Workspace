import os

content = r'''import { useState, useRef, useEffect } from "react";
import { FeedItem as FeedItemType, MediaType } from "@/lib/types/feed";
import { Heart, Play, Share2, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

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
  onClick,
  isNew = false,
  index = 0,
  isPlaceholder = false
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

    const initialHeight = cardRef.current.getBoundingClientRect().height;
    if (initialHeight > 0) {
      onHeightMeasured(item.id, initialHeight);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, [item.id, onHeightMeasured]);

  const isVideo = item.type === MediaType.VIDEO || item.type === MediaType.SHORT;

  const imageUrl =
    item.mediaUrl ||
    `https://picsum.photos/seed/${item.id}/${item.width}/${item.height}`;

  return (
    <div
      ref={cardRef}
      className={cn(
        "absolute group rounded-3xl overflow-hidden",
        isPlaceholder
          ? "bg-white/5 animate-pulse border-white/5"
          : "bg-white/5 backdrop-blur-sm border border-white/5 hover:border-white/20 hover:bg-white/10 hover:shadow-[0_20px_40px_rgba(0,0,0,0.4)] cursor-pointer"
      )}
      style={{
        width: columnWidth,
        left: x,
        top: y,
      }}
      onClick={() => onClick?.(item)}
      onMouseEnter={() => {
        setIsHovering(true);
        if (isVideo && videoRef) videoRef.play().catch(() => { });
      }}
      onMouseLeave={() => {
        setIsHovering(false);
        if (isVideo && videoRef) {
          videoRef.pause();
          videoRef.currentTime = 0;
        }
      }}
    >
      <div
        className={cn(
          "relative w-full overflow-hidden isolate bg-black/40",
          // Remove Tailwind aspect classes to use robust style-based aspect ratio
          "aspect-auto"
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
          {item.source.toLowerCase().includes('booru') && (
            <div className="p-2 rounded-xl bg-app-accent/80 backdrop-blur-md border border-white/10 text-black">
              <Sparkles className="w-3 h-3" />
            </div>
          )}
        </div>

        {isVideo && (
          <video
            ref={setVideoRef}
            src={item.mediaUrl}
            className={cn(
              "absolute inset-0 w-full h-full object-cover transform will-change-transform",
              "group-hover:scale-110 transition-transform duration-500 ease-out"
            )}
            muted
            loop
            playsInline
            preload="auto"
            onLoadedMetadata={() => {
              if (cardRef.current) {
                onHeightMeasured(item.id, cardRef.current.getBoundingClientRect().height);
              }
            }}
          />
        )}

        {!isVideo && (
          <img
            src={imageUrl}
            alt={item.caption}
            className={cn(
              "absolute inset-0 w-full h-full object-cover transform will-change-transform",
              "group-hover:scale-110 transition-transform duration-500 ease-out"
            )}
            loading="eager"
            decoding="async"
            onLoad={() => {
              if (cardRef.current) {
                onHeightMeasured(item.id, cardRef.current.getBoundingClientRect().height);
              }
            }}
          />
        )}

        {/* Dynamic Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
      </div>

      <div className="p-5 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-white/10 flex items-center justify-center text-[10px] font-black text-white/50 border border-white/5">
              {getSourceIcon(item.source)}
            </div>
            <span className="text-[10px] font-bold tracking-widest uppercase text-white/40">{item.source}</span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-white/40 hover:text-app-accent transition-colors">
              <Heart className="w-3.5 h-3.5" />
              <span className="text-[10px] font-bold">{formatNumber(item.likes)}</span>
            </div>
          </div>
        </div>

        <p className="text-sm text-white/80 font-medium leading-relaxed line-clamp-2">
          {item.caption}
        </p>

        <div className="flex items-center gap-3 mt-1 pt-3 border-t border-white/5">
          <div className="w-6 h-6 rounded-full overflow-hidden ring-1 ring-white/10">
            <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${item.author.handle}`} alt={item.author.handle} />
          </div>
          <div className="flex flex-col">
            <span className="text-[11px] font-bold text-white/90 leading-none">{item.author.name || item.author.handle}</span>
            <span className="text-[9px] font-medium text-white/30 tracking-tight">@{item.author.handle}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
'''

with open('/home/warby/Workspace/Bunny/app/client/src/components/feed/FeedItem.tsx', 'w') as f:
    f.write(content)
