"use client";

import React, { useState, useEffect } from "react";
import mermaid from "mermaid";
import { Network, Loader2 } from "lucide-react";

interface MermaidWidgetProps {
  content: string;
}

const MermaidWidget: React.FC<MermaidWidgetProps> = ({ content }) => {
  const [svg, setSvg] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (!content) {
      setLoading(false);
      return;
    }

    async function renderDiagram() {
      try {
        mermaid.initialize({ startOnLoad: false, theme: "neutral" });
        const { svg } = await mermaid.render("mermaid-diagram", content);
        setSvg(svg);
        setError("");
      } catch (err) {
        console.error("[Mermaid] Render error:", err);
        setError("Invalid diagram syntax");
      } finally {
        setLoading(false);
      }
    }

    renderDiagram();
  }, [content]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-matcha-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-red-500">
        <Network className="w-12 h-12 mb-4 opacity-50" />
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-industrial-400">
        <Network className="w-12 h-12 mb-4 opacity-50" />
        <p className="text-sm">No diagram content</p>
      </div>
    );
  }

  return (
    <div
      className="h-full w-full overflow-auto p-4 flex items-center justify-center bg-white dark:bg-industrial-900"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};

export default MermaidWidget;
