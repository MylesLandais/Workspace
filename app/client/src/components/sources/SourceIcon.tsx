"use client";

import { SourceType } from "@/lib/types/sources";

interface SourceIconProps {
  sourceType: SourceType;
  iconUrl?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "w-4 h-4",
  md: "w-5 h-5",
  lg: "w-6 h-6",
};

const platformColors: Record<SourceType, string> = {
  [SourceType.RSS]: "bg-orange-500",
  [SourceType.REDDIT]: "bg-orange-600",
  [SourceType.YOUTUBE]: "bg-red-600",
  [SourceType.TWITTER]: "bg-sky-500",
  [SourceType.INSTAGRAM]: "bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400",
  [SourceType.TIKTOK]: "bg-black",
  [SourceType.VSCO]: "bg-neutral-800",
  [SourceType.IMAGEBOARD]: "bg-green-600",
};

const platformIcons: Record<SourceType, React.ReactNode> = {
  [SourceType.RSS]: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-3 h-3">
      <circle cx="6" cy="18" r="3" />
      <path d="M4 4a16 16 0 0 1 16 16h-4A12 12 0 0 0 4 8V4z" />
      <path d="M4 10a10 10 0 0 1 10 10h-4a6 6 0 0 0-6-6v-4z" />
    </svg>
  ),
  [SourceType.REDDIT]: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-3 h-3">
      <circle cx="9" cy="12" r="1.5" />
      <circle cx="15" cy="12" r="1.5" />
      <path d="M12 16c-2 0-3.5-1-4-2h8c-.5 1-2 2-4 2z" />
      <path d="M22 12c0 5.5-4.5 10-10 10S2 17.5 2 12 6.5 2 12 2s10 4.5 10 10z" />
    </svg>
  ),
  [SourceType.YOUTUBE]: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-3 h-3">
      <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z" />
    </svg>
  ),
  [SourceType.TWITTER]: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-3 h-3">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  ),
  [SourceType.INSTAGRAM]: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-3 h-3">
      <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
    </svg>
  ),
  [SourceType.TIKTOK]: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-3 h-3">
      <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z" />
    </svg>
  ),
  [SourceType.VSCO]: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-3 h-3">
      <path d="M12 0C5.376 0 0 5.376 0 12s5.376 12 12 12 12-5.376 12-12S18.624 0 12 0zm7.2 17.52c-.528.672-2.592 2.4-5.616 2.4H8.712c-.528 0-.864-.192-1.056-.576-.144-.288-.144-.72.048-1.056l2.688-5.52c.144-.288.048-.672-.24-.864-.288-.144-.672-.048-.864.24l-3.552 5.808c-.192.288-.528.528-.912.576-.384.048-.768-.096-1.008-.384-.528-.672-2.4-2.592-2.4-5.616V10.8c0-.528.192-.864.576-1.056.288-.144.72-.144 1.056.048l5.52 2.688c.288.144.672.048.864-.24.144-.288.048-.672-.24-.864L3.384 7.824c-.288-.192-.528-.528-.576-.912-.048-.384.096-.768.384-1.008C3.864 5.376 5.928 3.6 8.952 3.6h1.776c.528 0 .864.192 1.056.576.144.288.144.72-.048 1.056l-2.688 5.52c-.144.288-.048.672.24.864.288.144.672.048.864-.24l3.552-5.808c.192-.288.528-.528.912-.576.384-.048.768.096 1.008.384.528.672 2.4 2.592 2.4 5.616v1.776c0 .528-.192.864-.576 1.056-.288.144-.72.144-1.056-.048l-5.52-2.688c-.288-.144-.672-.048-.864.24-.144.288-.048.672.24.864l5.808 3.552c.288.192.528.528.576.912.048.384-.096.768-.384 1.008z" />
    </svg>
  ),
  [SourceType.IMAGEBOARD]: (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-3 h-3">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  ),
};

export function SourceIcon({
  sourceType,
  iconUrl,
  size = "md",
  className = "",
}: SourceIconProps) {
  const sizeClass = sizeClasses[size];

  if (iconUrl) {
    return (
      <img
        src={iconUrl}
        alt=""
        className={`${sizeClass} rounded object-cover ${className}`}
      />
    );
  }

  return (
    <div
      className={`${sizeClass} ${platformColors[sourceType]} rounded flex items-center justify-center text-white ${className}`}
    >
      {platformIcons[sourceType]}
    </div>
  );
}
