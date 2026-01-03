"use client";

import { UserMenu } from "@/components/auth/UserMenu";
import { SearchBar } from "@/components/search/SearchBar";

interface FeedHeaderProps {
  itemCount: number;
}

export function FeedHeader({ itemCount }: FeedHeaderProps) {
  return (
    <header className="sticky top-0 z-50 bg-app-bg/60 backdrop-blur-2xl border-b border-white/5 py-4 px-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-app-accent to-app-accent-hover flex items-center justify-center shadow-lg shadow-app-accent/20">
            <span className="text-xl font-black text-black">B</span>
          </div>
          <h1 className="text-xl font-bold tracking-tight text-app-text hidden sm:block">
            Bunny
          </h1>
        </div>

        <SearchBar />

        <div className="hidden lg:flex items-center gap-4 text-sm text-app-muted font-medium">
          <span className="px-3 py-1 rounded-full bg-white/5 border border-white/5">
            {itemCount} items discovered
          </span>
          <UserMenu />
        </div>
        <div className="lg:hidden">
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
