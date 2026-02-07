"use client";

import { useState, useCallback } from "react";
import { X, Upload, FileText, Loader2, Check } from "lucide-react";
import type { OPMLFeed, OPMLParseResult } from "@/lib/types/sources";

interface OPMLImportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (feedUrls: string[]) => Promise<void>;
}

type Step = "upload" | "preview" | "importing" | "complete";

export function OPMLImportDialog({
  isOpen,
  onClose,
  onImport,
}: OPMLImportDialogProps) {
  const [step, setStep] = useState<Step>("upload");
  const [isDragging, setIsDragging] = useState(false);
  const [parseResult, setParseResult] = useState<OPMLParseResult | null>(null);
  const [selectedFeeds, setSelectedFeeds] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [importedCount, setImportedCount] = useState(0);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      await processFile(file);
    }
  }, []);

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        await processFile(file);
      }
    },
    [],
  );

  const processFile = async (file: File) => {
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/sources/import-opml", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Failed to parse OPML file");
      }

      const result: OPMLParseResult = await response.json();
      setParseResult(result);
      setSelectedFeeds(new Set(result.feeds.map((f) => f.xmlUrl)));
      setStep("preview");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const toggleFeed = (xmlUrl: string) => {
    const newSelected = new Set(selectedFeeds);
    if (newSelected.has(xmlUrl)) {
      newSelected.delete(xmlUrl);
    } else {
      newSelected.add(xmlUrl);
    }
    setSelectedFeeds(newSelected);
  };

  const toggleAll = () => {
    if (selectedFeeds.size === parseResult?.feeds.length) {
      setSelectedFeeds(new Set());
    } else {
      setSelectedFeeds(new Set(parseResult?.feeds.map((f) => f.xmlUrl) || []));
    }
  };

  const handleImport = async () => {
    if (selectedFeeds.size === 0) return;

    setStep("importing");
    try {
      await onImport(Array.from(selectedFeeds));
      setImportedCount(selectedFeeds.size);
      setStep("complete");
    } catch (err) {
      setError((err as Error).message);
      setStep("preview");
    }
  };

  const handleClose = () => {
    setStep("upload");
    setParseResult(null);
    setSelectedFeeds(new Set());
    setError(null);
    setImportedCount(0);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl max-h-[80vh] bg-zinc-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
          <h2 className="text-lg font-semibold text-app-text">
            {step === "upload" && "Import OPML"}
            {step === "preview" && "Select Feeds to Import"}
            {step === "importing" && "Importing Feeds..."}
            {step === "complete" && "Import Complete"}
          </h2>
          <button
            onClick={handleClose}
            className="p-1 rounded hover:bg-white/5 text-app-muted hover:text-app-text transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          {step === "upload" && (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
                isDragging
                  ? "border-app-accent bg-app-accent/5"
                  : "border-white/10 hover:border-white/20"
              }`}
            >
              <Upload className="w-12 h-12 mx-auto mb-4 text-app-muted" />
              <p className="text-app-text mb-2">
                Drag and drop your OPML file here
              </p>
              <p className="text-sm text-app-muted mb-4">or</p>
              <label className="inline-flex items-center gap-2 px-4 py-2 bg-white text-black font-semibold rounded-xl cursor-pointer hover:bg-zinc-200 transition-colors">
                <FileText className="w-4 h-4" />
                Choose File
                <input
                  type="file"
                  accept=".opml,.xml"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-app-muted mt-4">
                Supports OPML files exported from Feedly, Inoreader, and other
                RSS readers
              </p>
            </div>
          )}

          {step === "preview" && parseResult && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-app-muted">
                  Found {parseResult.feedCount} feeds
                  {parseResult.categories.length > 0 && (
                    <> in {parseResult.categories.length} categories</>
                  )}
                </p>
                <button
                  onClick={toggleAll}
                  className="text-sm text-app-accent hover:underline"
                >
                  {selectedFeeds.size === parseResult.feeds.length
                    ? "Deselect All"
                    : "Select All"}
                </button>
              </div>

              <div className="space-y-2 max-h-80 overflow-y-auto">
                {parseResult.feeds.map((feed) => (
                  <label
                    key={feed.xmlUrl}
                    className="flex items-center gap-3 p-3 bg-zinc-800/50 border border-white/5 rounded-xl cursor-pointer hover:bg-zinc-800 transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={selectedFeeds.has(feed.xmlUrl)}
                      onChange={() => toggleFeed(feed.xmlUrl)}
                      className="w-4 h-4 rounded border-white/20 bg-zinc-900 text-app-accent focus:ring-app-accent/50"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-app-text truncate">
                        {feed.title}
                      </div>
                      {feed.category && (
                        <div className="text-xs text-app-muted">
                          {feed.category}
                        </div>
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {step === "importing" && (
            <div className="py-12 text-center">
              <Loader2 className="w-12 h-12 mx-auto mb-4 text-app-accent animate-spin" />
              <p className="text-app-text">
                Importing {selectedFeeds.size} feeds...
              </p>
            </div>
          )}

          {step === "complete" && (
            <div className="py-12 text-center">
              <div className="w-12 h-12 mx-auto mb-4 bg-green-500/20 rounded-full flex items-center justify-center">
                <Check className="w-6 h-6 text-green-500" />
              </div>
              <p className="text-app-text mb-2">
                Successfully imported {importedCount} feeds
              </p>
              <p className="text-sm text-app-muted">
                Your new sources are now ready to use
              </p>
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/5">
          {step === "upload" && (
            <button
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-app-muted hover:text-app-text transition-colors"
            >
              Cancel
            </button>
          )}

          {step === "preview" && (
            <>
              <button
                onClick={() => setStep("upload")}
                className="px-4 py-2 text-sm font-medium text-app-muted hover:text-app-text transition-colors"
              >
                Back
              </button>
              <button
                onClick={handleImport}
                disabled={selectedFeeds.size === 0}
                className="px-4 py-2 bg-white text-black font-semibold rounded-xl hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Import {selectedFeeds.size} Feeds
              </button>
            </>
          )}

          {step === "complete" && (
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-white text-black font-semibold rounded-xl hover:bg-zinc-200 transition-colors"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
