"use client";

import React from "react";
import { SourceManagerWidget } from "@/components/sources/SourceManagerWidget";

interface SourcesWidgetProps {
  content?: string;
}

const SourcesWidget: React.FC<SourcesWidgetProps> = ({ content }) => {
  return (
    <div className="h-full w-full p-2">
      <SourceManagerWidget
        className="h-full border-none shadow-none bg-transparent"
        title={content || "Content Sources"}
      />
    </div>
  );
};

export default SourcesWidget;
