"use client";

import { Search, SlidersHorizontal, X } from "lucide-react";
import { useSearchStore } from "@/lib/store/search-store";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

export function SearchBar() {
    const { filters, setQuery, toggleFilters, isFiltersOpen, setCategories, setTags, resetFilters } = useSearchStore();

    return (
        <div className="relative w-full max-w-2xl mx-auto z-50">
            <div className={cn(
                "group relative flex items-center w-full h-14 px-4 rounded-2xl transition-all duration-300",
                "bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl",
                "focus-within:bg-white/15 focus-within:border-white/30 focus-within:ring-4 focus-within:ring-white/5"
            )}>
                <Search className="w-5 h-5 text-white/40 group-focus-within:text-white/70 transition-colors" />

                <input
                    type="text"
                    value={filters.query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search across your universe..."
                    className="flex-1 h-full bg-transparent border-none focus:ring-0 text-white placeholder:text-white/30 text-lg px-4"
                />

                <div className="flex items-center gap-2">
                    {filters.query && (
                        <button
                            onClick={() => setQuery("")}
                            className="p-1.5 rounded-lg hover:bg-white/10 text-white/40 hover:text-white/70 transition-all"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    )}

                    <div className="w-[1px] h-6 bg-white/10 mx-1" />

                    <button
                        onClick={toggleFilters}
                        className={cn(
                            "flex items-center gap-2 px-3 py-1.5 rounded-xl transition-all duration-300",
                            isFiltersOpen
                                ? "bg-white text-black shadow-[0_0_20px_rgba(255,255,255,0.3)]"
                                : "hover:bg-white/10 text-white/70 hover:text-white"
                        )}
                    >
                        <SlidersHorizontal className="w-4 h-4" />
                        <span className="text-sm font-medium">Filters</span>
                        {filters.categories.length + filters.tags.length > 0 && (
                            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-white/20 text-[10px] font-bold">
                                {filters.categories.length + filters.tags.length}
                            </span>
                        )}
                    </button>
                </div>
            </div>

            <AnimatePresence>
                {isFiltersOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        className="absolute top-full left-0 right-0 mt-4 p-6 rounded-3xl bg-black/60 backdrop-blur-3xl border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] z-40"
                    >
                        <div className="grid grid-cols-2 gap-8 mb-6">
                            <div>
                                <h3 className="text-xs uppercase tracking-widest text-white/40 font-bold mb-4 flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-app-accent" />
                                    Categories
                                </h3>
                                <div className="flex flex-wrap gap-2">
                                    {['Image', 'Video', 'Article'].map(cat => (
                                        <FilterTag
                                            key={cat}
                                            label={cat}
                                            active={filters.categories.includes(cat)}
                                            onClick={() => {
                                                const next = filters.categories.includes(cat)
                                                    ? filters.categories.filter(c => c !== cat)
                                                    : [...filters.categories, cat];
                                                setCategories(next);
                                            }}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div>
                                <h3 className="text-xs uppercase tracking-widest text-white/40 font-bold mb-4 flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                                    Quick Tags
                                </h3>
                                <div className="flex flex-wrap gap-2">
                                    {['Unread', 'Favorites', 'Archived'].map(tag => (
                                        <FilterTag
                                            key={tag}
                                            label={tag}
                                            active={filters.tags.includes(tag)}
                                            onClick={() => {
                                                const next = filters.tags.includes(tag)
                                                    ? filters.tags.filter(t => t !== tag)
                                                    : [...filters.tags, tag];
                                                setTags(next);
                                            }}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center justify-between pt-4 border-t border-white/5">
                            <span className="text-[10px] text-white/20 font-medium">Fine-tune your browsing experience</span>
                            <button
                                onClick={resetFilters}
                                className="text-[10px] font-bold text-app-accent hover:text-white transition-colors"
                            >
                                Clear All
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

function FilterTag({ label, active, onClick }: { label: string, active: boolean, onClick: () => void }) {
    return (
        <button
            onClick={onClick}
            className={cn(
                "px-4 py-2 rounded-full text-xs font-bold transition-all duration-300 border",
                active
                    ? "bg-white text-black border-white shadow-[0_0_15px_rgba(255,255,255,0.2)]"
                    : "bg-white/5 text-white/60 border-white/5 hover:border-white/20 hover:bg-white/10"
            )}
        >
            {label}
        </button>
    );
}
