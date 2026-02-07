"use client";

import React, { useRef, useEffect } from "react";
import { ReactSketchCanvas, ReactSketchCanvasRef } from "react-sketch-canvas";

interface DrawingCanvasProps {
  initialData?: unknown;
  onChange?: (data: unknown) => void;
  readOnly?: boolean;
  canvasRef: React.RefObject<ReactSketchCanvasRef | null>;
  strokeColor: string;
  strokeWidth: number;
  isEraser: boolean;
}

const DrawingCanvas: React.FC<DrawingCanvasProps> = ({
  initialData,
  onChange,
  readOnly = false,
  canvasRef,
  strokeColor,
  strokeWidth,
  isEraser,
}) => {
  // Sync Eraser mode
  useEffect(() => {
    if (canvasRef.current) {
      canvasRef.current.eraseMode(isEraser);
    }
  }, [isEraser, canvasRef]);

  // Load initial data
  useEffect(() => {
    if (
      initialData &&
      typeof initialData === "object" &&
      Object.keys(initialData).length > 0 &&
      canvasRef.current
    ) {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        canvasRef.current.loadPaths(initialData as any);
      } catch (e) {
        console.error("[DrawingCanvas] Failed to load canvas data", e);
      }
    }
  }, [initialData, canvasRef]);

  const handleStroke = async () => {
    if (onChange && canvasRef.current) {
      const paths = await canvasRef.current.exportPaths();
      onChange(paths);
    }
  };

  return (
    <div
      className={`relative w-full h-full bg-white dark:bg-industrial-950 ${readOnly ? "cursor-not-allowed" : "cursor-crosshair"}`}
      style={readOnly ? { pointerEvents: "none" } : {}}
    >
      <ReactSketchCanvas
        ref={canvasRef}
        strokeWidth={strokeWidth}
        strokeColor={strokeColor}
        onStroke={handleStroke}
        style={{ border: "none", width: "100%", height: "100%" }}
        width="100%"
        height="100%"
      />
    </div>
  );
};

export default DrawingCanvas;
