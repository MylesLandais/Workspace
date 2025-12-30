import React, { useState } from 'react';

export default function AIInsights() {
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
    }, 2000);
  };

  return (
    <div className="bg-theme-bg-secondary border border-theme-border-primary rounded-xl p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-theme-accent-secondary flex items-center justify-center">
              <svg
                className="w-6 h-6 text-theme-accent-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-theme-text-primary">AI Insights</h3>
          </div>
          <p className="text-sm text-theme-text-secondary">
            Generate a concise executive summary of repost trends and cluster growth.
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="ml-4 px-6 py-2 bg-theme-accent-primary hover:bg-theme-accent-primary/90 text-theme-bg-primary rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {isGenerating ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-theme-bg-primary"></div>
              <span>Generating...</span>
            </>
          ) : (
            <span>Generate Analysis</span>
          )}
        </button>
      </div>
    </div>
  );
}

