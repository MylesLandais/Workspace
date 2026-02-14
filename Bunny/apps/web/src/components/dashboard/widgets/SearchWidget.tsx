"use client";

import React, { useState } from "react";
import { Search } from "lucide-react";

interface SearchWidgetProps {
  content: string;
}

const SearchWidget: React.FC<SearchWidgetProps> = ({
  content: initialQuery,
}) => {
  const [query, setQuery] = useState(initialQuery || "");

  return (
    <div className="h-full flex flex-col p-4 bg-white dark:bg-industrial-900">
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-industrial-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search..."
            className="w-full pl-10 pr-4 py-2 bg-industrial-50 dark:bg-industrial-950 border border-industrial-200 dark:border-industrial-700 rounded text-sm text-industrial-900 dark:text-white placeholder:text-industrial-400 focus:outline-none focus:ring-2 focus:ring-matcha-500"
          />
        </div>
      </div>
      <div className="flex-1 flex items-center justify-center text-industrial-400">
        <p className="text-sm">Search functionality pending</p>
      </div>
    </div>
  );
};

export default SearchWidget;
