"use client";

import React, { useState } from "react";
import { FileText } from "lucide-react";

interface TextWidgetProps {
  content: string;
}

const TextWidget: React.FC<TextWidgetProps> = ({ content }) => {
  const [text, setText] = useState(content);

  return (
    <div className="h-full flex flex-col p-4 bg-white dark:bg-industrial-900">
      {text ? (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="flex-1 w-full bg-transparent text-industrial-700 dark:text-industrial-300 resize-none border-none outline-none font-mono text-sm leading-relaxed"
          placeholder="Start typing..."
        />
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center text-industrial-400">
          <FileText className="w-12 h-12 mb-4 opacity-50" />
          <p className="text-sm">Click to start writing</p>
        </div>
      )}
    </div>
  );
};

export default TextWidget;
