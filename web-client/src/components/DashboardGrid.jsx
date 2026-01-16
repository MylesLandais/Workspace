import React, { useEffect, useRef, useState } from 'react';
import { GridStack } from 'gridstack';
// import 'gridstack/dist/gridstack.min.css'; // Removed CSS import from here
const DashboardGrid = ({ layout, renderWidget, onLayoutChange }) => {
  const gridRef = useRef(null);
  const gsRef = useRef(null);
  const [isGridInitialized, setIsGridInitialized] = useState(false);

  useEffect(() => {
    if (!gridRef.current) return;
    
    // GridStack init only runs once on mount
    if (!gsRef.current) {
      const grid = GridStack.init(
        {
          column: 12,
          cellHeight: 100,
          margin: 10,
          float: true,
          animate: true,
          resizable: { handles: '.grid-stack-item-content-drag-handle' },
          alwaysShowResizeHandle: true,
        },
        gridRef.current
      );
      gsRef.current = grid;
      setIsGridInitialized(true);

      // Event listener for layout persistence
      grid.on('change', (_event, items) => {
        if (!items) return;
        const updatedLayout = items.map((it) => ({
          id: it.id,
          x: it.x,
          y: it.y,
          w: it.w,
          h: it.h,
          // Retain the widget type/content info
          type: layout.find(w => w.id === it.id)?.type || 'unknown',
        }));
        onLayoutChange?.(updatedLayout);
      });
    }

    return () => {
      if (gsRef.current) {
        gsRef.current.destroy(false);
        gsRef.current = null;
      }
    };
  }, [layout, onLayoutChange]);

  // Use a second effect to load the layout after Gridstack has initialized,
  // preventing race conditions with initial DOM rendering.
  useEffect(() => {
      if (isGridInitialized && layout && layout.length > 0) {
        // This is a simple implementation. In a complex app, you might use grid.load(layout) here
        // if the layout data wasn't already in the JSX attributes.
      }
  }, [isGridInitialized, layout]);

  return (
    <div className="grid-stack" ref={gridRef}>
      {layout.map((w) => (
        <div
          key={w.id}
          className="grid-stack-item"
          data-gs-id={w.id}
          data-gs-x={w.x}
          data-gs-y={w.y}
          data-gs-w={w.w}
          data-gs-h={w.h}
        >
          <div className="grid-stack-item-content bg-gray-900 rounded-lg p-4 shadow-xl border border-gray-700 overflow-y-auto">
            <div className="grid-stack-item-content-drag-handle text-gray-500 hover:text-gray-300 cursor-move text-right mb-2">
                {/* Drag handle icon */}
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 inline-block" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 100-2 1 1 0 000 2zm1 1a1 1 0 100-2 1 1 0 000 2zm3-1a1 1 0 100-2 1 1 0 000 2zm1 1a1 1 0 100-2 1 1 0 000 2zM7 13a1 1 0 100-2 1 1 0 000 2zm1 1a1 1 0 100-2 1 1 0 000 2zm3-1a1 1 0 100-2 1 1 0 000 2zm1 1a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                </svg>
            </div>
            {renderWidget(w)}
          </div>
        </div>
      ))}
    </div>
  );
};

export default DashboardGrid;
