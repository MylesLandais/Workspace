"use client";

import React from "react";
import { ImageIcon } from "lucide-react";
import Image from "next/image";

interface ImageWidgetProps {
  content: string;
}

const ImageWidget: React.FC<ImageWidgetProps> = ({ content }) => {
  if (!content) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-industrial-50 dark:bg-industrial-950">
        <ImageIcon className="w-12 h-12 text-industrial-300 dark:text-industrial-700 mb-4" />
        <p className="text-sm text-industrial-400 dark:text-industrial-600">
          No image URL provided
        </p>
      </div>
    );
  }

  return (
    <div className="h-full w-full relative bg-industrial-50 dark:bg-industrial-950 flex items-center justify-center">
      <Image src={content} alt="Widget image" fill className="object-contain" />
    </div>
  );
};

export default ImageWidget;
